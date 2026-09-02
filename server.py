#!/usr/bin/env python3
"""Host-routed static site for Cloud Run service deo-web."""

from __future__ import annotations

import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent
SITES = ROOT / "sites"

HOST_SITES = {
    "antiporn.devoutshaman.com": "antiporn",
    "phenomatch.devoutshaman.com": "phenomatch",
    "devoutshaman.com": "holding",
    "www.devoutshaman.com": "holding",
}

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
LOCAL_PATH_SITES = (
    ("/antiporn", "antiporn"),
    ("/phenomatch", "phenomatch"),
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
        self._serve(body=True)

    def do_HEAD(self) -> None:
        self._serve(body=False)

    def _serve(self, *, body: bool) -> None:
        host = normalize_host(self.headers.get("Host", ""))
        parsed = urlparse(self.path)
        path = unquote(parsed.path) or "/"
        site = site_for_host(host)

        if is_local_host(host):
            for prefix, name in LOCAL_PATH_SITES:
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
