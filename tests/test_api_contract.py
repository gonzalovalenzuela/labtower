"""Contrato de las APIs: sin sesión → 401, lectura sola no escribe, y las peticiones entre sitios se bloquean."""
import unittest
from tests import support
from tests.support import ADMIN, READONLY, NONE

# (módulo, ruta GET que pide sesión)
PROTECTED_GET = [
    ("overview/server.py", ["/api/system", "/api/events", "/api/pihistory", "/api/pidetail"]),
    ("nut-monitor/server.py", ["/api/servers", "/api/ups", "/api/history", "/api/config"]),
    ("wol-console/server.py", ["/api/devices", "/api/wake_log", "/api/config"]),
    ("net-monitor/server.py", ["/api/hosts", "/api/scan/status", "/api/config"]),
    ("proxmox-monitor/server.py", ["/api/clusters"]),
    ("nas-monitor/server.py", ["/api/nas"]),
    ("dns-monitor/server.py", ["/api/dns"]),
    ("wan-monitor/server.py", ["/api/wan"]),
]
# (módulo, ruta POST de escritura, cuerpo)
WRITE_POST = [
    ("nut-monitor/server.py", "/api/servers", {"name": "x", "host": "nut.example", "port": 3493}),
    ("wol-console/server.py", "/api/wake", {"mac": "aa:bb:cc:dd:ee:ff"}),
    ("net-monitor/server.py", "/api/scan/start", {}),
    ("proxmox-monitor/server.py", "/api/clusters", {"name": "x", "host": "pve.example"}),
    ("nas-monitor/server.py", "/api/nas", {"name": "x", "host": "nas.example", "user": "u"}),
    ("dns-monitor/server.py", "/api/dns", {"name": "x", "url": "192.0.2.9", "password": "p"}),
    ("wan-monitor/server.py", "/api/wan/config", {"interval": 60}),
]

class ApiContract(unittest.TestCase):
    servers = {}
    @classmethod
    def setUpClass(cls):
        cls.admin = support.make_user("adm", ADMIN); cls.ro = support.make_user("rdo", READONLY); cls.nobody = support.make_user("nob", NONE)
        for rel in {r for r, _ in PROTECTED_GET}:
            cls.servers[rel] = support.Server(support.load(rel).H)
    @classmethod
    def tearDownClass(cls):
        for s in cls.servers.values(): s.close()

    def test_protected_get_without_session_is_401(self):
        for rel, paths in PROTECTED_GET:
            for p in paths:
                with self.subTest(module=rel, path=p):
                    self.assertEqual(self.servers[rel].call("GET", p)[0], 401)
                    self.assertEqual(self.servers[rel].call("GET", p, token="0" * 64)[0], 401, "cookie falsa")

    def test_user_without_module_permission_is_rejected(self):
        for rel, paths in PROTECTED_GET:
            if rel.startswith("overview"): continue          # Resumen: cualquier sesión válida; cada tarjeta se filtra por permiso
            for p in paths[:1]:
                with self.subTest(module=rel, path=p):
                    self.assertIn(self.servers[rel].call("GET", p, token=self.nobody)[0], (401, 403))

    def test_readonly_user_cannot_write(self):
        for rel, p, body in WRITE_POST:
            with self.subTest(module=rel, path=p):
                self.assertIn(self.servers[rel].call("POST", p, body, token=self.ro)[0], (401, 403))

    def test_cross_site_post_is_blocked_even_with_admin_session(self):
        for rel, p, body in WRITE_POST:
            with self.subTest(module=rel, path=p):
                s, j = self.servers[rel].call("POST", p, body, token=self.admin, headers={"Sec-Fetch-Site": "cross-site"})
                self.assertEqual(s, 403, j)
                s, j = self.servers[rel].call("POST", p, body, token=self.admin, headers={"Origin": "http://evil.example", "Host": "pi.local"})
                self.assertEqual(s, 403, j)

    def test_health_hides_details_without_session(self):
        for rel, _ in PROTECTED_GET:
            with self.subTest(module=rel):
                s, j = self.servers[rel].call("GET", "/api/health")
                self.assertIn(s, (200, 503))
                self.assertNotIn("detail", repr(j).replace("'detail': ''", ""), "el detalle de salud solo con sesión")

    def test_pidetail_levels(self):
        ov = self.servers["overview/server.py"]
        s, j = ov.call("GET", "/api/pidetail", token=self.ro); self.assertEqual(s, 200); self.assertFalse(j["full"]); self.assertNotIn("users", j)
        s, j = ov.call("GET", "/api/pidetail", token=self.admin); self.assertEqual(s, 200); self.assertTrue(j["full"]); self.assertIn("users", j)
if __name__ == "__main__": unittest.main()
