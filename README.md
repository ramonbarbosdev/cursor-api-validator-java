# cursor-api-validator-java

Pacote **Cursor** para revisão de diff em APIs **Java / Spring Boot**: agente `/api-validator`, skill, regras `EV-*`, documentação de validação e padrões de controller, service, DTO e listagem.

Destinado a ser **instalado** no repositório da aplicação (ex.: `esimples-api`), não executado como app standalone.

## Conteúdo

| Caminho | Descrição |
|---------|-----------|
| `.cursor/agents/api-validator.md` | Veredito: Resumo, Crítico, Importante, Conclusão |
| `.cursor/commands/api-validator.md` | Comando Cursor `/api-validator` |
| `.cursor/skills/revisao-api/` | Skill operacional |
| `.cursor/rules/*.mdc` | Regras `EV-*` (REST, tenant, DDL, controller, service, …) |
| `docs/validador/` | Roteiro inteligente, escopo REST, checklist, ruído |
| `docs/padrao/` | Padrões genéricos (banco, PT, DTO, controller, service, listagem) |
| `docs/SPEC.template.md` | Template de `docs/SPEC.md` na branch |
| `stacks/java-spring-esimples/` | Overlay exemplo (financeiro e-Simples: Padrão C, vizinhos) |
| `install/` | Scripts para copiar arquivos no projeto alvo |

## Instalação no projeto Java

Na raiz do repositório da API (onde existem `src/main/java`, `pom.xml`):

### Windows (PowerShell)

```powershell
git clone https://github.com/SUA_ORG/cursor-api-validator-java.git .cursor-api-validator-java
.\.cursor-api-validator-java\install\install.ps1 -Target (Get-Location)
```

### Linux / macOS

```bash
git clone https://github.com/SUA_ORG/cursor-api-validator-java.git .cursor-api-validator-java
./.cursor-api-validator-java/install/install.sh "$(pwd)"
```

O script copia `.cursor/` e `docs/validador/`, `docs/padrao/`, `docs/SPEC.template.md` para o projeto. **Não remove** arquivos locais; sobrescreve apenas os que existem no pacote.

### Submodule (Cloud Agent / CI)

```bash
git submodule add https://github.com/SUA_ORG/cursor-api-validator-java.git .cursor-api-validator-java
./.cursor-api-validator-java/install/install.sh "$(pwd)"
git add .cursor docs/validador docs/padrao docs/SPEC.template.md
```

Após `git clone` do projeto: `git submodule update --init --recursive`.

### Overlay e-Simples (opcional)

```powershell
.\install\install.ps1 -Target C:\path\esimples-api -Stack java-spring-esimples
```

Copia também `stacks/java-spring-esimples/docs/padrao/*` e `revisao.overlay.md` → `docs/validador/revisao.overlay.md`.

## Uso no Cursor

1. Inclua no `AGENTS.md` do projeto (ver `templates/AGENTS.snippet.md`).
2. Comando: `/api-validator` + escopo (`docs/SPEC.md`, issue ou paths).
3. Cloud Agent: prompt citando `.cursor/skills/revisao-api/SKILL.md` e branch base (`develop`).

```text
/api-validator docs/SPEC.md — escopo ampliado, validador inteligente, diff vs develop
```

## Personalização no projeto alvo

| O que | Onde no projeto |
|-------|-----------------|
| Vizinhos por módulo | `docs/validador/revisao.md` ou `revisao.overlay.md` |
| Padrões só da empresa | `docs/padrao/` (merge com install) |
| Banco / permissões | `docs/arquitetura-banco-atual.md`, `docs/migrations-permissoes.md` (projeto) |
| Regras extras | `.cursor/rules/*.mdc` locais |

**Precedência:** SPEC da branch → regras CRÍTICAS → `docs/padrao/` do projeto → este pacote → código vizinho.

## Publicar no GitHub

```bash
cd cursor-api-validator-java
git init -b main
git add .
git commit -m "feat: pacote inicial api-validator Java/Spring"
git remote add origin https://github.com/SUA_ORG/cursor-api-validator-java.git
git push -u origin main
```

## Licença

MIT — use e adapte na sua organização.
