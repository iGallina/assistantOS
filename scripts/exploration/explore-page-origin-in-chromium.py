# Exploration script — not part of the main program.
# Drives the real page in headless Chromium (Playwright) against a throwaway store, to confirm in a real browser
# what the unit tests prove with raw HTTP (docs/changes/page-refuses-other-websites): the page itself works at both
# addresses on a non-default port, and a hostile page on another local port can neither write, read nor frame it.
# Run: uv run --with playwright python scripts/exploration/explore-page-origin-in-chromium.py [chromium-executable]
import socket
import sys
import tempfile
import threading
from datetime import date, datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

from assistantos.models import Event, Item
from assistantos.page.server import make_server
from assistantos.store import Store


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


db = Path(tempfile.mkdtemp()) / "aos.db"
s = Store(db)
for k in range(2):
    s.upsert_item(Item(id=f"wa:5561000000{k}@s.whatsapp.net", source="whatsapp", title=f"C{k}"))
    s.add_event(Event(item_id=f"wa:5561000000{k}@s.whatsapp.net", at=datetime.now(timezone.utc), direction="in", text="oi"))
ids = [i.id for i in s.items()]
s.close()
port = free_port()
srv = make_server(db, port, "pt-BR", date.today)
threading.Thread(target=srv.serve_forever, daemon=True).start()

ATTACK = f"""<html><body>
<form id=f method=POST action="http://127.0.0.1:{port}/api/mark" enctype="text/plain" target=sink>
<input name='{{"item_id":"{ids[1]}","status":"feito","x":"' value='"}}'></form>
<iframe name=sink></iframe><iframe id=framed src="http://127.0.0.1:{port}/"></iframe>
<script>
fetch("http://127.0.0.1:{port}/api/ask", {{method:"POST", mode:"no-cors", body: JSON.stringify({{item_id:"{ids[1]}", ask:"ataque"}})}});
f.submit();
</script></body></html>"""


class Evil(BaseHTTPRequestHandler):  # "another program on the owner's computer" serving a website
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(ATTACK.encode())

    def log_message(self, *a):
        pass


evil_port = free_port()
threading.Thread(target=ThreadingHTTPServer(("127.0.0.1", evil_port), Evil).serve_forever, daemon=True).start()


def stored():
    st = Store(db)
    try:
        return [(st.mark(i), st.requests(i)) for i in ids]
    finally:
        st.close()


results = {}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=sys.argv[1] if len(sys.argv) > 1 else None)
    pg = b.new_page()
    for n, host in enumerate(("127.0.0.1", "localhost")):
        pg.goto(f"http://{host}:{port}/")
        pg.wait_for_selector("details.item")
        results[f"{host}: page loads"] = pg.locator("details.item").count() == 2
        code = pg.evaluate("""async ([id, ask]) => (await fetch("/api/ask", {method: "POST",
            headers: {"Content-Type": "application/json"}, body: JSON.stringify({item_id: id, ask})})).status""",
                           [ids[0], f"pedido {n}"])
        results[f"{host}: Pedir ao assistente (fetch POST)"] = code == 200
    pg.goto(f"http://localhost:{port}/")
    pg.wait_for_selector("details.item")
    pg.locator("details.item summary").first.click()
    pg.get_by_role("button", name="Feito").first.click()
    pg.wait_for_timeout(500)
    results["localhost: Feito button marks"] = any(m and m.status == "feito" for m, _ in stored())
    before = stored()
    evil = b.new_page()
    evil.goto(f"http://127.0.0.1:{evil_port}/")
    evil.wait_for_timeout(1500)
    results["hostile page: form + no-cors fetch change nothing"] = stored() == before
    framed = evil.frame_locator("#framed").locator("details.item")
    results["hostile page: iframe shows nothing"] = framed.count() == 0
    b.close()
srv.shutdown()
for k, v in results.items():
    print(("PASS " if v else "FAIL ") + k)
sys.exit(0 if all(results.values()) else 1)
