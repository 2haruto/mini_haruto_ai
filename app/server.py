from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import json

from .service import ChatService


class MiniAIHandler(BaseHTTPRequestHandler):
    service: ChatService
    web_root: Path
    health: dict[str, object]

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)

        if parsed.path == "/api/health":
            self._json(HTTPStatus.OK, self.health)
            return

        if parsed.path == "/api/sessions":
            self._json(HTTPStatus.OK, {"sessions": self.service.list_sessions()})
            return

        if parsed.path == "/api/messages":
            params = parse_qs(parsed.query)
            session_id = (params.get("session_id") or [""])[0]
            if not session_id:
                self._json(HTTPStatus.BAD_REQUEST, {"error": "session_id is required"})
                return

            if not self.service.repo.session_exists(session_id):
                self._json(HTTPStatus.NOT_FOUND, {"error": "session not found"})
                return

            messages = self.service.list_messages(session_id)
            self._json(HTTPStatus.OK, {"messages": messages})
            return

        if parsed.path in {"/", "/index.html"}:
            self._serve_file("index.html", "text/html; charset=utf-8")
            return

        if parsed.path == "/app.js":
            self._serve_file("app.js", "application/javascript; charset=utf-8")
            return

        self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)

        if parsed.path != "/api/chat":
            self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return

        content_len = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_len)

        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid json"})
            return

        message = str(payload.get("message", "")).strip()
        session_id = payload.get("session_id")

        if not message:
            self._json(HTTPStatus.BAD_REQUEST, {"error": "message is required"})
            return

        result = self.service.chat(session_id=session_id, user_message=message)
        self._json(
            HTTPStatus.OK,
            {
                "session_id": result.session_id,
                "answer": result.answer,
                "citations": result.citations,
            },
        )

    def log_message(self, format: str, *args: object) -> None:
        return

    def _serve_file(self, file_name: str, content_type: str) -> None:
        path = self.web_root / file_name
        if not path.exists():
            self._json(HTTPStatus.NOT_FOUND, {"error": "file not found"})
            return

        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def run_server(host: str, port: int, service: ChatService, web_root: Path, health: dict[str, object]) -> None:
    handler = type(
        "ConfiguredMiniAIHandler",
        (MiniAIHandler,),
        {"service": service, "web_root": web_root, "health": health},
    )

    server = ThreadingHTTPServer((host, port), handler)
    print(f"MiniHarutoAI is running on http://{host}:{port}")
    server.serve_forever()
