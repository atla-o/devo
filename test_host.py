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

TILE_NAMES = ("Humanehealth", "utopiasocial", "Mattercircle")
TILE_BLURBS = (
    "utopia social club",
    "non-petroleum factory",
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
            self.assertNotIn('class="fineprint">devo</p>', body)
            self.assertIn(">Support Devo</a>", body)
            self.assertIn(
                "https://donate.stripe.com/7sY00ifPd8Xdb278i24Ni00",
                body,
            )
            self.assertIn(
                "A gift to Atla LLC. Not tax deductible, not an investment.",
                body,
            )
            self.assertEqual(body.count('class="support"'), 2, host)
            self.assertNotIn("parent holding of a lateral health corporation", body)
            self.assertNotIn('class="tile"', body)
            self.assertIn('class="mark mark--halo"', body)
            self.assertIn('class="theme-switch"', body)
            self.assertIn('class="theme-rich"', body)
            self.assertIn('class="topbar"', body)
            self.assertIn('class="topnav"', body)
            self.assertEqual(body.count('class="dropdown"'), 1, host)
            self.assertEqual(body.count('class="drop-sheet"'), 3, host)
            rich = body.split('class="theme-rich"', 1)[1]
            bar = rich.split('class="home-panels"', 1)[0]
            nav = bar.split('class="topnav"', 1)[1].split("menu-toggle", 1)[0]
            self.assertNotIn("data-local", nav, host)
            self.assertIn('href="/utopiasocial">utopiasocial</a>', bar)
            self.assertIn('href="/mattercircle">Mattercircle</a>', bar)
            self.assertIn('href="/humanehealth">Humanehealth</a>', bar)
            self.assertIn(">Menu<", bar)
            self.assertNotIn(">Arcada<", bar, host)
            self.assertNotIn(">Lightround<", bar, host)
            sheets = rich.split('class="drop-sheet"')[1:4]
            map_lines = (
                (
                    "concentrated stimulants",
                    "Humanehealth store",
                    "schedule wellness",
                    "invasive diagnostic",
                    "unnaturalfertility",
                    "cosmetic restoration",
                    "acashi",
                    "develop cures",
                ),
                (
                    "utopia social club",
                    "ancestry club",
                    "intellectual club",
                    "leisure club",
                    "political club",
                    "spiritual club",
                ),
                ("toiletries", "wearables", "utility", "furniture", "checkout"),
            )
            for menu, labels in zip(sheets, map_lines):
                self.assertLess(menu.index(">Products<"), menu.index(">Services<"), host)
                spots = [menu.index(f">{label}<") for label in labels]
                self.assertEqual(spots, sorted(spots), host)
            self.assertEqual(body.count('class="panel"'), 3, host)
            self.assertNotIn('class="branch-view"', body, host)
            self.assertIn("prefab housing", body)
            self.assertIn('href="/utopiasocial/ancestry"', body)
            self.assertIn('href="/utopiasocial/intellectual"', body)
            self.assertIn('href="/utopiasocial/leisure"', body)
            self.assertIn('href="/mattercircle/climb/toiletries"', body)
            self.assertIn('href="/humanehealth/ops/wellness"', body)
            self.assertNotIn("lightround.devoutshaman.com", body, host)
            self.assertNotIn("Lightround", body, host)
            self.assertNotIn("Terraform", body, host)
            self.assertNotIn("Arcada", body, host)
            self.assertNotIn(">devoutshaman<", body, host)
            self.assertNotIn("education club", body, host)
            self.assertNotIn("media club", body, host)
            self.assertNotIn("recreation club", body, host)
            self.assertNotIn("northern social club", body, host)
            self.assertNotIn("online intro", body, host)
            self.assertNotIn("Atlantis", body, host)
            self.assertNotIn("shippable", body, host)
            self.assertNotIn("<p>Product</p>", body)
            self.assertNotIn("<p>Service</p>", body)
            self.assertNotIn("<p>Fund</p>", body)
            for href in ("/utopiasocial", "/humanehealth", "/mattercircle"):
                self.assertIn(f'href="{href}"', body, host)
            for blurb in TILE_BLURBS:
                self.assertIn(blurb, body, host)
                self.assertLessEqual(len(blurb.split()), 3, blurb)
            self.assertNotIn("Clinic network", body, host)
            self.assertNotIn("Counterdecadence", body, host)
            self.assertNotIn("Factory essentials", body, host)
            simple = body.split('class="theme-rich"', 1)[0]
            for label in (
                "ancestry club",
                "intellectual club",
                "leisure club",
                "toiletries",
                "schedule wellness",
                "unnaturalfertility",
                "acashi",
                "Humanehealth store",
                "develop cures",
                "prefab housing",
            ):
                self.assertIn(label, simple, host)
            positions = [body.index(name) for name in TILE_NAMES]
            self.assertEqual(positions, sorted(positions), host)
            first = simple.split("<h2>", 1)[1]
            self.assertIn('href="/humanehealth"', first.split("</h2>", 1)[0])
            self.assertNotIn("data-local", first.split("</h2>", 1)[0])
            self.assertNotIn("Holdings", body, host)
            self.assertNotIn("biology", body, host)
            self.assertNotIn("physics", body, host)
            for buried in (
                "Phenomatch",
                "Antiporn",
                "Lessfret",
                "Acashi",
                "Planet",
            ):
                self.assertNotIn(buried, simple, host)
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
        self.assertIn("Products", body)
        self.assertIn("Services", body)
        self.assertIn("schedule wellness", body)
        self.assertIn("Humanehealth store", body)
        self.assertIn("unnaturalfertility", body)
        self.assertNotIn("Phenomatch", body)
        self.assertNotIn("Antiporn", body)
        self.assertNotIn("Lessfret", body)
        self.assertNotIn("Planet", body)
        self.assertNotIn('class="tile"', body)

        status, body = self.fetch("localhost", "/mattercircle")
        self.assertEqual(status, 200)
        self.assertIn("non-petroleum factory", body)
        self.assertIn("toiletries", body)
        sheet = body.split('class="theme-rich"', 1)[0]
        self.assertNotIn("Phenomatch", sheet)
        self.assertNotIn("unnaturalfertility", sheet)
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
        self.assertIn("Products", body)
        self.assertIn("Services", body)
        self.assertIn('href="/acashi"', body)
        self.assertIn(">acashi</a>", body)
        self.assertIn("schedule wellness", body)
        self.assertIn("Humanehealth store", body)
        self.assertIn("unnaturalfertility", body)
        self.assertNotIn("Clinic network.", body)
        self.assertNotIn("Phenomatch", body)
        self.assertNotIn("Antiporn", body)
        self.assertNotIn("Lessfret", body)
        self.assertNotIn("Planet", body)
        self.assertNotIn('class="tile"', body)
        self.assertNotIn("stage-6", body)
        self.assertNotIn("fineprint", body)
        status, offer = self.fetch("humanehealth.devoutshaman.com", "/ops/wellness")
        self.assertEqual(status, 200)
        self.assertIn(">Book</button>", offer)
        status, store = self.fetch("humanehealth.devoutshaman.com", "/products")
        self.assertEqual(status, 200)
        self.assertIn(">Buy</button>", store)

        status, body = self.fetch("mattercircle.devoutshaman.com")
        self.assertEqual(status, 200)
        self.assertIn("Mattercircle", body)
        self.assertIn("non-petroleum factory", body)
        self.assertIn("prefab housing", body)
        self.assertNotIn("Factory essentials.", body)
        sheet = body.split('class="theme-rich"', 1)[0]
        self.assertNotIn("Phenomatch", sheet)
        self.assertNotIn("physics", sheet.lower())
        self.assertNotIn("unnaturalfertility", sheet)
        self.assertNotIn("Planet", body)
        self.assertNotIn('class="tile"', body)

    def test_offer_request(self) -> None:
        conn = HTTPConnection("127.0.0.1", PORT, timeout=5)
        payload = (
            "house=humanehealth&offering=schedule+wellness&action=book"
            "&name=Ada&email=ada@example.com&next=/ops/wellness"
        )
        try:
            conn.request(
                "POST",
                "/offer",
                body=payload,
                headers={
                    "Host": "humanehealth.devoutshaman.com",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Content-Length": str(len(payload)),
                },
            )
            res = conn.getresponse()
            body = res.read().decode("utf-8")
            self.assertEqual(res.status, 200)
            self.assertIn("Noted. The house will write back.", body)
            self.assertIn('href="/ops/wellness"', body)
        finally:
            conn.close()

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
