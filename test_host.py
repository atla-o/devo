#!/usr/bin/env python3
"""Prove Host-based pages differ, including localhost preview paths."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode

import aca
import server

_ACA_TMP = tempfile.TemporaryDirectory(prefix="devo-aca-")
os.environ["ACA_STORE"] = "json"
os.environ["ACA_DATA_PATH"] = os.path.join(_ACA_TMP.name, "apps.json")

PORT = int(os.environ.get("TEST_PORT", "18080"))

PRODUCT_HOSTS = (
    "https://lightround.devoutshaman.com",
    "https://lessfret.devoutshaman.com",
    "https://antiporn.devoutshaman.com",
    "https://phenomatch.devoutshaman.com",
)
TILE_NAMES = ("Lightround", "Lessfret", "Antiporn", "Phenomatch", "Insurance")


class HostRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", PORT), server.Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def fetch(self, host: str, path: str = "/") -> tuple[int, str]:
        status, body, _ = self.fetch_full(host, path)
        return status, body

    def fetch_full(self, host: str, path: str = "/") -> tuple[int, str, str | None]:
        conn = HTTPConnection("127.0.0.1", PORT, timeout=5)
        try:
            conn.request("GET", path, headers={"Host": host})
            res = conn.getresponse()
            body = res.read().decode("utf-8")
            return res.status, body, res.getheader("Location")
        finally:
            conn.close()

    def test_holding_hosts(self) -> None:
        for host in (
            "devoutshaman.com",
            "www.devoutshaman.com",
            "localhost:18080",
            "devo-web-xxxxx-uw.a.run.app",
        ):
            status, body = self.fetch(host)
            self.assertEqual(status, 200, host)
            self.assertIn("devo - lateral health corp", body)
            self.assertNotIn("parent holding of a lateral health corporation", body)
            self.assertIn("Phenomatch", body)
            self.assertIn("Antiporn", body)
            self.assertIn("Lessfret", body)
            self.assertIn("Lightround", body)
            self.assertIn('class="tile"', body)
            self.assertIn('class="cluster"', body)
            self.assertNotIn("<p>Product</p>", body)
            self.assertNotIn("<p>Service</p>", body)
            self.assertNotIn("<p>Fund</p>", body)
            for href in PRODUCT_HOSTS:
                self.assertIn(f'href="{href}"', body, host)
            self.assertIn('href="/insurance"', body, host)
            self.assertIn("Insurance", body, host)
            positions = [body.index(name) for name in TILE_NAMES]
            self.assertEqual(positions, sorted(positions), host)
            self.assertNotIn("The fund", body)
            self.assertNotIn('href="/fund"', body)
            self.assertNotIn('href="/lessfret"', body)
            self.assertNotIn("Install is not available yet", body)
            self.assertNotIn("Not launched.", body)

    def test_antiporn_host(self) -> None:
        status, body = self.fetch("antiporn.devoutshaman.com")
        self.assertEqual(status, 200)
        self.assertIn("Self-imposed computer restriction for macOS", body)
        self.assertIn("Install is not available yet.", body)
        self.assertNotIn("parent holding of a lateral health corporation", body)
        self.assertNotIn("Not launched.", body)

    def test_phenomatch_host(self) -> None:
        status, body = self.fetch("phenomatch.devoutshaman.com")
        self.assertEqual(status, 200)
        self.assertIn("matches people by phenotype", body)
        self.assertIn("Not launched.", body)
        self.assertNotIn("parent holding of a lateral health corporation", body)
        self.assertNotIn("Install is not available yet.", body)

    def test_localhost_preview_paths(self) -> None:
        status, body = self.fetch("localhost", "/antiporn")
        self.assertEqual(status, 200)
        self.assertIn("Install is not available yet.", body)

        status, body = self.fetch("127.0.0.1", "/phenomatch")
        self.assertEqual(status, 200)
        self.assertIn("matches people by phenotype", body)

        status, body = self.fetch("devoutshaman.com", "/lightround")
        self.assertEqual(status, 200)
        self.assertIn("counterdecadence fund", body)

        status, body = self.fetch("devoutshaman.com", "/fund")
        self.assertEqual(status, 200)
        self.assertIn("Lightround", body)
        self.assertIn("counterdecadence fund", body)
        self.assertNotIn("The fund", body)

        status, body = self.fetch("localhost", "/lessfret")
        self.assertEqual(status, 200)
        self.assertIn("Coaching and care coordination", body)
        self.assertIn("Not therapy.", body)

    def test_lightround_and_lessfret_hosts(self) -> None:
        status, body = self.fetch("lightround.devoutshaman.com")
        self.assertEqual(status, 200)
        self.assertIn("Lightround", body)
        self.assertIn("counterdecadence fund", body)
        self.assertNotIn("The fund", body)
        self.assertNotIn("parent holding of a lateral health corporation", body)

        status, body = self.fetch("lessfret.devoutshaman.com")
        self.assertEqual(status, 200)
        self.assertIn("Coaching and care coordination", body)
        self.assertIn("Not therapy.", body)
        self.assertNotIn("parent holding of a lateral health corporation", body)

    def test_fund_host_redirects_to_lightround(self) -> None:
        status, body, location = self.fetch_full("fund.devoutshaman.com")
        self.assertEqual(status, 301)
        self.assertEqual(location, "https://lightround.devoutshaman.com")
        self.assertIn("lightround.devoutshaman.com", body)

        status, _, location = self.fetch_full("fund.devoutshaman.com", "/thesis")
        self.assertEqual(status, 301)
        self.assertEqual(location, "https://lightround.devoutshaman.com/thesis")

    def test_pages_are_distinct(self) -> None:
        pages = {
            host: self.fetch(host)[1]
            for host in (
                "devoutshaman.com",
                "antiporn.devoutshaman.com",
                "phenomatch.devoutshaman.com",
                "lightround.devoutshaman.com",
                "lessfret.devoutshaman.com",
            )
        }
        self.assertEqual(len(set(pages.values())), 5)

    def test_shared_assets(self) -> None:
        conn = HTTPConnection("127.0.0.1", PORT, timeout=5)
        try:
            conn.request("GET", "/shared/style.css", headers={"Host": "devoutshaman.com"})
            res = conn.getresponse()
            body = res.read().decode("utf-8")
            self.assertEqual(res.status, 200)
            self.assertIn("text/css", res.getheader("Content-Type", ""))
            self.assertIn("--measure", body)
        finally:
            conn.close()

        conn = HTTPConnection("127.0.0.1", PORT, timeout=5)
        try:
            conn.request("GET", "/shared/preview.js", headers={"Host": "localhost"})
            res = conn.getresponse()
            body = res.read().decode("utf-8")
            self.assertEqual(res.status, 200)
            self.assertIn("javascript", res.getheader("Content-Type", ""))
            self.assertIn("data-local", body)
        finally:
            conn.close()

    def test_unknown_path(self) -> None:
        status, _ = self.fetch("devoutshaman.com", "/no-such-page")
        self.assertEqual(status, 404)

    def test_insurance_page_and_aca_alias(self) -> None:
        status, body = self.fetch("devoutshaman.com", "/insurance")
        self.assertEqual(status, 200)
        self.assertIn("Affordable Care Act", body)
        self.assertIn("id=\"aca-form\"", body)
        self.assertIn("Not insurance advice", body)
        self.assertIn("not a licensed", body)
        self.assertIn("HealthCare.gov", body)
        self.assertIn("id=\"lookup-form\"", body)
        self.assertIn("Application status", body)

        status, body = self.fetch("localhost", "/insurance/app.js")
        self.assertEqual(status, 200)
        self.assertIn("devo_aca_receipt", body)

        status, body, location = self.fetch_full("devoutshaman.com", "/aca")
        self.assertEqual(status, 301)
        self.assertEqual(location, "/insurance")
        self.assertIn("insurance", body)

        status, _, location = self.fetch_full("www.devoutshaman.com", "/aca/")
        self.assertEqual(status, 301)
        self.assertEqual(location, "/insurance")


class AcaIntakeTests(unittest.TestCase):
    port = PORT + 1

    @classmethod
    def setUpClass(cls) -> None:
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", cls.port), server.Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def setUp(self) -> None:
        path = os.environ["ACA_DATA_PATH"]
        if os.path.exists(path):
            os.remove(path)

    def request(
        self,
        method: str,
        path: str,
        *,
        host: str = "devoutshaman.com",
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, str, str | None]:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            hdrs = {"Host": host}
            if headers:
                hdrs.update(headers)
            conn.request(method, path, body=body, headers=hdrs)
            res = conn.getresponse()
            return res.status, res.read().decode("utf-8"), res.getheader("Location")
        finally:
            conn.close()

    def post_app(self, payload: dict, **kwargs: str) -> tuple[int, dict]:
        raw = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(raw)),
        }
        headers.update(kwargs)
        status, body, _ = self.request(
            "POST",
            "/api/aca/applications",
            body=raw,
            headers=headers,
        )
        return status, json.loads(body) if body else {}

    def valid_payload(self, **overrides: object) -> dict:
        data: dict = {
            "name": "Ada Lovelace",
            "email": "ada@example.com",
            "phone": "415-555-0100",
            "state": "CA",
            "zip": "94102",
            "household_size": 2,
            "income_band": "40k-60k",
            "preferred_contact": "email",
            "notes": "Open enrollment question",
        }
        data.update(overrides)
        return data

    def test_validate_rejects_incomplete(self) -> None:
        with self.assertRaises(aca.ValidationError) as ctx:
            aca.validate({"name": "A"})
        self.assertIn("email", ctx.exception.fields)
        self.assertIn("zip", ctx.exception.fields)

    def test_post_and_lookup_roundtrip(self) -> None:
        status, created = self.post_app(self.valid_payload())
        self.assertEqual(status, 201)
        self.assertEqual(created["status"], "received")
        self.assertEqual(created["status_label"], "Received")
        self.assertTrue(created["receipt_id"].startswith("aca_"))
        self.assertEqual(created["email"], "ada@example.com")
        self.assertEqual(created["household_size"], 2)

        on_disk = json.loads(Path(os.environ["ACA_DATA_PATH"]).read_text(encoding="utf-8"))
        self.assertIn(created["receipt_id"], on_disk)

        status, body, _ = self.request(
            "GET",
            "/api/aca/applications?" + urlencode({"receipt_id": created["receipt_id"]}),
        )
        self.assertEqual(status, 200)
        fetched = json.loads(body)
        self.assertEqual(fetched["receipt_id"], created["receipt_id"])
        self.assertEqual(fetched["status"], "received")
        self.assertEqual(fetched["status_detail"], "Devo has your interest form.")

        status, body, _ = self.request(
            "GET",
            "/api/aca/applications?" + urlencode({"email": "ADA@example.com"}),
        )
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["receipt_id"], created["receipt_id"])

    def test_post_validation_error(self) -> None:
        status, payload = self.post_app(self.valid_payload(email="not-an-email", zip="12"))
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "validation")
        self.assertIn("email", payload["fields"])
        self.assertIn("zip", payload["fields"])

    def test_lookup_missing(self) -> None:
        status, body, _ = self.request(
            "GET",
            "/api/aca/applications?" + urlencode({"receipt_id": "aca_0123456789abcdef"}),
        )
        self.assertEqual(status, 404)
        self.assertIn("not found", body.lower())

        status, body, _ = self.request("GET", "/api/aca/applications")
        self.assertEqual(status, 400)

    def test_foreign_origin_rejected(self) -> None:
        status, payload = self.post_app(
            self.valid_payload(),
            Origin="https://evil.example",
        )
        self.assertEqual(status, 403)
        self.assertEqual(payload["error"], "forbidden")


if __name__ == "__main__":
    unittest.main()
