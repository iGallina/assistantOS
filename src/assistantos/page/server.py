"""The local page: stdlib HTTP on 127.0.0.1, one SQLite connection per request. Marks and requests — nothing is sent.
Only the page itself is answered (docs/changes/page-refuses-other-websites): every request must be addressed to
127.0.0.1:<port> or localhost:<port> (Host — what DNS rebinding cannot change) and every POST must come from one of
those two origins (Origin — what a website cannot forge). Never add Access-Control-Allow-Origin or an OPTIONS handler:
either hands other websites back the reads and writes this takes away."""
import json
from datetime import date, datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs, urlparse

from pydantic import ValidationError

from ..i18n import _strings
from ..models import Mark
from ..store import Store
from .state import build_state


class Handler(BaseHTTPRequestHandler):
    server: "PageServer"

    def log_message(self, *a):  # quiet: the page is polled
        pass

    def end_headers(self):  # every response, send_error's 400/501 included: no framing, no sniffing JSON as script
        self.send_header("Content-Security-Policy", "frame-ancestors 'none'")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def parse_request(self) -> bool:  # the guard: runs before routing, for every method
        if not super().parse_request():
            return False
        port = self.server.server_address[1]
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if (self.headers.get("Host") or "").lower() not in hosts or (
                self.command == "POST" and self.headers.get("Origin") not in {f"http://{h}" for h in hosts}):
            n = self.headers.get("Content-Length", "")
            if n.isdigit() and int(n) <= 65536:  # read, never parsed: a close with unread data can reset the 403
                self.rfile.read(int(n))
            self._send(403, {"error": "forbidden"})  # not logged: any website could fill the owner's log
            return False
        return True

    def _send(self, code: int, body, ctype="application/json; charset=utf-8"):
        data = body.encode() if isinstance(body, str) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        store = Store(self.server.db_path)
        try:
            if u.path == "/":
                strings = {k: v for k, v in _strings(self.server.lang).items() if k.startswith("page.")}
                html = files("assistantos.page").joinpath("page.html").read_text(encoding="utf-8")
                self._send(200, html.replace("/*STRINGS*/{}", json.dumps(strings, ensure_ascii=False))
                           .replace("<html>", f'<html lang="{self.server.lang}">'), "text/html; charset=utf-8")
            elif u.path == "/api/state":
                self._send(200, build_state(store, self.server.today()))
            elif u.path == "/api/events":
                item_id = parse_qs(u.query).get("id", [""])[0]
                self._send(200, [e.model_dump(mode="json") for e in store.events(item_id)])
            else:
                self._send(404, {"error": "not found"})
        finally:
            store.close()

    def do_POST(self):
        path = urlparse(self.path).path
        if path not in ("/api/mark", "/api/ask"):
            return self._send(404, {"error": "not found"})
        store = Store(self.server.db_path)
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
            if not store.item(str(body.get("item_id"))):
                return self._send(404, {"error": "unknown item"})
            if path == "/api/ask":  # queued; the next pass answers it. A new ask follows up the item's last one
                ask = str(body.get("ask") or "").strip()
                if not ask:
                    return self._send(400, {"error": "empty request"})
                last = store.requests(body["item_id"])
                return self._send(200, {"id": store.add_request(body["item_id"], ask, "page", last[0]["id"] if last else None)})
            store.set_mark(Mark(item_id=body["item_id"], status=body.get("status"), at=datetime.now(timezone.utc),
                                who=body.get("who") or None, until=body.get("until") or None))
            self._send(200, {"ok": True})
        except (ValidationError, ValueError) as e:
            self._send(400, {"error": str(e)})
        finally:
            store.close()


class PageServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, db_path: Path, port: int, lang: str, today: Callable[[], date]):
        super().__init__(("127.0.0.1", port), Handler)
        self.db_path, self.lang, self.today = db_path, lang, today


def make_server(db_path: Path, port: int, lang: str, today: Callable[[], date]) -> PageServer:
    return PageServer(db_path, port, lang, today)
