# Erros com consumidor (front) — Crítico vs Importante

**Prioridade do validador:** com SPA ou cliente HTTP assumido, procurar primeiro defeitos que **devem** ir em **Crítico** ou **Importante**. **Melhoria / Ajuste** só para o que restar (texto, polish, contrato documentado sem quebra funcional).

Pergunta guia: *“Se isso for para produção, o usuário deixa de usar o sistema, vê dado errado/de outro tenant, ou fica em loop de login — ou é só mensagem feia?”*

## Fluxo de classificação (obrigatório)

1. Diff toca auth, erro HTTP, validação, filtro, handler, sessão ou listagem autenticada?
2. Sim → percorrer tabelas abaixo **antes** de escrever Melhoria / Ajuste.
3. Se encaixar em Crítico ou Importante → reportar lá (com `EV-*` ou doc + evidência). **Não** duplicar em Melhoria.
4. Melhoria só se: comportamento tecnicamente aceitável, usuário ainda consegue concluir a tarefa, mas mensagem/status/campo `erro` pode confundir ou exigir gambiarra no front.

## **Crítico** (bloqueante — usuário ou segurança)

| Padrão | Evidência no diff | Impacto para o usuário |
|--------|-------------------|-------------------------|
| Cross-tenant ou dado de outra org na resposta | Query/service sem `idOrganizacao`; JWT sem validar vínculo | Vê contratos/financeiro de outra organização |
| Rota autenticada expõe PII sem auth alinhada | `permitAll` + retorno com dados sensíveis | Qualquer um com URL acessa cadastro |
| Sessão destruída em cascata | Refresh/logout limpa cookies em falha paralela; rotação inválida derruba access válido | Logou e em segundos volta ao login sem fazer nada |
| Auth bypass ou permissão ignorada | Filtro removido; `GLOBAL_*` tratado errado em rota tenant | Acessa módulo sem permissão |
| Migration que impede subida | `EV-PER-006` | Sistema fora do ar para todos |
| Corpo de erro vaza segredo | Stack, SQL, token em `mensagem`/`debugMessage` em prod | Risco + confusão extrema |
| 2FA / troca de senha obrigatória bypass | Filtro não aplicado no caminho alterado | Conta protegida fica exposta |

## **Importante** (defeito real — corrigir antes de concluir)

| Padrão | Evidência no diff | Impacto para o usuário |
|--------|-------------------|-------------------------|
| Contrato HTTP quebra fluxo do front | Login sem cookie em sucesso; mascaramento de token sem `Set-Cookie`; status incoerente (ex.: refresh sempre 204 sem distinguir renovação) | Não entra no app ou nome/org nunca carrega |
| 401/403 trocados em rota de negócio | Sem permissão → `SESSION_EXPIRED` | “Sessão expirada” e logout em vez de “sem acesso” |
| Bootstrap impossível | `/me` ou refresh bloqueados por filtro no estado intermediário (2FA, troca senha) sem rota alternativa documentada | Trava na login ou seleção de org |
| Validação não impede persistência inválida | Domínio/código aceito no POST que o banco ou regra rejeita depois | Erro 500 ou dado inconsistente na tela |
| Regressão em método compartilhado | Grep em chamadores; front depende do shape antigo | Telas quebram após deploy só da API |
| SPEC/aceite não atendido com efeito na UI | Critério citado na SPEC vs diff | Funcionalidade prometida não aparece |
| Whitelist/legado (`EV-VAL-004`) | Edição de cadastro antigo rejeitada sem plano | Usuário não consegue salvar registro existente |
| Colisão REST (`EV-REST-006/007`) | Path fixo capturado por `/{id}` | Ação da tela chama URL errada (404/500) |

## **Só Melhoria / Ajuste** (não bloqueia)

- Texto de `mensagem` genérico mas **código HTTP e `erro` corretos** e fluxo conclui.
- `path` no JSON aponta outro endpoint em requisições paralelas (ruído no log do front).
- Falta campo opcional no corpo que o front não usa (nome já vem de `/me`).
- Documentação do contrato cookie/refresh poderia estar mais explícita **sem** bug no handler atual.

## “Futuros erros” — sinais no diff

Ao revisar, marque mentalmente se o change **introduz** ou **amplifica**:

- Novo `catch` vazio ou `return false` sem resposta clara no auth.
- Novo endpoint GET coleção sem padrão de listagem/tenant do vizinho.
- Alteração em `SecurityConfig` / filtros sem espelho em teste ou doc de rota pública.
- Cookie path/domain/`secure` incoerente com doc de homolog (usuário loga em dev e “não loga” em homolog — **Importante** se aceite da atividade incluir homolog).
- Handler global que passa a mapear exceção de negócio para 500 em vez de 422.

Se houver evidência de quebra **no fluxo** (entrada → resposta), classifique **Importante** ou **Crítico**; não espere o front quebrar na PR para registrar.

## Evidência (igual ao agente)

Crítico/Importante exigem: regra ou doc, arquivo/trecho, entrada concreta, resultado errado, impacto ao usuário ou ao tenant.
