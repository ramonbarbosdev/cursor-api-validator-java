# Servidor webhook (estilo SIPEC, sem Actions)

O GitHub envia **POST** para sua URL quando há evento na PR. Você roda um processo na **sua máquina ou VPS** que recebe `/webhook` e dispara o validador.

## Arquitetura

```text
GitHub (PR: push, label, …)
    → POST https://SEU-TUNEL/webhook
    → pr_review_webhook.py (Python, porta 8765)
    → pr_review_runner.py (checkout, install, ci-api-validator)
    → comentário na PR + label de bloqueio
```

Comentários humanos na PR entram no prompt via `pr_human_comments.py` (token GitHub).

## 1. Pré-requisitos na máquina do servidor

| Item | Motivo |
|------|--------|
| Clone **esimples-api** em `REPO_ROOT` | `gh pr checkout` atualiza o código |
| Clone **cursor-api-validator-java** | install + scripts |
| `gh auth login` ou `GITHUB_TOKEN` (PAT) | checkout, comentário, labels |
| `CURSOR_API_KEY` | agente cloud (ou WSL + `ci-api-validator-cloud-wsl.ps1` no Windows) |
| Python 3.10+ | webhook + runner |
| `pip install -r scripts/requirements-ci.txt` | Cursor SDK no runner |

## 2. Configurar

```powershell
copy scripts\env.pr-review.example scripts\.env.pr-review
# edite GITHUB_REPOSITORY, REPO_ROOT, secrets
```

## 3. Subir o servidor

```powershell
cd cursor-api-validator-java
.\scripts\start-pr-review-webhook.ps1
```

Teste: `http://localhost:8765/health` → `ok`

## 4. Expor na internet (ngrok, como no SIPEC)

```bash
ngrok http 8765
```

No GitHub → **Settings → Webhooks → Add webhook**:

| Campo | Valor |
|-------|--------|
| Payload URL | `https://xxxx.ngrok-free.app/webhook` |
| Content type | `application/json` |
| Secret | mesmo valor de `GITHUB_WEBHOOK_SECRET` |
| Events | **Pull requests** (e opcional **Pull request reviews**) |

Cada **novo commit** na PR gera `pull_request` + action **`synchronize`** → runner valida de novo (SHA diferente do `automation-state.json`).

## 5. Labels (igual ao workflow)

| Env | Comportamento |
|-----|----------------|
| `API_VALIDATOR_REQUIRE_LABEL=validar-api` | só valida se a PR tiver essa label |
| `API_VALIDATOR_BLOCK_LABEL` (padrão Alteração Necessária) | com a label, webhook **ignora**; após NÃO APROVÁVEL o runner **aplica** a label |

## 6. VPS em produção

- Use **systemd** ou **nssm** no Windows para manter `pr_review_webhook.py` rodando.
- ngrok pago ou domínio + reverse proxy (Caddy/nginx) com HTTPS.
- Desative o workflow `api-validator-pr.yml` no esimples-api se não quiser Actions.

## Scripts

| Arquivo | Função |
|---------|--------|
| `pr_review_webhook.py` | HTTP `/webhook` |
| `pr_review_runner.py` | uma PR (`--pr 123`) |
| `pr_review_poller.py` | alternativa sem URL pública (cron) |
