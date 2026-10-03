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

TOP_HOSTS = (
    "https://arcada.devoutshaman.com",
    "https://lightround.devoutshaman.com",
    "https://humanehealth.devoutshaman.com",
    "https://mattercircle.devoutshaman.com",
)
TILE_NAMES = ("Arcada", "Mattercircle", "Humanehealth", "Lightround")
TILE_BLURBS = (
    "Social club",
    "material products",
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
            self.assertNotIn("devo - lateral health corp", body)
            self.assertIn('class="fineprint">devo</p>', body)
            self.assertNotIn("parent holding of a lateral health corporation", body)
            self.assertEqual(body.count('class="tile"'), 4, host)
            self.assertIn('class="mark mark--halo"', body)
            self.assertNotIn("<p>Product</p>", body)
            self.assertNotIn("<p>Service</p>", body)
            self.assertNotIn("<p>Fund</p>", body)
            for href in TOP_HOSTS:
                self.assertIn(f'href="{href}"', body, host)
            for blurb in TILE_BLURBS:
                self.assertIn(blurb, body, host)
                self.assertLessEqual(len(blurb.split()), 3, blurb)
            self.assertNotIn("Clinic network", body, host)
            self.assertNotIn("Counterdecadence", body, host)
            self.assertNotIn("Factory essentials", body, host)
            humane = body.split("<h2>Humanehealth</h2>", 1)[1].split("</li>", 1)[0]
            self.assertNotIn("tile-blurb", humane, host)
            self.assertIn("halo--fractured", humane, host)
            lightround = body.split("<h2>Lightround</h2>", 1)[1].split("</li>", 1)[0]
            self.assertNotIn("tile-blurb", lightround, host)
            self.assertNotIn("fund", lightround, host)
            self.assertIn("halo--fractured", lightround, host)
            for whole in ("Arcada", "Mattercircle"):
                after = body.split(f"<h2>{whole}</h2>", 1)[1].split("</li>", 1)[0]
                self.assertIn('class="halo"', after, host)
                self.assertNotIn("halo--fractured", after, host)
            positions = [body.index(name) for name in TILE_NAMES]
            self.assertEqual(positions, sorted(positions), host)
            arcada = body.split("<h2>Arcada</h2>", 1)[0]
            arcada_tag = arcada.rsplit("<a", 1)[-1]
            self.assertIn('href="https://arcada.devoutshaman.com"', arcada_tag)
            self.assertNotIn("data-local", arcada_tag)
            self.assertNotIn("Holdings", body, host)
            self.assertNotIn("biology", body, host)
            self.assertNotIn("physics", body, host)
            for buried in (
                "Phenomatch",
                "Antiporn",
                "Lessfret",
                "Acashi",
                "Planet",
                "unnaturalfertility",
            ):
                self.assertNotIn(buried, body, host)
            self.assertNotIn("stage-6", body)
            self.assertNotIn("The fund", body)
            self.assertNotIn('href="/fund"', body)
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

        status, body = self.fetch("localhost", "/acashi")
        self.assertEqual(status, 200)
        self.assertIn("Affordable Care Act subsidized health insurance", body)
        self.assertIn("Not launched.", body)

        status, body = self.fetch("localhost", "/humanehealth")
        self.assertEqual(status, 200)
        self.assertIn("Clinic network.", body)
        self.assertIn("insurance", body)
        self.assertIn("sell-health", body)
        self.assertIn("unnaturalfertility", body)
        self.assertNotIn("Phenomatch", body)
        self.assertNotIn("Antiporn", body)
        self.assertNotIn("Lessfret", body)
        self.assertNotIn("Planet", body)
        self.assertNotIn('class="tile"', body)

        status, body = self.fetch("localhost", "/mattercircle")
        self.assertEqual(status, 200)
        self.assertIn("Factory essentials.", body)
        self.assertNotIn("Phenomatch", body)
        self.assertNotIn("unnaturalfertility", body)
        self.assertNotIn("Planet", body)

    def test_lightround_and_lessfret_hosts(self) -> None:
        status, body = self.fetch("lightround.devoutshaman.com")
        self.assertEqual(status, 200)
        self.assertIn("Lightround", body)
        self.assertIn("counterdecadence fund", body)
        self.assertNotIn("The fund", body)
        self.assertNotIn("fineprint", body)
        self.assertNotIn("devo - lateral health corp", body)
        self.assertNotIn("parent holding of a lateral health corporation", body)

        status, body = self.fetch("lessfret.devoutshaman.com")
        self.assertEqual(status, 200)
        self.assertIn("Coaching and care coordination", body)
        self.assertIn("Not therapy.", body)
        self.assertNotIn("parent holding of a lateral health corporation", body)

        status, body = self.fetch("acashi.devoutshaman.com")
        self.assertEqual(status, 200)
        self.assertIn("Acashi", body)
        self.assertIn("Affordable Care Act subsidized health insurance", body)
        self.assertIn("Not launched.", body)
        self.assertNotIn("parent holding of a lateral health corporation", body)

    def test_humanehealth_and_mattercircle_hosts(self) -> None:
        status, body = self.fetch("humanehealth.devoutshaman.com")
        self.assertEqual(status, 200)
        self.assertIn("Humanehealth", body)
        self.assertIn("Clinic network.", body)
        self.assertIn('href="https://acashi.devoutshaman.com"', body)
        self.assertIn(">Acashi</a>", body)
        self.assertIn("insurance", body)
        self.assertIn("devoutshaman", body)
        self.assertIn("sell-health", body)
        self.assertIn("unnaturalfertility", body)
        self.assertNotIn("Phenomatch", body)
        self.assertNotIn("Antiporn", body)
        self.assertNotIn("Lessfret", body)
        self.assertNotIn("Planet", body)
        self.assertNotIn('class="tile"', body)
        self.assertNotIn("stage-6", body)
        self.assertNotIn("fineprint", body)
        nest_names = ("Acashi", "devoutshaman", "unnaturalfertility")
        positions = [body.index(f">{name}<") for name in nest_names]
        self.assertEqual(positions, sorted(positions))

        status, body = self.fetch("mattercircle.devoutshaman.com")
        self.assertEqual(status, 200)
        self.assertIn("Mattercircle", body)
        self.assertIn("Factory essentials.", body)
        self.assertNotIn("Phenomatch", body)
        self.assertNotIn("physics", body.lower())
        self.assertNotIn("unnaturalfertility", body)
        self.assertNotIn("Planet", body)
        self.assertNotIn('class="tile"', body)

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
                "acashi.devoutshaman.com",
                "humanehealth.devoutshaman.com",
                "mattercircle.devoutshaman.com",
            )
        }
        self.assertEqual(len(set(pages.values())), 8)

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
            self.assertIn("devoutshaman.com", body)
        finally:
            conn.close()

    def test_unknown_path(self) -> None:
        status, _ = self.fetch("devoutshaman.com", "/no-such-page")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
