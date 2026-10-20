#!/usr/bin/env python3
"""
Detecta PR com commit novo (sem GitHub Actions).

Compara headRefOid da PR com automation-state.json (ultimo SHA validado).
Uso (cron / Agendador de Tarefas, a cada 2-5 min):

  set GITHUB_REPOSITORY=org/esimples-api
  set REPO_ROOT=C:\\path\\esimples-api
  set CURSOR_API_KEY=...
  python scripts/pr_review_poller.py

Opcional: --run chama pr_review_runner.py para cada PR pendente.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from pr_review_config import PrReviewConfig  # noqa: E402
from pr_review_gate import should_validate  # noqa: E402
from pr_review_state import get_validated_sha, load_state, mark_validated  # noqa: E402


def _gh_json(args: list[str], cwd: Path | None = None) -> Any:
    out = subprocess.check_output(["gh", *args], text=True, cwd=str(cwd) if cwd else None)
    return json.loads(out) if out.strip() else None


def _resolve_repository(cfg: PrReviewConfig) -> str:
    if cfg.repository and "/" in cfg.repository:
        return cfg.repository
    slug = _gh_json(
        ["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
        cwd=cfg.app_dir,
    )
    if not slug:
        raise SystemExit("Defina GITHUB_REPOSITORY ou rode com `gh` na pasta do app (REPO_ROOT).")
    return str(slug).strip()


def list_open_prs(repo: str, base: str) -> list[dict[str, Any]]:
    return _gh_json(
        [
            "pr",
            "list",
            "--repo",
            repo,
            "--base",
            base,
            "--state",
            "open",
            "--json",
            "number,headRefOid,isDraft,labels,title",
        ]
    )


def pending_prs(cfg: PrReviewConfig) -> list[tuple[dict[str, Any], str]]:
    repo = _resolve_repository(cfg)
    state = load_state(cfg.state_path)
    pending: list[tuple[dict[str, Any], str]] = []

    for pr in list_open_prs(repo, cfg.base_branch):
        num = pr["number"]
        sha = pr.get("headRefOid") or ""
        ok, reason = should_validate(
            pr,
            block_label=cfg.block_label,
            require_label=cfg.require_label,
        )
        if not ok:
            continue
        last = get_validated_sha(state, num)
        if last == sha:
            continue
        pending.append((pr, f"novo commit: {last or '(nunca)'} -> {sha[:12]}… ({reason})"))

    return pending


def main() -> int:
    parser = argparse.ArgumentParser(description="Poll PRs por commit novo (sem Actions)")
    parser.add_argument(
        "--run",
        action="store_true",
        help="Executa pr_review_runner.py para cada PR pendente",
    )
    parser.add_argument("--pr", type=int, default=0, help="So esta PR (ignora lista)")
    args = parser.parse_args()

    if not shutil_which("gh"):
        print("Instale GitHub CLI (`gh`) e `gh auth login`.", file=sys.stderr)
        return 1

    cfg = PrReviewConfig.from_env()
    repo = _resolve_repository(cfg)

    if args.pr:
        pr = _gh_json(["pr", "view", str(args.pr), "--repo", repo, "--json", "number,headRefOid,isDraft,labels,title"])
        items = [(pr, "disparo manual --pr")]
    else:
        items = pending_prs(cfg)

    if not items:
        print("Nenhuma PR pendente de validacao.")
        return 0

    runner = SCRIPT_DIR / "pr_review_runner.py"
    for pr, msg in items:
        n = pr["number"]
        sha = pr.get("headRefOid") or ""
        print(f"PR #{n}: {msg}")
        if not args.run:
            continue
        if not runner.is_file():
            print(f"  Falta {runner} — marque SHA manualmente apos validar no Cursor.", file=sys.stderr)
            continue
        rc = subprocess.call(
            [sys.executable, str(runner), "--pr", str(n)],
            cwd=str(cfg.app_dir),
        )
        if rc == 0:
            mark_validated(cfg.state_path, n, sha)
        else:
            print(f"  Runner falhou (exit {rc}); SHA nao atualizado.", file=sys.stderr)
            return rc

    if not args.run:
        print("\nDry-run. Rode com --run para executar pr_review_runner.py.")
    return 0


def shutil_which(cmd: str) -> bool:
    try:
        subprocess.run([cmd, "--version"], capture_output=True, check=False)
        return True
    except FileNotFoundError:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
