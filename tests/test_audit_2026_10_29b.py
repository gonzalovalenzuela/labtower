"""Entradas con tipo inesperado / Wrongly-typed JSON input must give 400-class answers, never a dropped connection."""
import unittest
from tests import support
from tests.support import ADMIN

ODD = ([], {}, 123, ["10.0.0.1"], {"a": 1}, True)


class OddTypes(unittest.TestCase):
    def _run(self, rel, method, path, field, extra=None, ok=(200, 201, 400, 404, 409)):
        mod = support.load(rel); srv = support.Server(mod.H)
        try:
            tok = support.make_user("odd" + rel.split("-")[0], ADMIN)
            for v in ODD:
                body = dict(extra or {}); body[field] = v
                st, _ = srv.call(method, path, body, token=tok, headers={"Origin": "http://127.0.0.1"})
                self.assertIn(st, ok, f"{path} {field}={v!r} -> {st}")
        finally:
            srv.close()

    def test_net_hosts_delete_ip(self):      self._run("net-monitor/server.py", "POST", "/api/hosts/delete", "ip")
    def test_net_hosts_update_ip(self):      self._run("net-monitor/server.py", "POST", "/api/hosts/update", "ip")
    def test_proxmox_cluster_name(self):
        self._run("proxmox-monitor/server.py", "POST", "/api/clusters", "name",
                  {"host": "pve.example", "user": "u@pam", "token_name": "t", "token_value": "v"})
    def test_wol_ping_ip(self):              self._run("wol-console/server.py", "POST", "/api/ping", "ip")


if __name__ == "__main__":
    unittest.main()
