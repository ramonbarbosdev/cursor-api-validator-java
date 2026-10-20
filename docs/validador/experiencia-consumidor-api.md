# Experiência do consumidor da API — Melhoria / Ajuste (não bloqueante)

**Leia antes:** [`erros-consumidor-critico-importante.md`](erros-consumidor-critico-importante.md) — tudo que **impede** o usuário ou **quebra segurança** vai em **Crítico** ou **Importante**, não aqui.

Este doc cobre só **polish** de **resposta HTTP** após essa varredura. **JavaDoc e comentários no código:** [`melhoria-javadoc-e-comentarios.md`](melhoria-javadoc-e-comentarios.md).

## O que entra em **Melhoria / Ajuste** (seção do relatório)

Somente com evidência no diff (handler, controller, DTO de erro, filtro, `ApiErrorResponse`, mensagem em `mensagem`/`erro`/`path`):

| Situação | Exemplo de julgamento |
|----------|------------------------|
| Status HTTP confuso para o cliente | Access expirado com refresh válido: só 401 genérico em rota de bootstrap vs 204 em `/me` — o front precisa de contrato claro; sugira alinhar mensagem ou documentar no handler |
| Mensagem genérica para o usuário | `SESSION_EXPIRED` com texto pouco acionável (“faça login”) vs contexto (org revogada, 2FA pendente) |
| Campo `path` / `erro` inconsistente | Mesmo cenário com `erro` diferente entre endpoints; front não consegue tratar de forma uniforme |
| Validação 400/422 | `details` vazio ou `mensagem` técnica (nome de campo Java) em vez de texto de formulário |
| Fluxo multi-passo (login, org, 2FA) | Resposta de login sem indicar próximo passo no **corpo** quando cookies mascaram token; usuário vê tela “travada” — melhoria de contrato ou doc |
| 403 vs 401 com logout indevido | Se o front desloga em 401 → avaliar **Importante** em `erros-consumidor-critico-importante.md`; só Melhoria se permissão negada já retorna 403 e UI trata certo |

**Formato do item** (igual às outras seções, linguagem para dev + produto):

* **Título objetivo**
  * **Onde:** classe/método/handler
  * **Cenário:** o que o usuário fez (ex.: abriu configurações com access vencido)
  * **O que o usuário vê hoje:** mensagem/tela provável com o payload atual
  * **Melhoria:** status, campo `mensagem`/`erro`, ou contrato documentado para o front

## O que **não** entra aqui

- Layout, CSS, componente React, roteamento do front (outro repositório) — **não reportar**, salvo se a SPEC da PR citar front no escopo ampliado.
- Defeito de segurança, tenant ou regra de negócio incorreta — vai em **Crítico** / **Importante**, não em Melhoria.
- “Seria bonito ter campo X no JSON” sem impacto na mensagem ou fluxo do usuário — não reportar.
- Hipótese sem ler o handler/DTO do diff.

## Relação com o veredito

Itens em **Melhoria / Ajuste** **não** impedem `APROVÁVEL`. Só **Crítico** e **Importante** alteram a **Conclusão**.

Se o mesmo fato é **bug objetivo** (ex.: vazamento de dados em `mensagem`) → **Importante** ou **Crítico**, não duplicar em Melhoria.

## Quando percorrer este roteiro

Ative mentalmente (e reporte Melhoria se houver achado) quando o diff alterar:

- `*Exception*`, `GlobalExceptionHandler`, `RestAuthenticationEntryPoint`, `RestAccessDeniedHandler`
- `AuthController`, `AuthSessionService`, filtros de segurança
- DTOs de erro, `ApiErrorResponse`, `ConstraintMessageMap`
- Validação Bean Validation / `validar()` com mensagem exposta ao cliente
- Novo endpoint que o aceite da SPEC associa a tela ou fluxo do usuário

Para auth/sessão do esimples-api, use também `docs/auth-sessao-cookies.md` no projeto da API (se existir) como referência de contrato esperado pelo SPA.
