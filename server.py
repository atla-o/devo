#!/usr/bin/env python3
"""Host-routed static site for Cloud Run service devo-web."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import aca

ROOT = Path(__file__).resolve().parent
SITES = ROOT / "sites"

ACA_API_PATH = "/api/aca/applications"
MAX_ACA_BODY = 32_768

HOST_SITES = {
    "antiporn.devoutshaman.com": "antiporn",
    "phenomatch.devoutshaman.com": "phenomatch",
    "lightround.devoutshaman.com": "lightround",
    "lessfret.devoutshaman.com": "lessfret",
    "devoutshaman.com": "holding",
    "www.devoutshaman.com": "holding",
}

FUND_HOST = "fund.devoutshaman.com"
LIGHTROUND_ORIGIN = "https://lightround.devoutshaman.com"

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
PATH_SITES = (
    ("/antiporn", "antiporn"),
    ("/phenomatch", "phenomatch"),
    ("/lightround", "lightround"),
    ("/fund", "lightround"),
    ("/lessfret", "lessfret"),
)

MIME = {
    ".css": "text/css; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".ico": "image/x-icon",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".txt": "text/plain; charset=utf-8",
}


def normalize_host(raw: str) -> str:
    host = raw.split(",")[0].strip().lower()
    if host.startswith("[") and "]" in host:
        host = host[1 : host.index("]")]
    elif ":" in host:
        host = host.rsplit(":", 1)[0]
    return host


def site_for_host(host: str) -> str:
    return HOST_SITES.get(host, "holding")


def is_local_host(host: str) -> bool:
    return host in LOCAL_HOSTS or host.endswith(".localhost")


def safe_join(root: Path, rel: str) -> Path | None:
    candidate = (root / rel.lstrip("/")).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} {fmt % args}", flush=True)

    def do_GET(self) -> None:
        if self._aca_api():
            return
        self._serve(body=True)

    def do_HEAD(self) -> None:
        self._serve(body=False)

    def do_POST(self) -> None:
        if self._aca_api():
            return
        self._plain(404, b"Not found\n")

    def _aca_api(self) -> bool:
        parsed = urlparse(self.path)
        path = (unquote(parsed.path) or "/").rstrip("/") or "/"
        if path != ACA_API_PATH:
            return False

        if self.command == "POST":
            payload, err = self._read_json_body()
            if not self._same_origin():
                self._json(403, {"error": "forbidden"})
                return True
            if err:
                self._json(400, {"error": err})
                return True
            try:
                created = aca.create(payload)
            except aca.ValidationError as exc:
                self._json(400, {"error": "validation", "fields": exc.fields})
                return True
            except aca.StoreError:
                self._json(503, {"error": "Could not save application."})
                return True
            self._json(201, created)
            return True

        if self.command != "GET":
            self._json(405, {"error": "method not allowed"})
            return True

        query = parse_qs(parsed.query)
        receipt_id = (query.get("receipt_id") or query.get("receipt") or [""])[0]
        email = (query.get("email") or [""])[0]
        if not receipt_id and not email:
            self._json(400, {"error": "Provide receipt_id or email."})
            return True
        try:
            found = aca.lookup(receipt_id=receipt_id or None, email=email or None)
        except aca.StoreError:
            self._json(503, {"error": "Could not look up application."})
            return True
        if found is None:
            self._json(404, {"error": "Application not found."})
            return True
        self._json(200, found)
        return True

    def _same_origin(self) -> bool:
        origin = self.headers.get("Origin")
        if not origin:
            return True
        origin_host = normalize_host(urlparse(origin).netloc)
        request_host = normalize_host(self.headers.get("Host", ""))
        return bool(origin_host) and origin_host == request_host

    def _read_json_body(self) -> tuple[object | None, str | None]:
        try:
            length = int(self.headers.get("Content-Length") or "0")
        except ValueError:
            return None, "Invalid Content-Length."
        if length < 0 or length > MAX_ACA_BODY:
            return None, "Payload too large."
        raw = self.rfile.read(length) if length else b""
        if not raw:
            return None, "Send a JSON body."
        try:
            return json.loads(raw.decode("utf-8")), None
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None, "Invalid JSON."

    def _json(self, code: int, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def _serve(self, *, body: bool) -> None:
        host = normalize_host(self.headers.get("Host", ""))
        parsed = urlparse(self.path)
        path = unquote(parsed.path) or "/"

        if path.rstrip("/") == "/aca":
            self._redirect("/insurance", body=body)
            return

        if host == FUND_HOST:
            dest = LIGHTROUND_ORIGIN
            if path != "/":
                dest += path
            if parsed.query:
                dest += "?" + parsed.query
            self._redirect(dest, body=body)
            return

        site = site_for_host(host)

        if site == "holding" or is_local_host(host):
            for prefix, name in PATH_SITES:
                if path == prefix or path.startswith(prefix + "/"):
                    site = name
                    path = path[len(prefix) :] or "/"
                    break

        if path == "/":
            path = "/index.html"

        if path.startswith("/shared/"):
            file_path = safe_join(SITES / "shared", path[len("/shared/") :])
        else:
            file_path = safe_join(SITES / site, path)

        if file_path is None:
            self._plain(404, b"Not found\n")
            return

        if file_path.is_dir():
            file_path = file_path / "index.html"

        if not file_path.is_file():
            self._plain(404, b"Not found\n")
            return

        data = file_path.read_bytes()
        content_type = MIME.get(file_path.suffix.lower(), "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=300")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.end_headers()
        if body:
            self.wfile.write(data)

    def _redirect(self, location: str, *, body: bool, code: int = 301) -> None:
        payload = f"Redirecting to {location}\n".encode() if body else b""
        self.send_response(code)
        self.send_header("Location", location)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if body:
            self.wfile.write(payload)

    def _plain(self, code: int, payload: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"devo-web listening on 0.0.0.0:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("shutting down", flush=True)
        server.server_close()


if __name__ == "__main__":
    main()
