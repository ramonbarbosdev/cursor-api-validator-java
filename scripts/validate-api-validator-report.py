#!/usr/bin/env python3
"""Gate de qualidade do relatorio antes de publicar na PR."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path


def norm(text: str) -> str:
    """ASCII minusculo sem acentos (Conclusao == Conclusão)."""
    folded = unicodedata.normalize("NFKD", text)
    return folded.encode("ascii", "ignore").decode().lower()


def git_diff_names(root: Path, base: str) -> list[str]:
    for ref in (f"origin/{base}...HEAD", f"origin/{base}", "HEAD"):
        try:
            out = subprocess.check_output(
                ["git", "diff", "--name-only", ref],
                cwd=root,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            names = [ln.strip() for ln in out.splitlines() if ln.strip()]
            if names:
                return names
        except subprocess.CalledProcessError:
            continue
    return []


def has_section(body: str, *keywords: str) -> bool:
    nbody = norm(body)
    for kw in keywords:
        nk = norm(kw)
        if nk in nbody:
            return True
        if re.search(rf"(?m)^#+\s*{re.escape(nk)}\b", nbody):
            return True
        if re.search(rf"\*\*{re.escape(nk)}\*\*", nbody):
            return True
    return False


def has_conclusion_verdict(body: str) -> bool:
    return bool(
        re.search(
            r"conclus[aã]o\s*:?\s*"
            r"(nao\s+aprov[aá]vel|aprov[aá]vel\s+com\s+ressalvas|aprov[aá]vel)\b",
            norm(body),
        )
    )


def main() -> int:
    root = Path(os.environ.get("REPO_ROOT", ".")).resolve()
    report = root / "api-validator-report.md"
    if not report.is_file():
        print(f"Falta {report}", file=sys.stderr)
        return 1

    text = report.read_text(encoding="utf-8")
    body = text
    if "## API Validator" in text:
        body = text.split("## API Validator", 1)[-1]

    errors: list[str] = []

    if not has_section(body, "Resumo"):
        errors.append("Secao ausente: Resumo")

    if not has_section(body, "Critico", "Crítico"):
        # Aceita achado explicito sem titulo (legado do prompt sem acento)
        if not re.search(r"(?i)crit[ií]co\s*:", body) and "nenhum" not in norm(body):
            errors.append("Secao ausente: Critico (ou linha Critico: / Nenhum.)")

    if not has_section(body, "Importante"):
        errors.append("Secao ausente: Importante")

    if not has_section(body, "Conclusao", "Conclusão") and not has_conclusion_verdict(
        body
    ):
        errors.append("Secao ausente: Conclusao (ou linha Conclusao: APROVAVEL ...)")

    if len(body.strip()) < 280:
        errors.append("Relatorio muito curto (possivel resposta generica).")

    if not has_conclusion_verdict(body):
        errors.append(
            "Conclusao invalida ou ausente (esperado: NAO APROVAVEL | "
            "APROVAVEL COM RESSALVAS | APROVAVEL)."
        )

    strict = os.environ.get("CURSOR_VALIDATOR_STRICT_REPORT", "1").strip() not in (
        "0",
        "false",
        "no",
    )
    if strict:
        base = os.environ.get("GITHUB_BASE_REF", "develop").removeprefix("origin/")
        changed = git_diff_names(root, base)
        if changed:
            mentioned = any(
                name in body or Path(name).name in body for name in changed[:40]
            )
            if not mentioned:
                errors.append(
                    "Relatorio nao cita nenhum arquivo do diff "
                    f"(ex.: {changed[0]}). Revisao provavelmente superficial."
                )

    if errors:
        print("Relatorio reprovado no gate de qualidade:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("Relatorio ok (gate de qualidade).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
