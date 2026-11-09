"""2.1.4s: Proxmox expone las MAC e IP de sus VM/CT para Net Monitor / Proxmox exposes guests' MACs and IPs for Net Monitor."""
import unittest

from tests import support
from tests.support import READONLY

m = support.load("proxmox-monitor/server.py")

class Fake:
    def __init__(self): self.calls = []
    def get(self, path):
        self.calls.append(path)
        d = {
            "/nodes/n1/qemu/100/config": {"data": {"net0": "virtio=BC:24:11:AA:BB:CC,bridge=vmbr0", "net1": "e1000=de:ad:be:ef:00:01,bridge=vmbr1", "agent": "1"}},
            "/nodes/n1/qemu/100/agent/network-get-interfaces": {"data": {"result": [
                {"name": "lo", "ip-addresses": [{"ip-address": "127.0.0.1", "ip-address-type": "ipv4"}]},
                {"name": "eth0", "ip-addresses": [{"ip-address": "192.0.2.10", "ip-address-type": "ipv4"}, {"ip-address": "fe80::1", "ip-address-type": "ipv6"}]}]}},
            "/nodes/n1/qemu/101/config": {"data": {"net0": "virtio=BC:24:11:00:00:01,bridge=vmbr0", "agent": "0"}},
            "/nodes/n1/lxc/200/config": {"data": {"net0": "name=eth0,bridge=vmbr0,hwaddr=BC:24:11:22:33:44,ip=192.0.2.20/24,gw=192.0.2.1"}},
            "/nodes/n1/lxc/201/config": {"data": {"net0": "name=eth0,bridge=vmbr0,hwaddr=BC:24:11:55:66:77,ip=dhcp"}},
            "/nodes/n1/lxc/201/interfaces": {"data": [{"name": "lo", "inet": "127.0.0.1/8"}, {"name": "eth0", "inet": "192.0.2.21/24"}]},
        }
        if path not in d: raise RuntimeError("HTTP 403")
        return d[path]

class Cache:
    def snap(self):
        return {"data": {"nodes": [
            {"name": "n1", "status": "online",
             "vms": [{"vmid": 100, "name": "web", "status": "running"}, {"vmid": 101, "name": "off", "status": "stopped"}, {"vmid": 999, "name": "tpl", "status": "stopped", "template": 1}],
             "cts": [{"vmid": 200, "name": "ct-static", "status": "stopped"}, {"vmid": 201, "name": "ct-dhcp", "status": "running"}]},
            {"name": "n2", "status": "offline", "vms": [{"vmid": 5, "name": "x", "status": "stopped"}], "cts": []}]}}

class Round(unittest.TestCase):
    def test_macs_and_ips(self):
        f = Fake(); m._guest_round({"id": "c1", "name": "Lab"}, f, Cache())
        g = {x["vmid"]: x for x in m._gnets["c1"]}
        self.assertEqual(set(g), {100, 101, 200, 201})                      # no template, no offline node
        self.assertEqual(g[100]["macs"], ["bc:24:11:aa:bb:cc", "de:ad:be:ef:00:01"])
        self.assertEqual(g[100]["ips"], ["192.0.2.10"])                     # loopback and IPv6 dropped
        self.assertEqual((g[100]["type"], g[100]["cluster"], g[100]["node"]), ("qemu", "Lab", "n1"))
        self.assertEqual(g[101]["ips"], [])                                 # stopped + agent off: MAC only
        self.assertEqual(g[200]["ips"], ["192.0.2.20"])                     # static IP from the config
        self.assertEqual((g[201]["macs"], g[201]["ips"]), (["bc:24:11:55:66:77"], ["192.0.2.21"]))
        self.assertNotIn("/nodes/n1/qemu/101/agent/network-get-interfaces", f.calls)   # the agent is only asked when enabled and running

    def test_missing_permissions_keep_the_guest(self):
        class Deny(Fake):
            def get(self, path): raise RuntimeError("HTTP 403")
        m._guest_round({"id": "c2", "name": "Lab"}, Deny(), Cache())
        self.assertEqual(len(m._gnets["c2"]), 4)
        self.assertTrue(all(x["macs"] == [] and x["ips"] == [] for x in m._gnets["c2"]))

class Api(unittest.TestCase):
    def test_endpoint_needs_a_session(self):
        ro = support.make_user("pg_ro", READONLY)
        srv = support.Server(m.H)
        old = m.load_clusters
        m.load_clusters = lambda: [{"id": "c1", "name": "Lab", "host": "h", "user": "u", "token_name": "t", "token_value": "v"}]
        try:
            m._guest_round({"id": "c1", "name": "Lab"}, Fake(), Cache())
            self.assertIn(srv.call("GET", "/api/guests")[0], (401, 403))
            code, j = srv.call("GET", "/api/guests", token=ro)
            self.assertEqual(code, 200); self.assertEqual((len(j["guests"]), j["with_mac"], j["with_ip"]), (4, 4, 3))
            self.assertNotIn("token_value", str(j))
        finally: m.load_clusters = old

if __name__ == "__main__": unittest.main()
