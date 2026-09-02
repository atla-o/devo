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
        conn = HTTPConnection("127.0.0.1", PORT, timeout=5)
        try:
            conn.request("GET", path, headers={"Host": host})
            res = conn.getresponse()
            body = res.read().decode("utf-8")
            return res.status, body
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
            self.assertIn("parent holding of a lateral health corporation", body)
            self.assertIn("Phenomatch", body)
            self.assertIn("Antiporn", body)
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
        self.assertIn("Not launched.", body)

    def test_three_hosts_are_distinct(self) -> None:
        pages = {
            host: self.fetch(host)[1]
            for host in (
                "devoutshaman.com",
                "antiporn.devoutshaman.com",
                "phenomatch.devoutshaman.com",
            )
        }
        self.assertEqual(len(set(pages.values())), 3)

    def test_shared_css(self) -> None:
        status, body = self.fetch("devoutshaman.com", "/shared/style.css")
        self.assertEqual(status, 200)
        self.assertIn("--measure", body)

    def test_unknown_path(self) -> None:
        status, _ = self.fetch("devoutshaman.com", "/no-such-page")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
