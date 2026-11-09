"""2.1.5c: umbrales de volumen por NAS (90/95 por defecto) / per-NAS volume thresholds; sugeridos eliminados / suggested monitors removed."""
import unittest
from pathlib import Path

from tests import support

m = support.load("nas-monitor/server.py")
ROOT = Path(__file__).resolve().parents[1]
BASE = {"name": "N", "host": "192.0.2.20", "version": "2c", "community": "public"}

def snap(pct):
    return {"system": {}, "cpu": {}, "mem": None, "disks": [], "raids": [{"name": "V", "lv": "ok", "status": 1, "pct": pct}]}

class VolThr(unittest.TestCase):
    def test_defaults_and_validation(self):
        c = m.validate(dict(BASE)); self.assertEqual((c["vol_warn"], c["vol_crit"]), (90, 95))
        c = m.validate({**BASE, "vol_warn": 95, "vol_crit": 98}); self.assertEqual((c["vol_warn"], c["vol_crit"]), (95, 98))
        for bad in ({"vol_warn": 95, "vol_crit": 95}, {"vol_warn": 0}, {"vol_crit": 101}, {"vol_warn": "x"}, {"vol_warn": True}):
            with self.assertRaises(ValueError): m.validate({**BASE, **bad})
    def test_kept_on_edit(self):
        cur = m.validate({**BASE, "vol_warn": 92, "vol_crit": 97}); cur["id"] = "a"
        c = m.validate({"name": "N2", "host": "192.0.2.20"}, cur); self.assertEqual((c["vol_warn"], c["vol_crit"]), (92, 97))
    def test_alerts_use_thresholds(self):
        self.assertEqual(m.compute_alerts(snap(84.0), (95, 98)), [])
        self.assertEqual(m.compute_alerts(snap(96.0), (95, 98))[0]["lv"], "warn")
        self.assertEqual(m.compute_alerts(snap(98.0), (95, 98))[0]["lv"], "crit")
        self.assertEqual(m.compute_alerts(snap(92.0))[0]["lv"], "warn")      # default 90/95
    def test_ui_uses_snapshot_thresholds(self):
        a = (ROOT / "nas-monitor/static/app.js").read_text(); o = (ROOT / "overview/static/app.js").read_text()
        self.assertNotIn("VOL_W", a); self.assertIn("thr?.vol_warn", a); self.assertIn("thr?.vol_warn", o); self.assertNotIn("bar(vmax.pct,80,90)", o)
        self.assertIn('id="f-vol-warn"', (ROOT / "nas-monitor/static/index.html").read_text())
    def test_suggested_monitors_removed(self):
        self.assertFalse((ROOT / "overview/static/discover.js").exists())
        self.assertNotIn("c-sug", (ROOT / "overview/static/index.html").read_text())

if __name__ == "__main__": unittest.main()
