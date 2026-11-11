"""NAS Monitor: pausar un NAS sin borrarlo. Pausado no se consulta, no revisa certificados, no avisa en el estado ni en el Resumen y la
página lo muestra como «Pausado». La pausa va por su propia ruta (solo admin): editar el NAS la conserva y no se toca la huella fijada.
EN: NAS Monitor: pause a NAS without deleting it. Paused, it is not polled, its certificates are not checked, it raises no warning in the
status or the Overview and the page shows it as "Paused". The pause has its own route (admin only): editing the NAS keeps it and the pinned
fingerprint is left alone."""
import unittest
from pathlib import Path

from tests import support
from tests.support import ADMIN, READONLY

ROOT = Path(__file__).resolve().parents[1]
m = support.load("nas-monitor/server.py")
NAS = {"id": "np1", "name": "nas1", "type": "truenas", "host": "192.0.2.20", "port": 443, "https": True, "verify_tls": False,
       "user": "ro", "api_key": "k-secret", "timeout": 8, "tls_pin": {"host": "192.0.2.20", "fp": "ab" * 32}}


class Store(unittest.TestCase):
    def setUp(self):
        m.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.old, self.ep = m.load_nas(), m.ensure_poller
        m.ensure_poller = lambda n: None
        m.save_nas([dict(NAS)])
    def tearDown(self):
        m.ensure_poller = self.ep; m.save_nas(self.old); m._cache.pop("np1", None)

    def test_editing_keeps_the_pause_and_the_form_cannot_set_it(self):
        cur = {**NAS, "enabled": False}
        self.assertFalse(m.validate({"name": "nuevo"}, cur)["enabled"])
        self.assertNotIn("enabled", m.validate({"name": "nuevo", "enabled": False}, dict(NAS)))
        self.assertNotIn("enabled", m.validate({"type": "truenas", "name": "x", "host": "192.0.2.21", "user": "ro", "api_key": "k", "enabled": False}))

    def test_health_skips_a_paused_nas(self):
        m.save_nas([{**NAS, "enabled": False}])
        c = m.health_report(True)[1]["checks"]
        self.assertEqual(c["nas_snmp"]["level"], m.auth.OK); self.assertIn("1 paused", c["pollers"]["detail"])

    def test_poller_reads_nothing_while_paused(self):
        calls, cfgs = [], iter([{**NAS, "enabled": False}, None])
        old = m.collect, m.load_nas, m.POLL_IDLE, m.POLL_ACTIVE
        m.collect = lambda *a: calls.append(a)
        m.load_nas = lambda: [x for x in [next(cfgs)] if x]
        m.POLL_IDLE = m.POLL_ACTIVE = 0.01
        cc = m.NasCache("np1"); cc.update({"system": {"model": "old"}}); m._cache["np1"] = cc
        try: m._poll("np1")                                           # ends when the NAS disappears
        finally: m.collect, m.load_nas, m.POLL_IDLE, m.POLL_ACTIVE = old
        self.assertEqual(calls, [])
        self.assertEqual(cc.snap()["data"], {}); self.assertIsNone(cc.snap()["ts"])          # no stale data when resumed

    def test_certificates_are_not_checked_while_paused(self):
        src = (ROOT / "nas-monitor/server.py").read_text(encoding="utf-8")
        self.assertIn("if not is_paused(n): check_certs_due(n)", src)
        self.assertIn('if is_paused(n): return self._json(409, {"error": "The NAS is paused"})', src)


class Http(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adm = support.make_user("nas_pause_adm", ADMIN)
        cls.ro = support.make_user("nas_pause_ro", READONLY)
    def setUp(self):
        Store.setUp(self)
        cc = m.NasCache("np1"); cc.update({"system": {"model": "TN"}, "alerts": [{"lv": "crit", "type": "system"}]}); m._cache["np1"] = cc
        self.srv = support.Server(m.H)
    def tearDown(self):
        self.srv.close(); Store.tearDown(self)

    def nas(self): return self.srv.call("GET", "/api/nas?hist=0", token=self.adm)[1]["nas"][0]

    def test_pause_and_resume(self):
        st, d = self.srv.call("POST", "/api/nas/np1/pause", {"paused": True}, token=self.adm)
        self.assertEqual((st, d["nas"]["paused"]), (200, True)); self.assertNotIn("api_key", d["nas"])
        n = self.nas()
        self.assertTrue(n["paused"]); self.assertEqual(n["snap"]["data"], {}); self.assertIsNone(n["snap"]["error"])   # no alerts reach the page or the Overview
        saved = m.load_nas()[0]
        self.assertIs(saved["enabled"], False); self.assertEqual(saved["tls_pin"], NAS["tls_pin"]); self.assertEqual(saved["api_key"], "k-secret")
        st, d = self.srv.call("POST", "/api/nas/np1/pause", {"paused": False}, token=self.adm)
        self.assertEqual((st, d["nas"]["paused"]), (200, False))
        self.assertNotIn("enabled", m.load_nas()[0]); self.assertFalse(self.nas()["paused"])

    def test_only_admin_and_only_true_or_false(self):
        self.assertEqual(self.srv.call("POST", "/api/nas/np1/pause", {"paused": True}, token=self.ro)[0], 403)
        self.assertEqual(self.srv.call("POST", "/api/nas/np1/pause", {"paused": True})[0], 401)
        for bad in ({}, {"paused": "yes"}, {"paused": 1}):
            self.assertEqual(self.srv.call("POST", "/api/nas/np1/pause", bad, token=self.adm)[0], 400, bad)
        self.assertEqual(self.srv.call("POST", "/api/nas/nope/pause", {"paused": True}, token=self.adm)[0], 404)
        self.assertNotIn("enabled", m.load_nas()[0])

    def test_cert_check_refused_while_paused(self):
        self.srv.call("POST", "/api/nas/np1/pause", {"paused": True}, token=self.adm)
        self.assertEqual(self.srv.call("POST", "/api/nas/np1/certs", {}, token=self.adm)[0], 409)


class Pages(unittest.TestCase):
    def test_nas_page(self):
        js = (ROOT / "nas-monitor/static/app.js").read_text(encoding="utf-8")
        self.assertIn("data-on-click=\"pauseNas\"", js); self.assertIn(" pauseNas,", js)
        self.assertIn("fetch('api/nas/'+encodeURIComponent(id)+'/pause'", js)
        self.assertIn("function lvOf(n){if(n.paused)return 'paused';", js)
        self.assertIn("const act=items.filter(n=>!n.paused).length;", js)
        for k in ("pause:", "resume:", "paused:", "pausedMsg:", "pausedOk:", "resumedOk:"): self.assertEqual(js.count(k), 2, k)
        self.assertIn(".cluster-dot.paused{", (ROOT / "nas-monitor/static/app.css").read_text(encoding="utf-8"))

    def test_overview_and_rules_skip_paused(self):
        self.assertIn("const L=(d.nas||[]).filter(n=>!n.paused);", (ROOT / "overview/static/app.js").read_text(encoding="utf-8"))
        self.assertIn("((ok('nas') || {}).nas || []).filter(n => !n.paused).forEach(", (ROOT / "overview/static/rules.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
