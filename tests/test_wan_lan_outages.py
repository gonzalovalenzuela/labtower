"""WAN Monitor: «Calidad y disponibilidad» muestra, junto al total de cortes, los de la red local y los de la WAN (WAN del router e
Internet), para comparar unos con otros en 24 h, 7 y 30 días.
EN: WAN Monitor: «Quality and availability» shows, next to the total outages, the local network ones and the WAN ones (router WAN and
Internet), to compare them over 24 h, 7 and 30 days."""
import unittest
from pathlib import Path

from tests import support

m = support.load("wan-monitor/server.py")
ROOT = Path(__file__).resolve().parents[1]
NOW = 2_000_000_000


class Counts(unittest.TestCase):
    def test_each_window_carries_lan_and_wan(self):
        outs = [(NOW - 3600, NOW - 3000, "lan"), (NOW - 7200, NOW - 7000, "wan"), (NOW - 9000, NOW - 8900, "internet"), (NOW - 100, None, "internet")]
        r = m.wst.outage_stats(outs, NOW, 86400, NOW - 30 * 86400)
        self.assertEqual((r["count"], r["scopes"]["lan"], r["scopes"]["wan"] + r["scopes"]["internet"]), (4, 1, 3))


class Page(unittest.TestCase):
    def setUp(self): self.js = (ROOT / "wan-monitor/static/app.js").read_text()

    def test_columns_after_the_total(self):
        self.assertIn("<th>${esc(t('stOutN'))}</th><th>${esc(t('stOutLan'))}</th><th>${esc(t('stOutWan'))}</th><th>${esc(t('stOutMean'))}</th>", self.js)
        self.assertIn("(a.count?esc(a.count):esc(t('stNone')))}</td><td>${lan}</td><td>${wan}</td>", self.js)

    def test_wan_includes_internet(self):
        self.assertIn("[esc(s.lan||0),esc((s.wan||0)+(s.internet||0))]", self.js)
        self.assertIn("a.count==null?['—','—']", self.js)

    def test_fits_its_card(self):
        css = (ROOT / "wan-monitor/static/app.css").read_text()
        self.assertIn('<table class="wan-table st-table">', self.js)
        for k in (".st-table thead th{white-space:normal;vertical-align:bottom}",
                  "@container (max-width:1100px){.wan-table.st-table thead th,.wan-table.st-table tbody td{padding-left:8px;padding-right:8px}}",
                  "@container (max-width:800px){.wan-table.st-table thead th,.wan-table.st-table tbody td{padding-left:5px;padding-right:5px}}",
                  "@container (max-width:720px){.wan-table.st-table thead th,.wan-table.st-table tbody td{padding-left:3px;padding-right:3px}}"):
            self.assertIn(k, css, k)

    def test_texts(self):
        for k, en, es in (("stOutLan", "LAN outages", "Cortes LAN"), ("stOutWan", "WAN outages", "Cortes WAN")):
            self.assertIn(f'"{k}": "{en}"', self.js); self.assertIn(f'"{k}": "{es}"', self.js)


if __name__ == "__main__":
    unittest.main()
