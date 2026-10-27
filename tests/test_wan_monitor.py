"""WAN Monitor: validación, sondas (ping simulado y TCP real), cortes, IP pública, test de velocidad contra un servidor local, permisos y alertas."""
import http.client, json, os, socket, stat, sys, tempfile, textwrap, threading, time, unittest
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from tests import support
from tests.support import ADMIN, READONLY, NONE

m = support.load("wan-monitor/server.py")

# ── «ping» simulado: imprime el formato real de iputils; la variable FAKE_PING_DOWN lista los hosts que no responden ──
FAKE_PING = textwrap.dedent('''\
    #!%(py)s
    import os, sys
    host = sys.argv[-1]
    down = os.environ.get("FAKE_PING_DOWN", "").split(",")
    if host in down or "*" in down:
        print("--- %%s ping statistics ---" %% host); print("3 packets transmitted, 0 received, 100%% packet loss, time 2040ms"); sys.exit(1)
    lossy = host in os.environ.get("FAKE_PING_LOSSY", "").split(",")
    print("--- %%s ping statistics ---" %% host)
    print("3 packets transmitted, %%d received, %%s packet loss, time 2003ms" %% ((2, "33.3%%") if lossy else (3, "0%%")))
    print("rtt min/avg/max/mdev = 9.100/%%s/10.900/0.700 ms" %% ("20.250" if host == "8.8.8.8" else "10.000"))
''')

def fake_ping_dir(tmp):
    d = Path(tmp, "bin"); d.mkdir(exist_ok=True)
    p = d / "ping"; p.write_text(FAKE_PING % {"py": sys.executable}); p.chmod(0o755)
    return str(d)

class WithFakePing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(); self.old_path = os.environ["PATH"]
        os.environ["PATH"] = fake_ping_dir(self.tmp) + os.pathsep + self.old_path
        for k in ("FAKE_PING_DOWN", "FAKE_PING_LOSSY"): os.environ.pop(k, None)
    def tearDown(self):
        os.environ["PATH"] = self.old_path
        for k in ("FAKE_PING_DOWN", "FAKE_PING_LOSSY"): os.environ.pop(k, None)


class Validate(unittest.TestCase):
    def test_defaults_are_valid(self):
        c = m.validate({}); self.assertEqual(len(c["targets"]), 3); self.assertEqual((c["interval"], c["gateway"]), (30, "auto"))
        self.assertTrue(c["speed"]["enabled"]); self.assertEqual(c["speed"]["every_hours"], 12)

    def test_rules(self):
        base = m.validate({})
        self.assertEqual(m.validate({"interval": 60, "speed": {"seconds": 5}}, base)["speed"]["seconds"], 5)
        self.assertEqual(m.validate({"targets": [{"host": "example.com", "kind": "tcp"}]}, base)["targets"], [{"host": "example.com", "kind": "tcp", "port": 443}])
        for bad in ({"targets": []}, {"targets": [{"host": "-x", "kind": "ping"}]}, {"targets": [{"host": "a", "kind": "udp"}]},
                    {"targets": [{"host": "1.1.1.1", "kind": "ping"}, {"host": "1.1.1.1", "kind": "ping"}]},
                    {"targets": [{"host": "a", "kind": "tcp", "port": 0}]}, {"targets": [{"host": "h"}] * 7},
                    {"interval": 5}, {"interval": "x"}, {"gateway": "router"}, {"dns_name": "a b"}, {"ip_url": "http://x.example"},
                    {"ip_url": "https://u:p@x.example"}, {"speed": {"every_hours": 9999}}, {"speed": {"streams": 0}}, {"speed": {"down_url": "http://x.example"}}):
            with self.subTest(bad=bad), self.assertRaises(ValueError): m.validate(bad, base)
        self.assertEqual(m.validate({"ip_url": "", "dns_name": "", "gateway": ""}, base)["ip_url"], "")

    def test_default_gateway_parser(self):
        tmp = Path(tempfile.mkdtemp(), "route")
        tmp.write_text("Iface\tDestination\tGateway\tFlags\tRefCnt\tUse\tMetric\tMask\n"
                       "eth0\t00000000\t0100A8C0\t0003\t0\t0\t100\t00000000\n" "eth0\t0000A8C0\t00000000\t0001\t0\t0\t100\t00FFFFFF\n")
        self.assertEqual(m.default_gateway(str(tmp)), "192.168.0.1")
        tmp.write_text("Iface\tDestination\tGateway\tFlags\n" "eth0\t0000A8C0\t00000000\t0001\n"); self.assertIsNone(m.default_gateway(str(tmp)))
        self.assertIsNone(m.default_gateway("/nonexistent/route"))


class Probes(WithFakePing):
    def test_ping_parses_iputils_output(self):
        r = m.ping("1.1.1.1"); self.assertEqual((r["sent"], r["recv"], r["loss"], r["rtt"], r["jitter"]), (3, 3, 0.0, 10.0, 0.7))
        os.environ["FAKE_PING_DOWN"] = "1.1.1.1"; r = m.ping("1.1.1.1"); self.assertEqual((r["recv"], r["loss"], r["rtt"]), (0, 100.0, None))
        os.environ["FAKE_PING_LOSSY"] = "9.9.9.9"; r = m.ping("9.9.9.9"); self.assertEqual((r["recv"], r["loss"]), (2, 33.3))

    def test_tcp_probe_against_a_real_listener(self):
        s = socket.socket(); s.bind(("127.0.0.1", 0)); s.listen(8); port = s.getsockname()[1]
        try:
            r = m.tcp_probe("127.0.0.1", port); self.assertEqual((r["recv"], r["loss"]), (3, 0.0)); self.assertIsNotNone(r["rtt"])
        finally: s.close()
        r = m.tcp_probe("127.0.0.1", port, count=2, timeout=1); self.assertEqual((r["recv"], r["rtt"]), (0, None))

    def test_round_up_down_and_gateway(self):
        cfg = m.validate({"dns_name": "localhost"})
        r = m.probe_round(cfg, "192.168.0.1")
        self.assertTrue(r["up"]); self.assertEqual(len(r["targets"]), 3); self.assertEqual(r["gateway"]["host"], "192.168.0.1"); self.assertEqual(r["loss"], 0.0)
        self.assertEqual(r["rtt"], round((10 + 20.25 + 10) / 3, 2)); self.assertIsNotNone(r["dns"]); self.assertEqual(r["gw"], 10.0)
        os.environ["FAKE_PING_DOWN"] = "1.1.1.1,8.8.8.8,9.9.9.9"
        r = m.probe_round(cfg, "192.168.0.1"); self.assertFalse(r["up"]); self.assertEqual((r["rtt"], r["loss"]), (None, 100.0)); self.assertTrue(r["gateway"]["ok"])
        os.environ["FAKE_PING_DOWN"] = "*"; r = m.probe_round(cfg, "192.168.0.1"); self.assertFalse(r["gateway"]["ok"])
        os.environ["FAKE_PING_DOWN"] = "1.1.1.1"; r = m.probe_round(cfg, None); self.assertTrue(r["up"]); self.assertIsNone(r["gateway"]); self.assertEqual(r["loss"], round(100 / 3, 2))


class Outages(unittest.TestCase):
    def setUp(self):
        self.s0 = (m.S.fails, m.S.down_since, m.S.scope); m.S.fails, m.S.down_since, m.S.scope = 0, None, None
        c = support.auth.metrics_conn(); c.execute("DELETE FROM wan_outages"); c.commit(); c.close()
    def tearDown(self): m.S.fails, m.S.down_since, m.S.scope = self.s0

    @staticmethod
    def rnd(ts, up, gw_ok=True): return {"ts": ts, "up": up, "gateway": {"ok": gw_ok, "host": "g"}}

    def test_outage_needs_two_failed_rounds_and_records_duration(self):
        t = int(time.time()) - 500
        m.track_outage(self.rnd(t, False), t); self.assertIsNone(m.S.down_since)                    # one failure is not an outage
        m.track_outage(self.rnd(t + 30, True), t + 30); self.assertEqual(m.S.fails, 0)
        m.track_outage(self.rnd(t + 60, False), t + 60); m.track_outage(self.rnd(t + 90, False), t + 60)
        self.assertEqual((m.S.down_since, m.S.scope), (t + 60, "internet"))
        self.assertEqual([(o["start"], o["end"]) for o in m.recent_outages()], [(t + 60, None)])
        m.track_outage(self.rnd(t + 200, True), t + 200)
        self.assertIsNone(m.S.down_since); self.assertEqual([(o["start"], o["end"]) for o in m.recent_outages()], [(t + 60, t + 200)])

    def test_scope_is_lan_when_gateway_fails_too(self):
        t = int(time.time()); m.track_outage(self.rnd(t, False, False), t); m.track_outage(self.rnd(t + 30, False, False), t)
        self.assertEqual(m.S.scope, "lan"); self.assertEqual(m.recent_outages()[0]["scope"], "lan")

    def test_alerts(self):
        base = {"down_since": None, "loss": 0, "rtt": 10, "dns": 20, "dns_fail": False, "ip_changed": None}
        self.assertEqual(m.compute_alerts(base), [])
        self.assertEqual([a["type"] for a in m.compute_alerts({**base, "down_since": 5, "scope": "lan"})], ["down_lan"])
        self.assertEqual([a["type"] for a in m.compute_alerts({**base, "down_since": 5, "scope": "internet"})], ["down_internet"])
        self.assertEqual([a["type"] for a in m.compute_alerts({**base, "loss": 6, "rtt": 200, "dns": 900})], ["loss", "latency", "dns_slow"])
        self.assertEqual([a["type"] for a in m.compute_alerts({**base, "dns": None, "dns_fail": True})], ["dns_fail"])
        self.assertEqual(m.compute_alerts({**base, "ip_changed": time.time() - 60, "public_ip": "198.51.100.1"})[0]["type"], "ip_changed")
        self.assertEqual(m.compute_alerts({**base, "ip_changed": time.time() - 7200}), [])

    def test_uptime_and_history_range(self):
        now = int(time.time()); c = support.auth.metrics_conn()
        try:
            c.execute("DELETE FROM wan_samples")
            for i in range(10): c.execute("INSERT INTO wan_samples VALUES (?,?,?,?,?,?,?)", (now - 30 * i, 0 if i < 2 else 1, 12.0, 0.0, 1.0, 1.0, 20.0))
            c.commit()
        finally: c.close()
        self.assertEqual(m.uptime()["24h"], 80.0)
        h = m.history_range("1h"); self.assertEqual(len(h), 10); self.assertEqual(h[-1]["up"], 0)
        c = support.auth.metrics_conn(); c.execute("DELETE FROM wan_samples"); c.commit(); c.close()
        self.assertIsNone(m.uptime()["24h"])


class PublicIp(unittest.TestCase):
    def test_fetch_and_change_events(self):
        class Hd(BaseHTTPRequestHandler):
            ip = b"198.51.100.7\n"
            def log_message(self, *a): pass
            def do_GET(self):
                self.send_response(200); self.send_header("Content-Length", str(len(Hd.ip))); self.end_headers(); self.wfile.write(Hd.ip)
        srv = ThreadingHTTPServer(("127.0.0.1", 0), Hd); threading.Thread(target=srv.serve_forever, daemon=True).start()
        orig = m._conn; m._conn = lambda url, timeout=10: (http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=timeout), urlparse(url).path or "/")
        old_state, old_file = (m.S.ip, m.S.ip_changed), m.STATE_FILE; m.STATE_FILE = Path(tempfile.mkdtemp(), "state.json")
        try:
            self.assertEqual(m.fetch_public_ip("https://x.example/"), "198.51.100.7")
            Hd.ip = b"<html>nope</html>"; self.assertIsNone(m.fetch_public_ip("https://x.example/"))
            Hd.ip = b"198.51.100.7"; m.S.ip, m.S.ip_changed = None, None
            m.check_ip({"ip_url": "https://x.example/"}); self.assertEqual((m.S.ip, m.S.ip_changed), ("198.51.100.7", None))          # first value: no «change»
            Hd.ip = b"198.51.100.9"; m.check_ip({"ip_url": "https://x.example/"}); self.assertEqual(m.S.ip, "198.51.100.9"); self.assertIsNotNone(m.S.ip_changed)
            self.assertEqual(json.loads(m.STATE_FILE.read_text())["ip"], "198.51.100.9")
        finally:
            m._conn = orig; m.STATE_FILE = old_file; m.S.ip, m.S.ip_changed = old_state; srv.shutdown(); srv.server_close()


class Speed(unittest.TestCase):
    """Un servidor compatible con Cloudflare (/__down?bytes=N y /__up) sobre HTTP local; _conn se redirige a él."""
    @classmethod
    def setUpClass(cls):
        class Hd(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"
            def log_message(self, *a): pass
            def do_GET(self):
                n = int(parse_qs(urlparse(self.path).query).get("bytes", ["0"])[0]); n = min(n, 30_000_000)
                self.send_response(200); self.send_header("Content-Length", str(n)); self.end_headers()
                sent = 0; chunk = bytes(65536)
                try:
                    while sent < n: self.wfile.write(chunk[:min(65536, n - sent)]); sent += 65536
                except OSError: pass
            def do_POST(self):
                n = int(self.headers.get("Content-Length", 0)); left = n
                while left > 0: left -= len(self.rfile.read(min(65536, left)))
                self.send_response(200); self.send_header("Content-Length", "0"); self.end_headers()
        class Quiet(ThreadingHTTPServer):
            def handle_error(self, *a): pass
        cls.srv = Quiet(("127.0.0.1", 0), Hd); cls.srv.daemon_threads = True; threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.orig = m._conn; port = cls.srv.server_address[1]
        m._conn = lambda url, timeout=10: (http.client.HTTPConnection("127.0.0.1", port, timeout=timeout), urlparse(url).path or "/")
    @classmethod
    def tearDownClass(cls): m._conn = cls.orig; cls.srv.shutdown(); cls.srv.server_close()

    def cfg(self, **sp): return m.validate({"speed": {"seconds": 3, "streams": 2, **sp}})

    def test_download_upload_and_ping(self):
        r = m.run_speedtest(self.cfg())
        self.assertIsNone(r["error"], r); self.assertGreater(r["down"], 1); self.assertGreater(r["up"], 1); self.assertIsNotNone(r["ping"])
        self.assertEqual(r["server"], "speed.cloudflare.com")

    def test_upload_can_be_disabled(self):
        r = m.run_speedtest(self.cfg(upload=False)); self.assertIsNone(r["up"]); self.assertGreater(r["down"], 1)

    def test_unreachable_server_reports_an_error(self):
        orig = m._conn; m._conn = lambda url, timeout=10: (http.client.HTTPConnection("127.0.0.1", 9, timeout=1), "/")
        try:
            r = m.run_speedtest(self.cfg()); self.assertIsNotNone(r["error"]); self.assertIsNone(r["down"])
        finally: m._conn = orig

    def test_schedule(self):
        c = m.validate({}); old = (m.S.speed_last, m._STARTED)
        try:
            m.S.speed_last = 0; m._STARTED = 1000.0; self.assertEqual(m.next_speedtest(c), 1300.0)
            m.S.speed_last = 5000; self.assertEqual(m.next_speedtest(c), 5000 + 12 * 3600)
            self.assertIsNone(m.next_speedtest(m.validate({"speed": {"every_hours": 0}}, c))); self.assertIsNone(m.next_speedtest(m.validate({"speed": {"enabled": False}}, c)))
        finally: m.S.speed_last, m._STARTED = old

    def test_only_one_test_at_a_time_and_probes_pause(self):
        m.S.speed_running = False
        self.assertTrue(m.start_speedtest()); self.assertFalse(m.start_speedtest())
        for _ in range(100):
            if not m.S.speed_running: break
            time.sleep(0.2)
        self.assertFalse(m.S.speed_running)


class Http(WithFakePing):
    @classmethod
    def setUpClass(cls):
        m.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.admin, cls.exe, cls.ro, cls.none = (support.make_user("wadm", {**ADMIN}), support.make_user("wexe", {**READONLY, "wan": "execute"}),
                                                support.make_user("wro", READONLY), support.make_user("wnone", NONE))
        cls.srv = support.Server(m.H)
    @classmethod
    def tearDownClass(cls): cls.srv.close()
    def setUp(self):
        super().setUp(); m.save_config(m.validate({})); self._started = []; self._ss, m.start_speedtest = m.start_speedtest, lambda by_schedule=False: self._started.append(1) or True
        m.S.speed_started = 0
    def tearDown(self): m.start_speedtest = self._ss; super().tearDown()

    def test_permissions(self):
        c = self.srv.call
        self.assertEqual(c("GET", "/api/wan")[0], 401); self.assertEqual(c("GET", "/api/wan", token=self.none)[0], 401); self.assertEqual(c("GET", "/api/wan", token=self.ro)[0], 200)
        self.assertEqual(c("GET", "/api/wan/history", token=self.ro)[0], 200)
        for tok in (self.ro, self.exe): self.assertEqual(c("POST", "/api/wan/config", {"interval": 60}, token=tok)[0], 403)
        self.assertEqual(c("POST", "/api/wan/config", {"interval": 60})[0], 401)
        self.assertEqual(c("POST", "/api/wan/speedtest", {}, token=self.ro)[0], 403); self.assertEqual(c("POST", "/api/wan/speedtest", {})[0], 401)

    def test_status_payload(self):
        cfg = m.load_config(); r = m.probe_round(m.validate({"dns_name": ""}), "192.168.0.1"); m.S.last, m.S.gw = r, "192.168.0.1"
        s, j = self.srv.call("GET", "/api/wan", token=self.ro)
        self.assertEqual(s, 200); self.assertTrue(j["snap"]["up"]); self.assertEqual(j["snap"]["gateway_ip"], "192.168.0.1"); self.assertIn("config", j)
        self.assertIn("uptime", j); self.assertIn("speed", j); self.assertIn("outages", j); self.assertFalse(j["speed_running"])
        s, j = self.srv.call("GET", "/api/wan?hist=0", token=self.ro); self.assertEqual(j["history"], [])

    def test_config_update_and_validation(self):
        c = self.srv.call
        s, j = c("POST", "/api/wan/config", {"interval": 45, "speed": {"every_hours": 6}}, token=self.admin); self.assertEqual(s, 200, j)
        self.assertEqual((m.load_config()["interval"], m.load_config()["speed"]["every_hours"]), (45, 6)); self.assertEqual(j["config"]["speed"]["seconds"], 8)
        for bad in ({"interval": 1}, {"targets": []}, {"speed": {"down_url": "http://x"}}): self.assertEqual(c("POST", "/api/wan/config", bad, token=self.admin)[0], 400)
        self.assertEqual(oct(stat.S_IMODE(os.stat(m.DATA_FILE).st_mode)), "0o600")

    def test_speedtest_endpoint(self):
        c = self.srv.call
        self.assertEqual(c("POST", "/api/wan/speedtest", {}, token=self.exe)[0], 202); self.assertEqual(self._started, [1])
        m.S.speed_started = time.time(); self.assertEqual(c("POST", "/api/wan/speedtest", {}, token=self.exe)[0], 429)

    def test_history_and_cross_site(self):
        self.assertEqual(self.srv.call("GET", "/api/wan/history?range=zz", token=self.ro)[0], 400)
        s, j = self.srv.call("POST", "/api/wan/config", {"interval": 60}, token=self.admin, headers={"Sec-Fetch-Site": "cross-site"}); self.assertEqual(s, 403)

    def test_probe_loop_end_to_end(self):
        os.environ["FAKE_PING_DOWN"] = ""; m.save_config(m.validate({"interval": 10, "dns_name": "", "ip_url": "", "gateway": ""}))
        m.S.last = None; t = threading.Thread(target=m.probe_loop, daemon=True); t.start()
        for _ in range(100):
            if m.S.last: break
            time.sleep(0.1)
        m._stop.set(); m.S.wake.set()
        try:
            self.assertTrue(m.S.last["up"]); self.assertGreaterEqual(len(m.S.history), 1)
            self.assertEqual(m.health_report(False)[0], 200)
        finally: m._stop.clear()

if __name__ == "__main__": unittest.main()
