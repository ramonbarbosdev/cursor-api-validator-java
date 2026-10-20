#!/usr/bin/env python3
"""
Servidor webhook GitHub -> api-validator (sem Actions).

  set GITHUB_WEBHOOK_SECRET=...
  set GITHUB_REPOSITORY=org/esimples-api
  set REPO_ROOT=C:\\path\\esimples-api
  set CURSOR_API_KEY=...
  set GITHUB_TOKEN=...   (ou gh auth login)
  python scripts/pr_review_webhook.py

Exponha com ngrok:  ngrok http 8765
Payload URL:         https://....ngrok-free.app/webhook

Eventos recomendados: Pull request (opened, synchronize, reopened, labeled, unlabeled).
"""
from __future__ import annotations

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from pr_review_config import PrReviewConfig  # noqa: E402
from pr_review_gate import should_validate  # noqa: E402
from pr_review_github import verify_webhook_signature  # noqa: E402
from pr_review_runner import run_validation  # noqa: E402

PR_ACTIONS = frozenset(
    {
        "opened",
        "synchronize",
        "reopened",
        "ready_for_review",
        "labeled",
        "unlabeled",
    }
)


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default).strip()


def _pr_from_payload(payload: dict[str, Any]) -> dict[str, Any] | None:
    pr = payload.get("pull_request")
    if not isinstance(pr, dict):
        return None
    labels = pr.get("labels") or []
    return {
        "number": pr.get("number"),
        "head_sha": (pr.get("head") or {}).get("sha"),
        "isDraft": pr.get("draft"),
        "labels": labels,
    }


def _should_process_event(payload: dict[str, Any], cfg: PrReviewConfig) -> tuple[bool, str, int | None]:
    repo_full = (payload.get("repository") or {}).get("full_name") or ""
    expected = cfg.repository
    if expected and repo_full and repo_full.lower() != expected.lower():
        return False, f"repo ignorado ({repo_full})", None

    event = _env("GITHUB_EVENT_NAME", payload.get("action", ""))
    # Handler sets GITHUB_EVENT_NAME from X-GitHub-Event header
    gh_event = os.environ.get("_CURRENT_GH_EVENT", "")

    if gh_event == "pull_request":
        action = payload.get("action") or ""
        if action not in PR_ACTIONS:
            return False, f"pull_request action ignorada: {action}", None
        pr = _pr_from_payload(payload)
        if not pr or not pr.get("number"):
            return False, "sem numero de PR", None
        ok, reason = should_validate(
            pr,
            block_label=cfg.block_label,
            require_label=cfg.require_label,
        )
        if not ok:
            return False, reason, int(pr["number"])
        return True, reason, int(pr["number"])

    if gh_event == "pull_request_review":
        action = payload.get("action") or ""
        if action != "submitted":
            return False, "review ignorado", None
        pr = payload.get("pull_request")
        if not isinstance(pr, dict):
            return False, "sem PR", None
        num = pr.get("number")
        if not num:
            return False, "sem numero", None
        pr_gate = {
            "isDraft": pr.get("draft"),
            "labels": pr.get("labels") or [],
        }
        ok, reason = should_validate(
            pr_gate,
            block_label=cfg.block_label,
            require_label=cfg.require_label,
        )
        if not ok:
            return False, reason, int(num)
        return True, f"review submitted ({reason})", int(num)

    return False, f"evento ignorado: {gh_event}", None


def _run_async(cfg: PrReviewConfig, pr_number: int) -> None:
    try:
        rc = run_validation(cfg, pr_number)
        if rc != 0:
            print(f"[webhook] PR #{pr_number} exit {rc}", file=sys.stderr)
    except Exception as e:
        print(f"[webhook] PR #{pr_number} erro: {e}", file=sys.stderr)


class WebhookHandler(BaseHTTPRequestHandler):
    server_version = "PrReviewWebhook/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[webhook] {self.address_string()} - {fmt % args}")

    def do_GET(self) -> None:
        if self.path in ("/", "/health"):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok\n")
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:
        cfg: PrReviewConfig = self.server.cfg  # type: ignore[attr-defined]
        secret = _env("GITHUB_WEBHOOK_SECRET", "")
        path = self.path.split("?", 1)[0]
        if path not in ("/webhook", "/"):
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(length)
        sig = self.headers.get("X-Hub-Signature-256")
        event = self.headers.get("X-GitHub-Event", "")

        if secret and not verify_webhook_signature(body, sig, secret):
            self.send_response(401)
            self.end_headers()
            return

        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        os.environ["_CURRENT_GH_EVENT"] = event
        run_it, reason, pr_num = _should_process_event(payload, cfg)
        if run_it and pr_num:
            print(f"[webhook] {event}: PR #{pr_num} -> fila ({reason})")
            threading.Thread(
                target=_run_async,
                args=(cfg, pr_num),
                daemon=True,
            ).start()
        else:
            print(f"[webhook] {event}: ignorado — {reason}")

        self.send_response(202)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True, "queued": bool(run_it and pr_num)}).encode())


def main() -> int:
    host = _env("WEBHOOK_HOST", "0.0.0.0")
    port = int(_env("WEBHOOK_PORT", "8765") or "8765")
    secret = _env("GITHUB_WEBHOOK_SECRET", "")
    if not secret:
        print("AVISO: GITHUB_WEBHOOK_SECRET vazio — assinatura nao sera validada.", file=sys.stderr)

    cfg = PrReviewConfig.from_env()
    if not cfg.repository:
        print("Defina GITHUB_REPOSITORY=org/repo", file=sys.stderr)
        return 1

    httpd = ThreadingHTTPServer((host, port), WebhookHandler)
    httpd.cfg = cfg  # type: ignore[attr-defined]
    print(f"Webhook em http://{host}:{port}/webhook (repo={cfg.repository})")
    print("ngrok: ngrok http", port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
