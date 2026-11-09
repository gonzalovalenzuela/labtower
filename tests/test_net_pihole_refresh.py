"""Net Monitor: Pi-hole se vuelve a conectar solo. Un ciclo propio refresca los datos al vencer (5 min si respondió, 1 min si falló), sin
depender de los escaneos ni de guardar los ajustes, y el error de inicio de sesión se borra cuando vuelve a funcionar.
EN: Net Monitor: Pi-hole reconnects on its own. Its own loop refreshes the data when it expires (5 min if it answered, 1 min if it failed),
without depending on scans or on saving the settings, and the login error is cleared when it works again."""
import json
import time
import unittest
from pathlib import Path
from unittest import mock

from tests import support

net = support.load("net-monitor/server.py")


class Stop(Exception):
    pass


class Loop(unittest.TestCase):
    def setUp(self):
        self.old = (net.PIHOLE_PASS, net._pihole_ts)
        net.PIHOLE_PASS = "x"
    def tearDown(self): net.PIHOLE_PASS, net._pihole_ts = self.old

    def run_one_tick(self):
        calls = []
        with mock.patch.object(net.time, "sleep", side_effect=[None, Stop()]), \
             mock.patch.object(net, "refresh_pihole_cache", lambda: calls.append(1)), self.assertRaises(Stop):
            net._pihole_loop()
        return len(calls)

    def test_refreshes_when_expired(self):
        net._pihole_ts = time.time() - net.PIHOLE_TTL - 1
        self.assertEqual(self.run_one_tick(), 1)

    def test_waits_while_fresh_or_without_password(self):
        net._pihole_ts = time.time()
        self.assertEqual(self.run_one_tick(), 0)
        net._pihole_ts, net.PIHOLE_PASS = 0, ""
        self.assertEqual(self.run_one_tick(), 0)

    def test_started_with_the_service(self):
        src = (Path(net.__file__).parent / "server.py").read_text(encoding="utf-8")
        i = src.index("def start_auto_scan():")
        self.assertIn('threading.Thread(target=_pihole_loop, daemon=True, name="net-pihole").start()', src[i:i + 600])


class Recovers(unittest.TestCase):
    """Pi-hole cae y vuelve: el estado pasa de error a conectado sin tocar nada. / EN: Pi-hole goes down and back: error to connected untouched."""
    def setUp(self):
        self.old = (net._pihole_request, net._pihole_logout, net.PIHOLE_PASS, net.PIHOLE_HOSTS)
        net.PIHOLE_PASS, net.PIHOLE_HOSTS = "x", "192.0.2.2"
        net._pihole_logout = lambda h, s: None
        net._pihole_cache.clear(); net._pihole_last_err.clear(); self.down = True
        def req(host, path, method="GET", data=None, sid=None):
            if self.down: raise RuntimeError("timed out")
            if path == "/api/auth": return {"session": {"sid": "s1"}}
            if path == "/api/network/devices": return {"devices": [{"hwaddr": "aa:bb:cc:00:00:01", "ips": [{"ip": "192.0.2.5", "name": "nas"}]}]}
            return {}
        net._pihole_request = req
    def tearDown(self): net._pihole_request, net._pihole_logout, net.PIHOLE_PASS, net.PIHOLE_HOSTS = self.old

    def test_error_then_connected(self):
        net.refresh_pihole_cache()
        self.assertFalse(net._pihole_diag["login"]); self.assertIn("timed out", net._pihole_diag["errors"]["login"])
        self.assertLess(net._pihole_ts, time.time() - net.PIHOLE_TTL + 61)          # retried within a minute
        self.down = False
        net.refresh_pihole_cache()
        self.assertTrue(net._pihole_diag["login"]); self.assertEqual(net._pihole_diag["errors"], {})
        self.assertNotIn("192.0.2.2", net._pihole_last_err)
        self.assertEqual(net._pihole_cache["192.0.2.5"]["hostname"], "nas")

    def test_no_session_gives_its_own_message(self):
        self.down = False
        net._pihole_last_err["192.0.2.2"] = "an old error"
        net._pihole_request = lambda h, p, method="GET", data=None, sid=None: {}          # answers, but without a session
        net.refresh_pihole_cache()
        self.assertEqual(net._pihole_diag["errors"]["login"], "login failed: Pi-hole did not return a session")
        self.assertNotIn("an old error", json.dumps(net._pihole_diag))


class Dot(unittest.TestCase):
    """El punto de la barra recibe el estado real en /api/hosts (antes nunca llegaba y quedaba gris). / EN: The bar dot gets the real state in /api/hosts."""
    @classmethod
    def setUpClass(cls):
        net.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.admin = support.make_user("phadm", support.ADMIN); cls.ro = support.make_user("phro", support.READONLY)
        cls.srv = support.Server(net.H)
    @classmethod
    def tearDownClass(cls): cls.srv.close()
    def setUp(self): self.old = net.PIHOLE_PASS; net.PIHOLE_PASS = "x"; net._pihole_diag.clear()
    def tearDown(self): net.PIHOLE_PASS = self.old; net._pihole_diag.clear()

    def test_states(self):
        self.assertEqual(net.pihole_state(), {"enabled": True, "ok": None, "ts": None})            # no read yet: connecting
        net._pihole_diag.update({"ts": 5, "login": True, "errors": {}})
        self.assertTrue(net.pihole_state()["ok"])
        net._pihole_diag.update({"login": False, "errors": {"login": "Connection refused at 192.0.2.2"}})
        self.assertEqual(net.pihole_state(True)["error"], "Connection refused at 192.0.2.2")
        self.assertNotIn("error", net.pihole_state(False))                                        # only administrators see the reason
        net.PIHOLE_PASS = ""
        self.assertFalse(net.pihole_state()["enabled"])

    def test_sent_with_the_hosts(self):
        net._pihole_diag.update({"ts": 5, "login": False, "errors": {"login": "boom"}})
        _, j = self.srv.call("GET", "/api/hosts", token=self.admin)
        self.assertEqual(j["pihole"], {"enabled": True, "ok": False, "ts": 5, "error": "boom"})
        _, j = self.srv.call("GET", "/api/hosts", token=self.ro)
        self.assertNotIn("error", j["pihole"])

    def test_page_uses_it(self):
        js = (Path(net.__file__).parent / "static/app.js").read_text(encoding="utf-8")
        self.assertIn("if(d.pihole) updatePiholeStatusDot(d.pihole);", js)
        self.assertIn("const st = !p||!p.enabled ? 'off' : p.ok===true ? 'ok' : p.ok===false ? 'fail' : 'wait';", js)
        for k in ("piholeDotOk:", "piholeDotFail:", "piholeDotWait:", "piholeDotOff:"): self.assertEqual(js.count(k), 2, k)
        src = (Path(net.__file__).parent / "server.py").read_text(encoding="utf-8")
        self.assertIn("_pihole_diag.clear()\n            if PIHOLE_PASS:", src)                  # saving shows "connecting" until the new read


if __name__ == "__main__":
    unittest.main()
