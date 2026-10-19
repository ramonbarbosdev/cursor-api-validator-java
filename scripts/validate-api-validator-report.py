#!/usr/bin/env python3
"""Gate de qualidade do relatorio antes de publicar na PR."""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


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


def main() -> int:
    root = Path(os.environ.get("REPO_ROOT", ".")).resolve()
    report = root / "api-validator-report.md"
    if not report.is_file():
        print(f"Falta {report}", file=sys.stderr)
        return 1

    text = report.read_text(encoding="utf-8")
    # Corpo apos cabecalho gerado pelo CI
    body = text
    if "## API Validator" in text:
        body = text.split("## API Validator", 1)[-1]

    errors: list[str] = []

    for label in ("Resumo", "Crítico", "Importante", "Conclusão"):
        if label not in body and label.lower() not in body.lower():
            errors.append(f"Secao ausente: **{label}**")

    if len(body.strip()) < 280:
        errors.append("Relatorio muito curto (possivel resposta generica).")

    if not re.search(
        r"Conclus[aã]o\s*:?\s*(N[AÃ]O\s+APROV[AÁ]VEL|APROV[AÁ]VEL\s+COM\s+RESSALVAS|APROV[AÁ]VEL)",
        body,
        re.IGNORECASE,
    ):
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
