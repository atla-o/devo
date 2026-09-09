#!/usr/bin/env python3
"""Prove Host-based pages differ, including localhost preview paths."""

from __future__ import annotations

import os
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

import server

PORT = int(os.environ.get("TEST_PORT", "18080"))

PRODUCT_HOSTS = (
    "https://phenomatch.devoutshaman.com",
    "https://antiporn.devoutshaman.com",
    "https://lessfret.devoutshaman.com",
    "https://lightround.devoutshaman.com",
)


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
            for href in PRODUCT_HOSTS:
                self.assertIn(f'href="{href}"', body, host)
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


if __name__ == "__main__":
    unittest.main()
