#!/usr/bin/env python3
"""Roda o api-validator no CI (somente relatório). Requer CURSOR_API_KEY e install já feito no REPO_ROOT."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from cursor_sdk import Agent, AgentOptions, CursorAgentError, LocalAgentOptions


def main() -> int:
    api_key = os.environ.get("CURSOR_API_KEY", "").strip()
    if not api_key:
        print("CURSOR_API_KEY não definido.", file=sys.stderr)
        return 1

    root = Path(os.environ.get("REPO_ROOT", ".")).resolve()
    agent_file = root / ".cursor" / "agents" / "api-validator.md"
    if not agent_file.is_file():
        print(f"Falta install do validador: {agent_file}", file=sys.stderr)
        return 1

    base = os.environ.get("GITHUB_BASE_REF", "develop").removeprefix("origin/")
    pr = os.environ.get("PR_NUMBER", "").strip()
    pr_label = f"PR #{pr}" if pr else "PR"

    try:
        stat = subprocess.check_output(
            ["git", "diff", "--stat", f"origin/{base}...HEAD"],
            cwd=root,
            text=True,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError:
        stat = subprocess.check_output(
            ["git", "diff", "--stat", f"origin/{base}", "HEAD"],
            cwd=root,
            text=True,
        )

    spec_path = root / "docs" / "SPEC.md"
    if spec_path.is_file():
        spec_line = (
            "Existe docs/SPEC.md na branch: modo inteligente; "
            "escopo ampliado se a SPEC tiver Contrato HTTP (docs/validador/escopo-e-rest.md)."
        )
    else:
        spec_line = "Sem docs/SPEC.md na branch: gate enxuto (somente git diff vs base)."

    model = os.environ.get("CURSOR_VALIDATOR_MODEL", "composer-2.5")

    prompt = f"""Você é o revisor api-validator do esimples-api (Java Spring Boot).

Leia e siga à risca o procedimento, precedência, evidência e formato em:
{agent_file}

Também use .cursor/skills/revisao-api/SKILL.md e docs/validador/nao-reportar.md quando aplicável.

Modo somente leitura: NÃO altere arquivos.

Escopo: {pr_label}, diff vs origin/{base}.
{spec_line}

Execute (somente leitura): git status -sb; git diff --stat origin/{base}...HEAD; git diff origin/{base}...HEAD nos arquivos relevantes.

Saída EXATAMENTE nesta ordem, em português: **Resumo**, **Crítico**, **Importante**, **Conclusão**.
Conclusão: NÃO APROVÁVEL | APROVÁVEL COM RESSALVAS | APROVÁVEL (regras do agente).
Sem achado: Crítico e Importante = "Nenhum."

git diff --stat (referência):
{stat}
"""

    report_path = root / "api-validator-report.md"
    try:
        result = Agent.prompt(
            prompt,
            AgentOptions(
                api_key=api_key,
                model=model,
                local=LocalAgentOptions(cwd=str(root)),
            ),
        )
    except CursorAgentError as e:
        print(f"Falha ao iniciar agente: {e}", file=sys.stderr)
        return 1

    if result.status == "error":
        print(f"Run falhou: {result.id}", file=sys.stderr)
        return 2

    body = (result.result or "").strip()
    if not body:
        body = "_Validador não retornou texto. Ver logs do workflow._"

    header = f"<!-- api-validator -->\n## API Validator ({pr_label})\n\n"
    if pr:
        header += f"_Base: `{base}` · disparo: push na PR_\n\n"
    report_path.write_text(header + body + "\n", encoding="utf-8")
    print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
