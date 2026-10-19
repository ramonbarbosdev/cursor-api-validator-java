# Padrão de banco de dados (DDL / Flyway / JPA)

Normas para **migrations**, **schemas**, **tenant**, **constraints** e **entity**. Colunas: [`nomenclatura-colunas-sql.md`](nomenclatura-colunas-sql.md) · PT: [`nomenclatura-portugues.md`](nomenclatura-portugues.md).

Validador: `.cursor/rules/persistence.mdc`, `ev-ddl-nomenclatura.mdc`, `multi-tenant.mdc`.

**No projeto alvo:** manter `docs/arquitetura-banco-atual.md` (mapa de schemas/tabelas) e `docs/migrations-permissoes.md` se houver banco central — o validador usa como referência, não exige doc atualizada (`EV-ESP-003`).

---

## Onde vive cada DDL

| Destino | Caminho típico (Spring) | Uso |
|---------|-------------------------|-----|
| **Tenant** | `src/main/resources/db/migration/` | Negócio isolado por organização |
| **Central** | `src/main/resources/db/central/` | Catálogo global, auth, permissões |

`EV-PER-001` / `EV-PER-002`: não misturar responsabilidades tenant ↔ central.

---

## Flyway

- `V{N}__descricao.sql` — uma versão por arquivo (`EV-PER-004`).
- **Nunca** alterar/apagar migration já aplicada; correção = novo `V*`.
- Hibernate `validate`: DDL só via Flyway.

---

## Schemas

- PostgreSQL com **schemas por módulo** (`public`, `financeiro`, `contrato`, …) conforme o projeto.
- SQL qualificado: `schema.tabela`; entity com `@Table(schema = "...", name = "...")`.
- Novo objeto: **mesmo schema** do vizinho do módulo (SPEC ou tabela análoga).

---

## Multi-tenant

- `id_organizacao NOT NULL` + índice nas tabelas de negócio tenant.
- Entity base tipo `TenantEntity` + filtro no repository/service (`EV-MTN-*`).
- Referência a catálogo central por ID: validação no service, sem FK entre bancos (`EV-MTN-004`).

---

## Tabelas, constraints, índices

- Tabela `snake_case`; colunas com prefixos (`id_`, `nm_`, `fl_`, `dt_`, `vl_`, `tp_`, …).
- `fk_*`, `uk_*`, `ck_*`, `idx_*`; mensagens em `ConstraintMessageMap` quando aplicável.
- SPEC literal de nomes → `EV-DDL-001`.

---

## Tríade

1. Migration SQL  
2. `@Column` / entity  
3. DTO + service  

---

## Transações

Service: `@Transactional`; central: `centralTransactionManager`. Sem TX no controller.

---

## Checklist (diff com migration)

- [ ] `V*` novo no pasta certa (tenant vs central)
- [ ] `id_organizacao` + índice se tenant
- [ ] Entity alinhada; tríade com DTO
- [ ] Sem edição de `V*` legado no diff

---

## Stack e-Simples

Exemplos concretos de schema `financeiro` e migrations: instalar overlay `java-spring-esimples` e ver `docs/arquitetura-banco-atual.md` no projeto e-Simples.
