"""Proxmox Monitor: editar un cluster (permisos, validación, secreto vacío = conservar, certificado al cambiar host/puerto, clientes que
se rehacen) y la página que ofrece volver a fijar el certificado aunque no haya datos.
EN: Proxmox Monitor: editing a cluster (permissions, validation, empty secret = keep, certificate when host/port change, clients that are
rebuilt) and the page offering to pin the certificate again even without data."""
import unittest
from pathlib import Path
from unittest import mock

from tests import support
from tests.support import ADMIN, READONLY

m = support.load("proxmox-monitor/server.py")
ROOT = Path(__file__).resolve().parents[1]
FP = "aa" * 32
BASE = {"id": "c1", "name": "Lab", "host": "192.0.2.10", "port": 8006, "user": "mon@pve", "token_name": "lt",
        "token_value": "11111111-2222-3333-4444-555555555555", "verify_ssl": False, "fingerprint": FP, "layout": {"order": ["n1"], "pinned": []}}


class Edit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        m.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.admin, cls.ro = support.make_user("pedadm", ADMIN), support.make_user("pedro", READONLY)
        cls.srv = support.Server(m.H)
    @classmethod
    def tearDownClass(cls): cls.srv.close(); m.save_clusters([])
    def setUp(self): m.save_clusters([dict(BASE), {**BASE, "id": "c2", "name": "Other", "host": "192.0.2.11"}])

    def test_permissions_and_not_found(self):
        c = self.srv.call
        self.assertEqual(c("POST", "/api/clusters/c1", {"name": "x"})[0], 401)
        self.assertEqual(c("POST", "/api/clusters/c1", {"name": "x"}, token=self.ro)[0], 403)
        self.assertEqual(c("POST", "/api/clusters/zz", {**BASE, "token_value": ""}, token=self.admin)[0], 404)

    def test_rename_keeps_token_fingerprint_and_layout(self):
        s, j = self.srv.call("POST", "/api/clusters/c1", {**BASE, "name": "Renamed", "token_value": ""}, token=self.admin)
        self.assertEqual(s, 200, j); self.assertNotIn("token_value", j["cluster"])
        c = next(x for x in m.load_clusters() if x["id"] == "c1")
        self.assertEqual((c["name"], c["token_value"], c["fingerprint"], c["layout"]["order"]), ("Renamed", BASE["token_value"], FP, ["n1"]))

    def test_new_secret_and_validation(self):
        call = lambda b: self.srv.call("POST", "/api/clusters/c1", {**BASE, **b}, token=self.admin)[0]
        self.assertEqual(call({"token_value": "99999999-2222-3333-4444-555555555555"}), 200)
        self.assertEqual(next(x for x in m.load_clusters() if x["id"] == "c1")["token_value"], "99999999-2222-3333-4444-555555555555")
        for bad in ({"name": ""}, {"port": 0}, {"user": "bad user"}, {"token_name": "a/b"}, {"token_value": "a b"}, {"host": "-x"}):
            self.assertEqual(call(bad), 400, bad)

    def test_moving_needs_the_certificate_and_no_duplicates(self):
        call = lambda b: self.srv.call("POST", "/api/clusters/c1", {**BASE, "token_value": "", "fingerprint": None, **b}, token=self.admin)
        self.assertEqual(call({"host": "192.0.2.20"})[0], 400)                                  # new host, no confirmed certificate
        self.assertEqual(call({"host": "192.0.2.11", "fingerprint": "bb" * 32})[0], 409)         # host:port of another cluster
        s, _ = call({"host": "192.0.2.20", "port": 8007, "fingerprint": "BB:" * 31 + "BB"})
        self.assertEqual(s, 200)
        c = next(x for x in m.load_clusters() if x["id"] == "c1")
        self.assertEqual((c["host"], c["port"], c["fingerprint"]), ("192.0.2.20", 8007, "bb" * 32))

    def test_connection_test_uses_the_stored_secret(self):
        seen = {}
        class Fake:
            def __init__(self, host, port, user, tname, tval, fingerprint=None): seen["tval"] = tval
            def version(self): return "9.2"
            def nodes(self): return [1, 2]
        with mock.patch.object(m, "PVEClient", Fake):
            s, j = self.srv.call("POST", "/api/test", {**BASE, "token_value": "", "id": "c1", "fingerprint": FP}, token=self.admin)
        self.assertEqual((s, j.get("ok"), seen["tval"]), (200, True, BASE["token_value"]))


class ClientFor(unittest.TestCase):
    def test_reuse_adopt_fingerprint_or_rebuild(self):
        a = m._client_for(BASE)
        self.assertIs(m._client_for(BASE, a), a)
        b = m._client_for({**BASE, "fingerprint": "cc" * 32}, a)
        self.assertIs(b, a); self.assertEqual(a.fingerprint, "cc" * 32)                  # a re-pin keeps the client
        for k, v in (("host", "192.0.2.30"), ("token_value", "x"), ("user", "other@pve"), ("port", 8007)):
            self.assertIsNot(m._client_for({**BASE, k: v}, a), a, k)                      # an edit rebuilds it

    def test_threads_use_the_helper(self):
        src = (ROOT / "proxmox-monitor/server.py").read_text()
        self.assertEqual(src.count("client = _client_for(cur, client)"), 5)
        self.assertNotIn("if fp != client.fingerprint: client.fingerprint = fp; client.close()\n            _", src)


class Page(unittest.TestCase):
    def setUp(self): self.js = (ROOT / "proxmox-monitor/static/app.js").read_text()

    def test_edit_button_and_form(self):
        for k in ('data-on-click="openEditCluster"', "function openEditCluster(id)", "openEditCluster,", "token_value:tval,fingerprint:pendingFp.fp,...(editingId?{id:editingId}:{})",
                  "'api/clusters'+(edit?'/'+encodeURIComponent(edit):'')"):
            self.assertIn(k, self.js, k)
        for k in ("editClusterTitle:", "editCluster:", "tokenKeep:", "clusterSaved:"): self.assertEqual(self.js.count(k), 2, k)

    def test_repin_without_data(self):
        self.assertIn("if(!snap?.ts&&!snap?.error){", self.js)
        i = self.js.index("if(snap.error&&!snap.data?.nodes?.length){")
        self.assertIn("snap.error_kind==='cert'", self.js[i:i + 400]); self.assertIn('data-on-click="pinCluster"', self.js[i:i + 900])


if __name__ == "__main__":
    unittest.main()
