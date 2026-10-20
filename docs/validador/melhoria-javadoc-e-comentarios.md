# JavaDoc e comentários — Melhoria / Ajuste vs Importante

Aplicar ao **código novo ou alterado no diff** (não exigir JavaDoc em massa em classes legadas intocadas). Referência: [`docs/padrao/services.md`](../padrao/services.md), [`docs/padrao/controllers.md`](../padrao/controllers.md), `EV-SVC-*`, `EV-CTL-*`.

## Vai em **Importante** (bloqueia veredito)

| Regra | O que procurar no diff | Evidência |
|-------|------------------------|-----------|
| **EV-SVC-003** | Comentário `//` ou bloco `/* … */` **dentro do corpo** de método (não é JavaDoc `/**` imediatamente antes da declaração) | Trecho com comentário entre `{` e `}` do método |
| **EV-SVC-002** | Classe `*Service` **nova** ou método **público novo** **sem** JavaDoc `/** … */` | Assinatura sem bloco `/**` acima |
| **EV-SVC-004** | Método novo sem uso no projeto | Grep sem chamadores |
| Controller | Comentário inline no corpo do endpoint (`docs/padrao/controllers.md`) | Mesmo critério que service |

**Mensagem ao usuário do relatório:** comentário aleatório no meio do código **não é** Melhoria — é **Importante** (polui manutenção, mascara código morto, desvia do padrão do projeto).

## Vai em **Melhoria / Ajuste** (qualidade do JavaDoc)

Somente quando **já existe** JavaDoc no método/classe alterado, mas a **padronização** pode melhorar:

| Situação | Critério |
|----------|----------|
| Resumo vago | `/** Service */` ou `/** metodo */` sem explicar efeito, tenant ou exceções |
| `@param` / `@return` | Método público com parâmetros ou retorno relevante sem tags |
| `@author` / `@since` | Ausentes em método/classe **novo** no diff (`EV-SVC-005` — melhoria, não Importante se o bloco `/**` existir) |
| `{@link}` | Tipos de exceção ou service citados só no texto corrido |
| Desatualizado | JavaDoc contradiz assinatura ou comportamento após o diff (atualizar texto → se omitido, pode ser **Importante** como EV-SVC-002 “alteração relevante”) |
| Controller público | Endpoint novo com JavaDoc mínimo; padrão alinhado ao vizinho (`*Controller` do módulo) |

**Não reportar em Melhoria:** JavaDoc ausente em método **não tocado** pelo diff; classe legada sem documentação histórica.

## Checklist rápido (revisor)

1. Diff em `service/*`, `controller/*`, `security/*` com método novo ou corpo alterado?
2. Há `//` ou `/*` dentro de método? → **Importante** (EV-SVC-003).
3. Método/classe pública nova sem `/**`? → **Importante** (EV-SVC-002).
4. Há `/**` mas incompleto ou genérico? → **Melhoria / Ajuste** (listar o que falta: `@param`, resumo, `@since`, etc.).

## Formato do item em **Melhoria / Ajuste**

* **JavaDoc incompleto em `FooService.bar`**
  * **Onde:** `FooService.java`
  * **Situação:** método público novo/alterado no diff
  * **Gap:** falta `@param id`, resumo não menciona tenant; sem `@since`
  * **Ajuste:** seguir modelo em `docs/padrao/services.md` (ex. `AuthRefreshTokenService`, `BancoService`)

## Formato do item em **Importante** (comentário inline)

* **Comentário no corpo do método**
  * **Onde:** `FooService.java`, método `bar`
  * **Problema:** `// explica passo` dentro do método
  * **Impacto:** viola padrão do projeto; documentação deve ser JavaDoc fora do corpo ou nome de método
  * **Correção:** remover comentário; extrair método privado ou expandir JavaDoc do método
