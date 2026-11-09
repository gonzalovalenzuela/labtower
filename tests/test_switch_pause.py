"""Switch Monitor: un switch se puede pausar sin borrarlo (por ejemplo, si otra instalación de LabTower ya lo vigila: estos switches admiten
una sola sesión). Pausado no se lee, no genera alertas, no aparece en el Resumen y se muestra como «Pausado».
EN: Switch Monitor: a switch can be paused without deleting it (for instance when another LabTower already watches it: these switches allow
a single session). Paused, it is not read, raises no alerts, is left out of the Overview and is shown as "Paused"."""
import unittest
from pathlib import Path

from tests import test_switches as ts

ROOT = Path(__file__).resolve().parents[1]


class Pause(unittest.TestCase):
    # Misma preparación que los tests del administrador de switches. / EN: Same setup as the switch manager tests.
    setUp, add, feed = ts.ManagerTests.setUp, ts.ManagerTests.add, ts.ManagerTests.feed

    def test_paused_has_no_alerts_and_leaves_the_overview(self):
        sid = self.add()["id"]
        self.feed(sid, ts.mk_snap("zx310s", 3_000_000.0, [ts.mk_port(1)], temp=85))
        self.assertTrue(self.m.state()["switches"][0]["alerts"])
        self.m.save_switch({"id": sid, "enabled": False})
        s = self.m.state()["switches"][0]
        self.assertEqual((s["paused"], s["enabled"], s["alerts"]), (True, False, []))
        self.assertEqual(self.m.summary(), {"switches": [], "lv": "ok"})
        self.m.save_switch({"id": sid, "enabled": True})
        self.assertFalse(self.m.state()["switches"][0]["paused"])
        self.assertEqual(len(self.m.summary()["switches"]), 1)

    def test_no_reader_thread_while_paused(self):
        sid = self.add()["id"]
        self.m.save_switch({"id": sid, "enabled": False})
        del self.m.reconcile                                                    # the real one
        self.m.reconcile()
        self.assertNotIn(sid, self.m.workers)

    def test_page_offers_the_switch_and_shows_it(self):
        js = (ROOT / "net-monitor/static/switches.js").read_text(encoding="utf-8")
        for k in ("id=\"m-on\"${c.enabled === false ? '' : ' checked'}", "enabled: $('m-on').checked", "s.paused ? `<span class=\"sw-pill\">${esc(t('swPaused'))}</span>`",
                  "A = S.filter(s => !s.paused)", "kpi('teal', upSw + '/' + A.length"):
            self.assertIn(k, js, k)
        for k in ("swPaused:", "swActive:"): self.assertEqual(js.count(k), 2, k)
        self.assertIn(".sw-card.paused>*:not(.sw-head){opacity:.55}", (ROOT / "net-monitor/static/app.css").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
