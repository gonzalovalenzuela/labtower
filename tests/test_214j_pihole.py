"""2.1.4j: Net Monitor toma los nombres de Pi-hole también de «Local DNS» y de las concesiones DHCP / names also from Local DNS and DHCP leases."""
import unittest
from tests import support

net = support.load("net-monitor/server.py")

class Parsers(unittest.TestCase):
    def test_local_hosts(self):
        r = net.pihole_parse_local_hosts(["192.0.2.5 nas01 nas01.lan", "192.0.2.6\tweb # comentario", "# solo comentario", "bad name", "192.0.2.5 otro", "192.0.2.7", 5, "2001:db8::1 v6host"])
        self.assertEqual(r, {"192.0.2.5": "nas01", "192.0.2.6": "web", "2001:db8::1": "v6host"})
        self.assertEqual(net.pihole_parse_local_hosts(None), {})
    def test_leases(self):
        r = net.pihole_parse_leases([{"ip": "192.0.2.10", "name": "laptop.local", "hwaddr": "aa:bb:cc:dd:ee:ff"}, {"ip": "192.0.2.11", "name": "*", "hwaddr": "x"},
                                     {"ip": "nope", "name": "z"}, {"ip": "192.0.2.12", "name": "tv", "hwaddr": "no-mac"}, "x"])
        self.assertEqual(r, {"192.0.2.10": {"hostname": "laptop", "mac": "aa:bb:cc:dd:ee:ff"}, "192.0.2.12": {"hostname": "tv", "mac": ""}})

class Refresh(unittest.TestCase):
    def setUp(self):
        self.old = (net._pihole_request, net._pihole_login, net._pihole_logout, net.PIHOLE_PASS, net.PIHOLE_HOSTS)
        net.PIHOLE_PASS, net.PIHOLE_HOSTS = "x", "192.0.2.2"
        net._pihole_login = lambda h, p: "sid"; net._pihole_logout = lambda h, s: None
        net._pihole_cache.clear(); self.fail = False; self.calls = []
        def req(host, path, method="GET", data=None, sid=None):
            self.calls.append(path)
            if self.fail: raise RuntimeError("down")
            if path == "/api/network/devices":
                return {"devices": [{"hwaddr": "aa:bb:cc:00:00:01", "macVendor": "Acme", "ips": [{"ip": "192.0.2.5", "name": "reverse-name.local"}, {"ip": "192.0.2.6", "name": "only-reverse"}]}]}
            if path == "/api/dhcp/leases": return {"leases": [{"ip": "192.0.2.6", "name": "from-dhcp", "hwaddr": "aa:bb:cc:00:00:06"}, {"ip": "192.0.2.9", "name": "lease-only", "hwaddr": ""}]}
            if path == "/api/config/dns/hosts": return {"config": {"dns": {"hosts": ["192.0.2.5 my-nas"]}}}
            raise RuntimeError("HTTP 404")
        net._pihole_request = req
    def tearDown(self): net._pihole_request, net._pihole_login, net._pihole_logout, net.PIHOLE_PASS, net.PIHOLE_HOSTS = self.old
    def test_priority_local_dns_then_dhcp_then_reverse(self):
        net.refresh_pihole_cache(); c = net._pihole_cache
        self.assertEqual(c["192.0.2.5"]["hostname"], "my-nas")            # Local DNS beats the reverse name
        self.assertEqual(c["192.0.2.5"]["vendor"], "Acme")
        self.assertEqual(c["192.0.2.6"]["hostname"], "from-dhcp")         # DHCP beats the reverse name
        self.assertEqual(c["192.0.2.6"]["mac"], "aa:bb:cc:00:00:01")      # the MAC Pi-hole already knew is kept
        self.assertEqual(c["192.0.2.9"]["hostname"], "lease-only")        # known only from the lease
    def test_missing_optional_endpoints_do_not_break_the_names(self):
        orig = net._pihole_request
        net._pihole_request = lambda h, p, method="GET", data=None, sid=None: orig(h, p, method, data, sid) if p == "/api/network/devices" else (_ for _ in ()).throw(RuntimeError("HTTP 403"))
        net.refresh_pihole_cache()
        self.assertEqual(net._pihole_cache["192.0.2.5"]["hostname"], "reverse-name")
        g = net._pihole_diag                                  # 2.1.4m: the panel can say WHY the Local DNS names are missing
        self.assertEqual((g["login"], g["leases"], g["local"]), (True, None, None))
        self.assertIn("403", g["errors"]["local"]); self.assertIn("403", g["errors"]["leases"])
    def test_diag_counts(self):
        net.refresh_pihole_cache(); g = net._pihole_diag
        self.assertEqual((g["devices"], g["leases"], g["local"], g["errors"]), (2, 2, 1, {}))
    def test_outage_keeps_known_names_and_retries_soon(self):
        net.refresh_pihole_cache(); self.assertTrue(net._pihole_cache)
        self.fail = True; net.refresh_pihole_cache()
        self.assertEqual(net._pihole_cache["192.0.2.5"]["hostname"], "my-nas")
        import time
        self.assertLess(net._pihole_ts + net.PIHOLE_TTL - time.time(), 61)
    def test_single_flight(self):
        self.assertTrue(net._pihole_busy.acquire(blocking=False))
        try:
            net.refresh_pihole_cache(); self.assertEqual(self.calls, [])
        finally: net._pihole_busy.release()

if __name__ == "__main__": unittest.main()
