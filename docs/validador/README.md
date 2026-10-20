# Validador de API (`/api-validator`)

Processo de revisão: cruzar **SPEC**, **diff** e **padrões** do projeto Java/Spring.

**Veredito:** [`.cursor/agents/api-validator.md`](../../.cursor/agents/api-validator.md)

**Skill:** [`.cursor/skills/revisao-api/SKILL.md`](../../.cursor/skills/revisao-api/SKILL.md) · **Comando:** [`.cursor/commands/api-validator.md`](../../.cursor/commands/api-validator.md)

**Padrões:** [`../padrao/README.md`](../padrao/README.md) · **SPEC:** [`../SPEC.template.md`](../SPEC.template.md) → `docs/SPEC.md` na branch

**Vizinhos extras (opcional):** [`revisao.overlay.md`](revisao.overlay.md) — ex. stack `java-spring-esimples`

---

## Documentos

| Arquivo | Uso |
|---------|-----|
| [`inteligente.md`](inteligente.md) | Roteiro SPEC → DDL → domínio → REST |
| [`escopo-e-rest.md`](escopo-e-rest.md) | Escopo ampliado; colisão `/{id}` |
| [`revisao.md`](revisao.md) | Tipo de atividade → doc + vizinho (base) |
| [`nao-reportar.md`](nao-reportar.md) | Ruído |
| [`review-checklist-api.md`](review-checklist-api.md) | Checklist por área |
| [`erros-consumidor-critico-importante.md`](erros-consumidor-critico-importante.md) | **Prioridade:** defeitos ao usuário → Crítico/Importante |
| [`experiencia-consumidor-api.md`](experiencia-consumidor-api.md) | Polish HTTP → Melhoria / Ajuste |
| [`melhoria-javadoc-e-comentarios.md`](melhoria-javadoc-e-comentarios.md) | JavaDoc (Melhoria); comentário inline → Importante |
| [`wsl-windows-runner.md`](wsl-windows-runner.md) | WSL no Windows (runner self-hosted + SDK cloud) |
| [`review-por-pr.md`](review-por-pr.md) | PR, CI e comentário na PR |

```text
/api-validator docs/SPEC.md — escopo ampliado, validador inteligente
```
