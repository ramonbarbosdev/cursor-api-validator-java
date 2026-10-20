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

Status / fila:       http://localhost:8765/status



Eventos recomendados: Pull request (opened, synchronize, reopened, labeled, unlabeled).

"""

from __future__ import annotations



import json

import os

import sys

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from pathlib import Path

from typing import Any



SCRIPT_DIR = Path(__file__).resolve().parent

if str(SCRIPT_DIR) not in sys.path:

    sys.path.insert(0, str(SCRIPT_DIR))



from pr_review_config import PrReviewConfig, load_pr_review_env_file  # noqa: E402

from pr_review_gate import should_validate  # noqa: E402

from pr_review_github import verify_webhook_signature  # noqa: E402

from pr_review_queue import QueueJob, get_queue  # noqa: E402

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





def _should_process_event(payload: dict[str, Any], cfg: PrReviewConfig) -> tuple[bool, str, int | None, str | None]:

    repo_full = (payload.get("repository") or {}).get("full_name") or ""

    expected = cfg.repository

    if expected and repo_full and repo_full.lower() != expected.lower():

        return False, f"repo ignorado ({repo_full})", None, None



    gh_event = os.environ.get("_CURRENT_GH_EVENT", "")

    action = payload.get("action") or ""



    if gh_event == "pull_request":

        if action not in PR_ACTIONS:

            return False, f"pull_request action ignorada: {action}", None, None

        pr = _pr_from_payload(payload)

        if not pr or not pr.get("number"):

            return False, "sem numero de PR", None, None

        ok, reason = should_validate(

            pr,

            block_label=cfg.block_label,

            require_label=cfg.require_label,

        )

        if not ok:

            return False, reason, int(pr["number"]), pr.get("head_sha")

        return True, reason, int(pr["number"]), pr.get("head_sha")



    if gh_event == "pull_request_review":

        if action != "submitted":

            return False, "review ignorado", None, None

        pr = payload.get("pull_request")

        if not isinstance(pr, dict):

            return False, "sem PR", None, None

        num = pr.get("number")

        if not num:

            return False, "sem numero", None, None

        pr_gate = {

            "isDraft": pr.get("draft"),

            "labels": pr.get("labels") or [],

        }

        ok, reason = should_validate(

            pr_gate,

            block_label=cfg.block_label,

            require_label=cfg.require_label,

        )

        head_sha = (pr.get("head") or {}).get("sha")

        if not ok:

            return False, reason, int(num), head_sha

        return True, f"review submitted ({reason})", int(num), head_sha



    return False, f"evento ignorado: {gh_event}", None, None





class WebhookHandler(BaseHTTPRequestHandler):

    server_version = "PrReviewWebhook/1.0"



    def log_message(self, fmt: str, *args: Any) -> None:

        print(f"[webhook] {self.address_string()} - {fmt % args}")



    def _json_response(self, code: int, payload: dict[str, Any]) -> None:

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        self.send_response(code)

        self.send_header("Content-Type", "application/json; charset=utf-8")

        self.send_header("Content-Length", str(len(body)))

        self.end_headers()

        self.wfile.write(body)



    def do_GET(self) -> None:

        path = self.path.split("?", 1)[0]

        if path in ("/", "/health"):

            self.send_response(200)

            self.send_header("Content-Type", "text/plain; charset=utf-8")

            self.end_headers()

            self.wfile.write(b"ok\n")

            return

        if path == "/status":

            cfg: PrReviewConfig = self.server.cfg  # type: ignore[attr-defined]

            snap = get_queue().snapshot()

            self._json_response(

                200,

                {

                    "ok": True,

                    "repository": cfg.repository,

                    **snap,

                },

            )

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

        action = payload.get("action") or ""

        event_label = f"{event}/{action}" if action else event

        run_it, reason, pr_num, head_sha = _should_process_event(payload, cfg)



        resp: dict[str, Any] = {"ok": True, "queued": False, "event": event_label}

        if pr_num is not None:

            resp["pr"] = pr_num



        if run_it and pr_num:

            from datetime import datetime, timezone



            job = QueueJob(

                pr_number=pr_num,

                enqueued_at=datetime.now(timezone.utc).isoformat(),

                event=event_label,

                reason=reason,

                head_sha=head_sha,

            )

            position, pending = get_queue().enqueue(job)

            print(f"[webhook] {event_label}: PR #{pr_num} -> fila pos {position} ({reason})")

            resp["queued"] = True

            resp["queue_position"] = position

            resp["pending_count"] = pending

        else:

            print(f"[webhook] {event_label}: ignorado — {reason}")

            resp["ignored"] = True

            resp["reason"] = reason



        self._json_response(202, resp)





def main() -> int:

    load_pr_review_env_file()

    host = _env("WEBHOOK_HOST", "0.0.0.0")

    port = int(_env("WEBHOOK_PORT", "8765") or "8765")

    secret = _env("GITHUB_WEBHOOK_SECRET", "")

    if not secret:

        print("AVISO: GITHUB_WEBHOOK_SECRET vazio — assinatura nao sera validada.", file=sys.stderr)

    if not _env("GITHUB_TOKEN", ""):

        print("AVISO: GITHUB_TOKEN vazio — validacao via webhook vai falhar.", file=sys.stderr)



    cfg = PrReviewConfig.from_env()

    if not cfg.repository:

        print("Defina GITHUB_REPOSITORY=org/repo", file=sys.stderr)

        return 1



    q = get_queue()



    def _run_pr(pr_number: int) -> int:

        load_pr_review_env_file()

        job_cfg = PrReviewConfig.from_env()

        return run_validation(job_cfg, pr_number)



    q.start_worker(_run_pr)



    httpd = ThreadingHTTPServer((host, port), WebhookHandler)

    httpd.cfg = cfg  # type: ignore[attr-defined]

    print(f"Webhook em http://{host}:{port}/webhook (repo={cfg.repository})")

    print(f"Status/fila: http://{host}:{port}/status")

    print("ngrok: ngrok http", port)

    try:

        httpd.serve_forever()

    except KeyboardInterrupt:

        print("\nEncerrado.")

    return 0





if __name__ == "__main__":

    raise SystemExit(main())


