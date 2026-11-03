"""WOL (estado en vivo), WAN (historial de IP y traceroute por corte) y DNS (sondeo de upstreams y prueba de resolución)."""
import socket, struct, threading, time, unittest
from tests import support
from tests.support import ADMIN, READONLY

wol = support.load("wol-console/server.py")
wan = support.load("wan-monitor/server.py")
dns = support.load("dns-monitor/server.py")
dnsq = dns.dnsq


class WolStatus(unittest.TestCase):
    DEVS = [{"id": "a" * 8 + "-0000-0000-0000-" + "0" * 12, "name": "pc", "mac": "AA:BB:CC:DD:EE:01", "ip": "192.0.2.10", "port": 9, "tag": "PC"},
            {"id": "b" * 8 + "-0000-0000-0000-" + "0" * 12, "name": "noip", "mac": "AA:BB:CC:DD:EE:02", "ip": None, "port": 9, "tag": "PC"},
            {"id": "c" * 8 + "-0000-0000-0000-" + "0" * 12, "name": "net", "mac": "AA:BB:CC:DD:EE:03", "ip": "192.0.2.30", "port": 9, "tag": "PC"}]

    @classmethod
    def setUpClass(cls):
        cls.ro = support.make_user("wro", support.READONLY); cls.none = support.make_user("wnone", support.NONE)
        cls.srv = support.Server(wol.H)
    @classmethod
    def tearDownClass(cls): cls.srv.close()
    def setUp(self):
        self.calls = []
        self._o = (wol.load_devices, wol.load_net_hosts, wol.ping_host)
        wol.load_devices = lambda: [dict(d) for d in self.DEVS]
        wol.load_net_hosts = lambda: {"aabbccddee03": {"ip": "192.0.2.99", "online": True}}
        wol.ping_host = lambda ip, timeout=1.0: (self.calls.append(ip), ip.endswith(".10") or ip.endswith(".99"))[1]
        wol._probe_cache.clear()
    def tearDown(self): wol.load_devices, wol.load_net_hosts, wol.ping_host = self._o

    def test_device_ip_prefers_net_monitor_and_rejects_junk(self):
        self.assertEqual(wol.device_ip(self.DEVS[2], wol.load_net_hosts()), "192.0.2.99")
        self.assertEqual(wol.device_ip(self.DEVS[1], {}), "")
        self.assertEqual(wol.device_ip({"mac": "x", "ip": "-oProxy=evil"}, {}), "")

    def test_status_of_everyone(self):
        s, j = self.srv.call("GET", "/api/status", token=self.ro)
        self.assertEqual(s, 200)
        st = j["status"]
        self.assertTrue(st[self.DEVS[0]["id"]]); self.assertIsNone(st[self.DEVS[1]["id"]]); self.assertTrue(st[self.DEVS[2]["id"]])
        self.assertEqual(sorted(self.calls), ["192.0.2.10", "192.0.2.99"])       # the device without IP is not pinged

    def test_cache_and_single_device_is_fresh(self):
        self.srv.call("GET", "/api/status", token=self.ro); n = len(self.calls)
        self.srv.call("GET", "/api/status", token=self.ro); self.assertEqual(len(self.calls), n)     # reused
        time.sleep(1.1)
        s, j = self.srv.call("GET", "/api/status?id=" + self.DEVS[0]["id"], token=self.ro)
        self.assertEqual(s, 200); self.assertEqual(list(j["status"]), [self.DEVS[0]["id"]]); self.assertEqual(len(self.calls), n + 1)

    def test_permissions_and_unknown_id(self):
        self.assertEqual(self.srv.call("GET", "/api/status")[0], 401)
        self.assertEqual(self.srv.call("GET", "/api/status", token=self.none)[0], 401)
        self.assertEqual(self.srv.call("GET", "/api/status?id=nope", token=self.ro)[0], 404)


class WanTraceAndIps(unittest.TestCase):
    def test_trace_destination_is_always_an_ip(self):
        self.assertEqual(wan.trace_dest({"targets": [{"host": "one.example"}, {"host": "1.1.1.1"}]}), "1.1.1.1")
        o = wan.socket.gethostbyname
        try:
            wan.socket.gethostbyname = lambda h: "192.0.2.5"
            self.assertEqual(wan.trace_dest({"targets": [{"host": "one.example"}]}), "192.0.2.5")
            wan.socket.gethostbyname = lambda h: "not-an-ip"
            self.assertIsNone(wan.trace_dest({"targets": [{"host": "one.example"}]}))
        finally: wan.socket.gethostbyname = o

    def test_traceroute_is_stored_cleaned_and_capped(self):
        start = int(time.time()) + 7_000_000
        class R: stdout = " 1  192.0.2.1  1 ms\x1b[31m\n" + "x" * 5000
        o = (wan.shutil.which, wan.subprocess.run); seen = []
        wan.shutil.which = lambda n: "/usr/bin/traceroute"
        wan.subprocess.run = lambda cmd, **kw: (seen.append(cmd), R)[1]
        try: wan.run_trace(start, {"targets": [{"host": "1.1.1.1"}]})
        finally: wan.shutil.which, wan.subprocess.run = o
        self.assertEqual(seen[0][-1], "1.1.1.1"); self.assertEqual(seen[0][0], "/usr/bin/traceroute")
        tr = wan.get_trace(start)
        self.assertEqual(tr["dest"], "1.1.1.1"); self.assertNotIn("\x1b", tr["text"]); self.assertLessEqual(len(tr["text"]), wan.TRACE_MAX)
        wan._db("INSERT OR REPLACE INTO wan_outages (start,end,scope) VALUES (?,?,?)", (start, start + 5, "wan"))
        try: self.assertTrue(next(x for x in wan.recent_outages(500) if x["start"] == start)["trace"])
        finally:
            wan._db("DELETE FROM wan_outages WHERE start = ?", (start,)); wan._db("DELETE FROM wan_traces WHERE start = ?", (start,))

    def test_without_the_program_nothing_is_stored(self):
        start = int(time.time()) + 7_000_001
        o = wan.shutil.which; wan.shutil.which = lambda n: None
        try: wan.run_trace(start, {"targets": [{"host": "1.1.1.1"}]})
        finally: wan.shutil.which = o
        self.assertIsNone(wan.get_trace(start))

    def test_ip_change_is_recorded(self):
        o = (wan.fetch_public_ip, wan.S.ip, wan.S.ip_changed, wan.S.ip_prev, wan.auth.write_json)
        wan._db("DELETE FROM wan_ips")
        wan.auth.write_json = lambda *a, **k: None
        try:
            wan.S.ip = "198.51.100.1"
            wan.fetch_public_ip = lambda url: "198.51.100.2"
            wan.check_ip({"ip_url": "https://x"})
        finally: wan.fetch_public_ip, wan.S.ip, wan.S.ip_changed, wan.S.ip_prev, wan.auth.write_json = o
        l = wan.recent_ips()
        self.assertEqual((l[0]["ip"], l[0]["prev"]), ("198.51.100.2", "198.51.100.1"))
        wan._db("DELETE FROM wan_ips")

    def test_history_is_seeded_with_the_known_ip(self):
        wan._db("DELETE FROM wan_ips"); o = (wan.S.ip, wan.S.ip_changed, wan.S.ip_prev, wan.auth.read_json)
        wan.auth.read_json = lambda *a, **k: {"ip": "198.51.100.9", "changed": 1700000000, "prev": "198.51.100.8"}
        try: wan.load_history()
        finally: wan.S.ip, wan.S.ip_changed, wan.S.ip_prev, wan.auth.read_json = o
        self.assertEqual(wan.recent_ips(), [{"ts": 1700000000, "ip": "198.51.100.9", "prev": "198.51.100.8"}])
        wan._db("DELETE FROM wan_ips")

    def test_earlier_ip_changes_are_recovered_from_the_events(self):
        wan._db("DELETE FROM wan_ips"); o = wan.auth.read_events
        ev = [{"t": 1700000300, "m": "wan", "k": "wan_ipc", "p": {"ip": "198.51.100.3", "prev": "198.51.100.2"}},
              {"t": 1700000100, "m": "wan", "k": "wan_ipc", "p": {"ip": "198.51.100.2", "prev": "198.51.100.1"}},
              {"t": 1700000200, "m": "wan", "k": "wan_down_wan", "p": {}},                       # another event: ignored
              {"t": 1700000400, "m": "wan", "k": "wan_ipc", "p": {"ip": "not-an-ip", "prev": "x"}}]   # junk: ignored
        wan.auth.read_events = lambda mods, limit=100: ev
        try:
            self.assertEqual(wan.backfill_ips(), 2); self.assertEqual(wan.backfill_ips(), 0)          # twice: no duplicates
        finally: wan.auth.read_events = o
        self.assertEqual([(x["ip"], x["prev"]) for x in wan.recent_ips()],
                         [("198.51.100.3", "198.51.100.2"), ("198.51.100.2", "198.51.100.1")])
        wan._db("DELETE FROM wan_ips")

    def test_wan_reads_only_its_own_events(self):
        authrpc = support.load("auth/authrpc.py"); asked = []
        class FA:
            def read_events(self, mods, limit): asked.append((mods, limit)); return [{"m": "wan"}]
        svc = authrpc.Service(FA(), identify=lambda uid: "wan")
        self.assertEqual(svc.handle("wan", {"op": "events", "modules": ["wol", "auth"], "limit": 999})["events"], [{"m": "wan"}])
        self.assertEqual(asked, [(["wan"], 300)])
        self.assertEqual(svc.handle("wol", {"op": "events"}), {"error": "forbidden"})

    def test_trace_endpoint(self):
        srv = support.Server(wan.H); tok = support.make_user("wtr", READONLY)
        try:
            self.assertEqual(srv.call("GET", "/api/wan/trace?start=1")[0], 401)
            self.assertEqual(srv.call("GET", "/api/wan/trace?start=abc", token=tok)[0], 400)
            self.assertEqual(srv.call("GET", "/api/wan/trace?start=1", token=tok)[0], 404)
        finally: srv.close()


class FakeDns:
    """Servidor DNS UDP en loopback que contesta A 192.0.2.7."""
    def __init__(self, ip="192.0.2.7", rcode=0):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); self.s.bind(("127.0.0.1", 0)); self.port = self.s.getsockname()[1]
        self.ip, self.rcode = ip, rcode
        threading.Thread(target=self.run, daemon=True).start()
    def run(self):
        while True:
            try: d, a = self.s.recvfrom(512)
            except OSError: return
            q = d[12:]
            r = d[:2] + struct.pack(">HHHHH", 0x8180 | self.rcode, 1, 1, 0, 0) + q + b"\xc0\x0c" + struct.pack(">HHIH", 1, 1, 60, 4) + bytes(map(int, self.ip.split(".")))
            try: self.s.sendto(r, a)
            except OSError: return
    def close(self): self.s.close()


class DnsClient(unittest.TestCase):
    def test_names(self):
        for ok in ("example.com", "a-b.example.cl.", "x_y.test"): self.assertTrue(dnsq.valid_name(ok), ok)
        for bad in ("", "a b", "-x.com", "x" * 64 + ".com", "a..b", "a;b.com", "http://x", "$(id).com", "é.com"): self.assertFalse(dnsq.valid_name(bad), bad)

    def test_upstream_text(self):
        self.assertEqual(dnsq.split_upstream("1.1.1.1"), ("1.1.1.1", 53))
        self.assertEqual(dnsq.split_upstream("127.0.0.1#5335"), ("127.0.0.1", 5335))
        self.assertEqual(dnsq.split_upstream("[2606:4700::1111]:853"), ("2606:4700::1111", 853))
        self.assertEqual(dnsq.split_upstream("8.8.8.8", 5353), ("8.8.8.8", 5353))
        for bad in ("https://dns.google/dns-query", "tls://1.1.1.1", "dns.google", "1.1.1.1:99999", ""): self.assertIsNone(dnsq.split_upstream(bad), bad)

    def test_query_round_trip_and_failures(self):
        f = FakeDns()
        try:
            r = dnsq.query("127.0.0.1", f.port, "example.com"); self.assertTrue(r["ok"]); self.assertEqual(r["answers"], [{"type": "A", "value": "192.0.2.7"}])
        finally: f.close()
        self.assertFalse(dnsq.query("127.0.0.1", f.port, "example.com", timeout=0.3)["ok"])
        self.assertFalse(dnsq.query("not-an-ip", 53, "example.com")["ok"])

    def test_garbage_packets_are_rejected(self):
        for raw in (b"", b"\x00" * 5, b"\x12\x34" + b"\xff" * 30):
            with self.assertRaises(ValueError): dnsq.parse_response(raw, 0x1234)


class DnsFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dns.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls._ep, dns.ensure_poller = dns.ensure_poller, lambda n: None
        cls.admin, cls.exe, cls.ro = support.make_user("fadm", {**ADMIN}), support.make_user("fexe", {**READONLY, "dns": "execute"}), support.make_user("fro", READONLY)
        cls.srv = support.Server(dns.H)
    @classmethod
    def tearDownClass(cls): dns.ensure_poller = cls._ep; cls.srv.close()
    def setUp(self): dns.save_servers([]); dns._cache.clear()

    def test_probe_marks_each_upstream_and_raises_alerts(self):
        asked = []
        o = dnsq.query
        dnsq.query = lambda h, p, n, t="A", timeout=2.0: (asked.append((h, p)), {"ok": h == "192.0.2.53", "ms": 4.2, "error": None if h == "192.0.2.53" else "timeout"})[1]
        try:
            snap = {"upstreams": [{"name": "good", "ip": "192.0.2.53", "port": 53}, {"name": "bad", "ip": "192.0.2.54", "port": 5353},
                                  {"name": "https://dns.example/q", "ip": "https://dns.example/q", "port": None}]}
            st = {}
            dns.probe_upstreams(snap, st)
            self.assertTrue(snap["upstreams"][0]["probe"]["ok"]); self.assertFalse(snap["upstreams"][1]["probe"]["ok"])
            self.assertNotIn("probe", snap["upstreams"][2])                          # DoH cannot be probed
            self.assertIn(("192.0.2.54", 5353), asked)
            n = len(asked); dns.probe_upstreams(snap, st); self.assertEqual(len(asked), n)    # throttled
            al = [a for a in dns.compute_alerts({"blocking": "enabled", "upstreams": snap["upstreams"]}) if a["type"] == "upstream_down"]
            self.assertEqual((al[0]["lv"], al[0]["value"]), ("warn", "bad"))
            for u in snap["upstreams"]: u["probe"] = {"ok": False}
            al = [a for a in dns.compute_alerts({"blocking": "enabled", "upstreams": snap["upstreams"][:2]}) if a["type"] == "upstream_down"]
            self.assertEqual(al[0]["lv"], "crit")
        finally: dnsq.query = o

    def test_probe_ports_and_same_name_upstreams(self):
        asked = []; o = dnsq.query
        dnsq.query = lambda h, p, *a, **k: (asked.append((h, p)), {"ok": p == 5353, "ms": 1})[1]
        try:
            snap = {"upstreams": [{"name": "same", "ip": "192.0.2.60", "port": 5353}, {"name": "same", "ip": "192.0.2.60", "port": 53},
                                  {"name": "ssh", "ip": "192.0.2.61", "port": 22}]}
            dns.probe_upstreams(snap, {})
        finally: dnsq.query = o
        self.assertEqual(sorted(asked), [("192.0.2.60", 53), ("192.0.2.60", 5353)])           # port 22 is never probed
        self.assertEqual([u.get("probe", {}).get("ok") for u in snap["upstreams"]], [True, False, None])   # same name, own result

    def test_probe_never_targets_this_machine(self):
        asked = []; o = (dnsq.query, dns.auth.valid_target)
        dnsq.query = lambda h, p, *a, **k: (asked.append(h), {"ok": True, "ms": 1})[1]
        dns.auth.valid_target = support.real_valid_target
        try:
            dns.probe_upstreams({"upstreams": [{"name": "l", "ip": "127.0.0.1", "port": 5335}, {"name": "ll", "ip": "169.254.1.1", "port": 53}]}, {})
        finally: dnsq.query, dns.auth.valid_target = o
        self.assertEqual(asked, [])

    def _server(self):
        s, j = self.srv.call("POST", "/api/dns", {"name": "Main", "url": "192.0.2.9", "type": "pihole", "password": "x"}, token=self.admin)
        self.assertEqual(s, 201, j); return j["server"]["id"]

    def test_resolve_compares_with_the_outside_and_flags_blocking(self):
        sid = self._server(); o = dnsq.query
        def fake(h, p, name, t="A", timeout=2.0):
            if h == dns.COMPARE_DNS: return {"ok": True, "ms": 9, "rcode": 0, "answers": [{"type": "A", "value": "93.184.216.34"}]}
            return {"ok": True, "ms": 2, "rcode": 0, "answers": [{"type": "A", "value": "0.0.0.0"}]}
        dnsq.query = fake
        try:
            s, j = self.srv.call("POST", f"/api/dns/{sid}/resolve", {"name": "ads.example.com"}, token=self.exe)
            self.assertEqual(s, 200, j); self.assertEqual(j["verdict"], "blocked"); self.assertEqual(j["server"]["addr"], "192.0.2.9")
            dnsq.query = lambda h, p, n, t="A", timeout=2.0: {"ok": True, "ms": 3, "rcode": 0, "answers": [{"type": "A", "value": "93.184.216.34"}]}
            self.assertEqual(self.srv.call("POST", f"/api/dns/{sid}/resolve", {"name": "example.com", "type": "AAAA"}, token=self.admin)[1]["verdict"], "ok")
            dnsq.query = lambda h, p, n, t="A", timeout=2.0: {"ok": False, "error": "timeout"} if h == "192.0.2.9" else {"ok": True, "ms": 1, "rcode": 0, "answers": []}
            self.assertEqual(self.srv.call("POST", f"/api/dns/{sid}/resolve", {"name": "example.com"}, token=self.exe)[1]["verdict"], "failed")
        finally: dnsq.query = o

    def test_resolve_permissions_and_input(self):
        sid = self._server(); c = self.srv.call; path = f"/api/dns/{sid}/resolve"
        self.assertEqual(c("POST", path, {"name": "example.com"})[0], 401)
        self.assertEqual(c("POST", path, {"name": "example.com"}, token=self.ro)[0], 403)
        for bad in ({"name": "a b"}, {"name": "-x.com"}, {"name": ""}, {"name": "example.com", "type": "TXT"}, {"name": ["x"]}):
            self.assertEqual(c("POST", path, bad, token=self.exe)[0], 400, bad)
        self.assertEqual(c("POST", "/api/dns/zzz/resolve", {"name": "example.com"}, token=self.exe)[0], 404)


if __name__ == "__main__":
    unittest.main()
