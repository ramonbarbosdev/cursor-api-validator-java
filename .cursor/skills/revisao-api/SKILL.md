---
name: revisao-api
description: Revisa o diff de API Java/Spring no escopo pedido (SPEC, DDL literal, domínio, REST). Usa .cursor/agents/api-validator.md e docs/validador/. Acionar com /api-validator, api-validator ou revisão de PR/feature.
---

# Revisão de diff (API Java / Spring)

Quality gate do diff. Com **escopo ampliado**, inclui SPEC, REST e testes conforme o agente.

**Fonte de verdade do procedimento:** `.cursor/agents/api-validator.md`. **Padrões:** `docs/padrao/README.md`. **Overlay de vizinhos (opcional):** `docs/validador/revisao.overlay.md`.

## Passos

1. Escopo: texto após `/api-validator`, `docs/SPEC.md` na branch, issue citada ou **Discussao na PR** (CI / `.api-validator-review/pr-*-discussion.md`). Sem escopo, perguntar e parar.
2. Ler `docs/validador/inteligente.md` e seguir o roteiro SPEC (resultado → DDL → domínio → HTTP → aceite).
3. Ler `docs/validador/escopo-e-rest.md` e decidir se o **escopo ampliado** está ativo.
4. `git status -sb` e `git diff origin/develop...HEAD --stat` (ou base indicada no escopo).
5. Ler `docs/validador/nao-reportar.md` antes de achados marginais.
6. Checklist: `docs/validador/review-checklist-api.md` (seções pertinentes).
7. Regras `EV-*` em `.cursor/rules/*.mdc` só nas áreas tocadas pelo diff/SPEC.
8. Vizinho: `docs/validador/revisao.md` + `revisao.overlay.md` se existir.
9. Fluxo: controller → DTO/`validar()` → service → repository → SQL.
10. DDL literal: migration + `@Column` + DTO vs SPEC (`EV-DDL-001`).
11. Domínio na SPEC: service implementa estratégia descrita.
12. REST: paths da SPEC vs controllers (`EV-REST-006`).
13. Testes tocados: `mvn -q -Dtest=... test`.
14. Saída: **Crítico**, **Importante**, **Conclusão** (agente).

## Delegação

Comando: `.cursor/commands/api-validator.md`. Não alterar código da aplicação na revisão.
