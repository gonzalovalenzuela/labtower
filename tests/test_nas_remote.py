"""NAS Monitor: TrueNAS (JSON-RPC por WebSocket) y OpenMediaVault (rpc.php) con servidores simulados / with simulated servers."""
import base64, hashlib, json, os, shutil, socket, ssl, stat, struct, subprocess, tempfile, threading, unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from tests import support
from tests.support import ADMIN, READONLY

m = support.load("nas-monitor/server.py")
remote = m.remote
GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
_TMP = tempfile.mkdtemp(prefix="nas-remote-")

def make_cert(name):
    crt, key = os.path.join(_TMP, name + ".crt"), os.path.join(_TMP, name + ".key")
    subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", crt, "-days", "2",
                    "-subj", "/CN=nas.example.lan"], check=True, capture_output=True)
    return crt, key

HAVE_OPENSSL = shutil.which("openssl") is not None
if HAVE_OPENSSL:
    CERT_A, CERT_B = make_cert("a"), make_cert("b")

def tls_ctx(cert):
    c = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); c.load_cert_chain(*cert); return c

# ── TrueNAS simulado: handshake WebSocket y JSON-RPC 2.0 / simulated TrueNAS: WebSocket handshake and JSON-RPC 2.0 ──
INFO = {"version": "TrueNAS-25.04.2", "hostname": "tn1", "uptime_seconds": 90000.5, "loadavg": [0.5, 0.4, 0.3], "physmem": 1000,
        "model": "Intel Xeon", "system_product": "TRUENAS-MINI-X", "system_serial": "SN1"}
POOLS = [{"name": "tank", "status": "ONLINE", "healthy": True, "size": 1000, "allocated": 400, "free": 600, "scan": {"state": "FINISHED"}},
         {"name": "bad", "status": "DEGRADED", "healthy": False, "size": 1000, "allocated": 900, "free": 100}]
DISKS = [{"name": "sda", "model": "WD40", "type": "HDD"}, {"name": "sdb", "model": "ST4", "type": "HDD"}]
ALERTS = [{"klass": "SMART", "level": "CRITICAL", "formatted": "Device: /dev/sdb, SMART failed", "dismissed": False},
          {"klass": "Old", "level": "INFO", "formatted": "old thing", "dismissed": True}]
EVENT = {"cpu": {"cpu": {"usage": 12.5, "user": 8, "system": 4, "idle": 87.5, "temp": 48}},
         "memory": {"physical_memory_total": 1000, "physical_memory_available": 250},
         "interfaces": {"eno1": {"received_bytes_rate": 1000, "sent_bytes_rate": 500, "speed": 1000, "received_bytes": 10, "sent_bytes": 5},
                        "docker0": {"received_bytes_rate": 9, "sent_bytes_rate": 9}},
         "disks": {"busy": 3.5, "read_bytes": 100, "write_bytes": 200}}

class TnMock:
    def __init__(self, cert, api_key="KEY", user="admin", event=EVENT, subscribe_error=False, big_frame=False):
        self.api_key, self.user, self.event, self.subscribe_error, self.big_frame = api_key, user, event, subscribe_error, big_frame
        self.log, self.sock, self.ctx = [], socket.socket(), tls_ctx(cert)
        self.sock.bind(("127.0.0.1", 0)); self.sock.listen(8); self.port = self.sock.getsockname()[1]
        self.alive = True
        threading.Thread(target=self._accept, daemon=True).start()

    def close(self):
        self.alive = False
        try: self.sock.close()
        except OSError: pass

    def _accept(self):
        while self.alive:
            try: c, _ = self.sock.accept()
            except OSError: return
            threading.Thread(target=self._serve, args=(c,), daemon=True).start()

    @staticmethod
    def _rd(s, n):
        b = b""
        while len(b) < n:
            x = s.recv(n - len(b))
            if not x: raise EOFError
            b += x
        return b

    def _frame(self, s):
        b0, b1 = self._rd(s, 2); ln = b1 & 0x7F
        if ln == 126: ln = struct.unpack(">H", self._rd(s, 2))[0]
        elif ln == 127: ln = struct.unpack(">Q", self._rd(s, 8))[0]
        mask = self._rd(s, 4); data = bytes(b ^ mask[i & 3] for i, b in enumerate(self._rd(s, ln)))
        return b0 & 0x0F, data

    @staticmethod
    def _send(s, obj, op=1):
        p = obj if isinstance(obj, bytes) else json.dumps(obj).encode(); n = len(p)
        h = bytes([0x80 | op]) + (bytes([n]) if n < 126 else bytes([126]) + struct.pack(">H", n) if n < 65536 else bytes([127]) + struct.pack(">Q", n))
        s.sendall(h + p)

    def _serve(self, raw):
        try:
            s = self.ctx.wrap_socket(raw, server_side=True)
        except (ssl.SSLError, OSError):
            raw.close(); return
        try:
            head = b""
            while b"\r\n\r\n" not in head: head += s.recv(4096)
            lines = head.decode().split("\r\n"); hdr = {l.split(":", 1)[0].lower(): l.split(":", 1)[1].strip() for l in lines[1:] if ":" in l}
            self.log.append(("GET", lines[0].split(" ")[1]))
            if lines[0].split(" ")[1] != "/api/current":
                s.sendall(b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"); return
            acc = base64.b64encode(hashlib.sha1((hdr["sec-websocket-key"] + GUID).encode()).digest()).decode()
            s.sendall(f"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: {acc}\r\n\r\n".encode())
            authed = False
            while True:
                op, data = self._frame(s)
                if op == 8: return
                req = json.loads(data); meth = req["method"]; self.log.append(meth)
                rid = req["id"]
                if meth == "auth.login_ex":
                    a = req["params"][0]
                    ok = a.get("mechanism") == "API_KEY_PLAIN" and a.get("api_key") == self.api_key and a.get("username") == self.user
                    authed = ok
                    self._send(s, {"jsonrpc": "2.0", "id": rid, "result": {"response_type": "SUCCESS" if ok else "AUTH_ERR"}}); continue
                if not authed:
                    self._send(s, {"jsonrpc": "2.0", "id": rid, "error": {"code": -32001, "message": "ENOTAUTHENTICATED"}}); continue
                if meth == "core.subscribe":
                    if self.subscribe_error:
                        self._send(s, {"jsonrpc": "2.0", "id": rid, "error": {"code": 22, "message": "Invalid", "data": {"reason": "no such event"}}}); continue
                    self._send(s, {"jsonrpc": "2.0", "id": rid, "result": 1})
                    self._send(s, {"jsonrpc": "2.0", "method": "collection_update", "params": {"msg": "changed", "collection": "reporting.realtime", "fields": self.event}})
                    continue
                if self.big_frame and meth == "system.info":
                    s.sendall(bytes([0x81, 127]) + struct.pack(">Q", 100 << 20)); return
                res = {"system.info": INFO, "pool.query": POOLS, "disk.query": DISKS, "alert.list": ALERTS,
                       "disk.temperatures": {"sda": 35, "sdb": 61}}.get(meth)
                self._send(s, {"jsonrpc": "2.0", "id": rid, "result": res})
        except (EOFError, OSError, ssl.SSLError, ValueError):
            pass
        finally:
            try: s.close()
            except OSError: pass

# ── OpenMediaVault simulado / simulated OpenMediaVault ──
OMV = {
    ("System", "getInformation"): {"hostname": "omv1", "version": "7.4.17-1 (Sandworm)", "cpuModelName": "ARM", "uptime": 3600.5, "cpuUtilization": 23.4,
                                   "memTotal": 1000, "memUsed": 300, "memAvailable": 600, "loadAverage": {"1min": 0.1, "5min": 0.2, "15min": 0.3},
                                   "availablePkgUpdates": 3, "rebootRequired": True},
    ("DiskMgmt", "enumerateDevices"): [{"devicefile": "/dev/sda", "devicename": "sda", "model": "WD", "israid": False},
                                       {"devicefile": "/dev/md0", "devicename": "md0", "israid": True}],
    ("Smart", "getList"): {"total": 1, "data": [{"devicefile": "/dev/sda", "devicename": "sda", "model": "WD", "temperature": 34, "overallstatus": "BAD_SECTOR"}]},
    ("FileSystemMgmt", "enumerateFilesystems"): [{"uuid": "u1", "devicefile": "/dev/sda1", "label": "data", "type": "ext4", "mounted": True,
                                                  "size": "1000", "available": "250", "used": "750"},
                                                 {"uuid": "u2", "devicefile": "/dev/sda2", "label": "efi", "type": "vfat", "mounted": True, "size": "10", "available": "9"}],
    ("Network", "enumerateDevices"): [{"devicename": "eth0", "speed": 1000}, {"devicename": "lo"}],
}

class OmvMock:
    def __init__(self, cert=None, user="admin", password="pw", redirect=False, deep=False):
        self.deep = deep
        self.user, self.password, self.redirect, self.logins, self.valid, self.calls, self.cookies_seen = user, password, redirect, 0, set(), [], []
        mock = self
        class Hd(BaseHTTPRequestHandler):
            def log_message(self, *a): pass
            def _reply(self, code, obj, cookie=None):
                b = json.dumps(obj).encode(); self.send_response(code); self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(b)))
                if cookie: self.send_header("Set-Cookie", cookie + "; path=/; HttpOnly")
                self.end_headers(); self.wfile.write(b)
            def do_POST(self):
                if mock.redirect:
                    self.send_response(302); self.send_header("Location", "https://x/"); self.send_header("Content-Length", "0"); self.end_headers(); return
                req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if mock.deep:
                    b = b"[" * 200000 + b"]" * 200000; self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b); return
                svc, meth = req["service"], req["method"]; mock.calls.append((svc, meth))
                ck = self.headers.get("Cookie") or ""; mock.cookies_seen.append(ck)
                if (svc, meth) == ("Session", "login"):
                    p = req["params"]
                    if p.get("username") == mock.user and p.get("password") == mock.password:
                        mock.logins += 1; sid = f"S{mock.logins}"; mock.valid.add(sid)
                        return self._reply(200, {"response": {"authenticated": True, "username": mock.user, "permissions": {}, "sessionid": sid}, "error": None},
                                           f"PHPSESSID={sid}")
                    return self._reply(400, {"response": None, "error": {"code": 0, "message": "Incorrect username or password.", "trace": "SECRET TRACE"}})
                sid = ck.split("PHPSESSID=")[-1].split(";")[0] if "PHPSESSID=" in ck else ""
                if sid not in mock.valid:
                    return self._reply(401, {"response": None, "error": {"code": 5000, "message": "Session not authenticated.", "trace": "x"}})
                if (svc, meth) not in OMV:
                    return self._reply(500, {"response": None, "error": {"code": 1, "message": "Method not found.", "trace": "T"}})
                self._reply(200, {"response": OMV[(svc, meth)], "error": None})
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), Hd)
        if cert: self.srv.socket = tls_ctx(cert).wrap_socket(self.srv.socket, server_side=True)
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def close(self): self.srv.shutdown(); self.srv.server_close()

def tn_cfg(port, **kw):
    return m.validate({"type": "truenas", "name": "TN", "host": "127.0.0.1", "port": port, "user": "admin", "api_key": "KEY", "timeout": 5, **kw})

def omv_cfg(port, **kw):
    return m.validate({"type": "omv", "name": "OMV", "host": "127.0.0.1", "port": port, "user": "admin", "password": "pw", "timeout": 5, **kw})

@unittest.skipUnless(HAVE_OPENSSL, "openssl not installed")
class TrueNas(unittest.TestCase):
    def test_full_reading(self):
        srv = TnMock(CERT_A); self.addCleanup(srv.close)
        cfg = tn_cfg(srv.port); snap = m.collect(cfg, {})
        s = snap["system"]
        self.assertEqual((s["name"], s["model"], s["dsm"], s["serial"], s["uptime"], s["temp"]), ("tn1", "TRUENAS-MINI-X", "TrueNAS-25.04.2", "SN1", 90000.5, 48))
        self.assertEqual((snap["cpu"]["pct"], snap["cpu"]["load"]), (12.5, [0.5, 0.4, 0.3]))
        self.assertEqual((snap["mem"]["pct"], snap["mem"]["total"]), (75.0, 1000))
        self.assertEqual([(n["name"], n["rx"], n["tx"], n["speed"]) for n in snap["net"]], [("eno1", 8000, 4000, 1000)])
        self.assertEqual([(r["name"], r["status_text"], r["lv"], r["pct"]) for r in snap["raids"]], [("bad", "DEGRADED", "warn", 90.0), ("tank", "ONLINE", "ok", 40.0)])
        self.assertEqual([(d["name"], d["lv"], d["temp"]) for d in snap["disks"]], [("sda", "ok", 35.0), ("sdb", "crit", 61.0)])
        kinds = {(a["type"], a["lv"]) for a in snap["alerts"]}
        for want in [("raid", "warn"), ("vol_full", "warn"), ("disk", "crit"), ("remote", "crit")]: self.assertIn(want, kinds)
        self.assertEqual([a for a in snap["alerts"] if a["type"] == "remote"][0]["value"], "Device: /dev/sdb, SMART failed")     # the dismissed one is not listed
        self.assertEqual(snap["io"][0]["load"], 3.5)
        self.assertEqual(len(cfg["tls_pin"]), 64)                                       # the fingerprint was learned
        self.assertFalse(any(x in ("pool.create", "pool.delete") for x in srv.log if isinstance(x, str)))

    def test_only_read_methods_are_called(self):
        srv = TnMock(CERT_A); self.addCleanup(srv.close); m.collect(tn_cfg(srv.port), {})
        called = {x for x in srv.log if isinstance(x, str) and x != "GET"}
        self.assertEqual(called, {"auth.login_ex", "core.subscribe", "system.info", "pool.query", "disk.query", "alert.list", "disk.temperatures"})

    def test_wrong_key_and_user(self):
        srv = TnMock(CERT_A); self.addCleanup(srv.close)
        with self.assertRaisesRegex(remote.RemoteError, "Authentication failed"): m.collect(tn_cfg(srv.port, api_key="nope"), {})
        with self.assertRaisesRegex(remote.RemoteError, "Authentication failed"): m.collect(tn_cfg(srv.port, user="other"), {})

    def test_without_realtime_the_rest_still_works(self):
        srv = TnMock(CERT_A, subscribe_error=True); self.addCleanup(srv.close)
        snap = m.collect(tn_cfg(srv.port), {})
        self.assertIsNone(snap["cpu"]["pct"]); self.assertIsNone(snap["mem"]); self.assertEqual(len(snap["raids"]), 2)
        self.assertTrue(any("realtime" in w and "no such event" in w for w in snap["warnings"]))

    def test_pin_mismatch_stops_before_sending_the_key(self):
        a = TnMock(CERT_A); self.addCleanup(a.close)
        cfg = tn_cfg(a.port); m.collect(cfg, {}); pin = cfg["tls_pin"]
        b = TnMock(CERT_B); self.addCleanup(b.close)
        cfg2 = tn_cfg(b.port, tls_pin=pin); cfg2["tls_pin"] = pin
        with self.assertRaisesRegex(remote.RemoteError, "pinned fingerprint mismatch"): m.collect(cfg2, {})
        self.assertEqual([x for x in b.log if x != "GET"], [])                          # no API call (and no key) reached the impostor
        self.assertEqual(b.log, [])                                                      # not even the handshake

    def test_verify_tls_rejects_self_signed(self):
        srv = TnMock(CERT_A); self.addCleanup(srv.close)
        with self.assertRaisesRegex(remote.RemoteError, "TLS error"): m.collect(tn_cfg(srv.port, verify_tls=True), {})

    def test_oversized_frame_is_refused(self):
        srv = TnMock(CERT_A, big_frame=True); self.addCleanup(srv.close)
        with self.assertRaisesRegex(remote.RemoteError, "too large"): m.collect(tn_cfg(srv.port), {})

    def test_connection_refused_and_not_a_websocket(self):
        s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
        with self.assertRaises(remote.RemoteError): m.collect(tn_cfg(port), {})

    def test_connection_test(self):
        srv = TnMock(CERT_A); self.addCleanup(srv.close)
        r = m.test_connection(tn_cfg(srv.port))
        self.assertEqual((r["name"], r["model"], r["dsm"], r["kind"]), ("tn1", "TRUENAS-MINI-X", "TrueNAS-25.04.2", "truenas"))

@unittest.skipUnless(HAVE_OPENSSL, "openssl not installed")
class OpenMediaVault(unittest.TestCase):
    def test_full_reading_over_https(self):
        srv = OmvMock(CERT_A); self.addCleanup(srv.close)
        cfg = omv_cfg(srv.port); snap = m.collect(cfg, {})
        s = snap["system"]
        self.assertEqual((s["name"], s["model"], s["dsm"], s["uptime"], s["upgrade"]), ("omv1", "OpenMediaVault", "7.4.17-1 (Sandworm)", 3600.5, 1))
        self.assertEqual((snap["cpu"]["pct"], snap["cpu"]["load"]), (23.4, [0.1, 0.2, 0.3]))
        self.assertEqual((snap["mem"]["pct"], snap["mem"]["total"]), (40.0, 1000))
        self.assertEqual([(d["name"], d["lv"], d["status_text"], d["temp"]) for d in snap["disks"]], [("sda", "warn", "BAD_SECTOR", 34.0)])
        self.assertEqual([(r["name"], r["pct"], r["lv"]) for r in snap["raids"]], [("data", 75.0, "ok")])
        self.assertEqual([n["name"] for n in snap["net"]], ["eth0"])
        self.assertIn(("disk", "warn"), {(a["type"], a["lv"]) for a in snap["alerts"]})
        self.assertIn(("upgrade", "info"), {(a["type"], a["lv"]) for a in snap["alerts"]})
        self.assertEqual(len(cfg["tls_pin"]), 64)

    def test_plain_http_works_when_selected(self):
        srv = OmvMock(None); self.addCleanup(srv.close)
        snap = m.collect(omv_cfg(srv.port, https=False), {}); self.assertEqual(snap["system"]["name"], "omv1")

    def test_session_is_reused_and_renewed(self):
        srv = OmvMock(CERT_A); self.addCleanup(srv.close)
        cfg, prev = omv_cfg(srv.port), {}
        m.collect(cfg, prev); m.collect(cfg, prev)
        self.assertEqual(srv.logins, 1)                                                  # one login for two readings
        srv.valid.clear()                                                                # the session expires on the NAS
        m.collect(cfg, prev); self.assertEqual(srv.logins, 2)

    def test_session_is_dropped_when_the_target_changes(self):
        srv = OmvMock(CERT_A); self.addCleanup(srv.close)
        prev = {}; m.collect(omv_cfg(srv.port), prev)
        m.collect(omv_cfg(srv.port, user="admin", password="pw", timeout=6), prev); self.assertEqual(srv.logins, 1)
        srv.user = "other"; m.collect(omv_cfg(srv.port, user="other"), prev); self.assertEqual(srv.logins, 2)

    def test_wrong_password_hides_the_trace(self):
        srv = OmvMock(CERT_A); self.addCleanup(srv.close)
        with self.assertRaises(remote.RemoteError) as cm: m.collect(omv_cfg(srv.port, password="bad"), {})
        self.assertIn("Incorrect username or password", str(cm.exception)); self.assertNotIn("SECRET TRACE", str(cm.exception))

    def test_redirect_is_not_followed(self):
        srv = OmvMock(None, redirect=True); self.addCleanup(srv.close)
        with self.assertRaisesRegex(remote.RemoteError, "redirected"): m.collect(omv_cfg(srv.port, https=False), {})

    def test_pin_mismatch(self):
        a = OmvMock(CERT_A); self.addCleanup(a.close)
        cfg = omv_cfg(a.port); m.collect(cfg, {})
        b = OmvMock(CERT_B); self.addCleanup(b.close)
        cfg2 = omv_cfg(b.port); cfg2["tls_pin"] = cfg["tls_pin"]
        with self.assertRaisesRegex(remote.RemoteError, "pinned fingerprint mismatch"): m.collect(cfg2, {})
        self.assertEqual(b.calls, [])

    def test_missing_optional_services_give_warnings_not_errors(self):
        srv = OmvMock(CERT_A); self.addCleanup(srv.close)
        saved = OMV.pop(("Smart", "getList"))
        try:    snap = m.collect(omv_cfg(srv.port), {})
        finally: OMV[("Smart", "getList")] = saved
        self.assertTrue(any(w.startswith("smart:") for w in snap["warnings"])); self.assertEqual(snap["disks"][0]["lv"], "ok")

    def test_only_read_methods_are_called(self):
        srv = OmvMock(CERT_A); self.addCleanup(srv.close); m.collect(omv_cfg(srv.port), {})
        self.assertEqual({s for s, _ in srv.calls}, {"Session", "System", "DiskMgmt", "Smart", "FileSystemMgmt", "Network"})
        self.assertTrue(all(me in ("login", "getInformation", "enumerateDevices", "getList", "enumerateFilesystems") for _, me in srv.calls))

class ValidateRemote(unittest.TestCase):
    def test_truenas_rules(self):
        base = {"type": "truenas", "name": "T", "host": "192.0.2.5", "user": "admin", "api_key": "k"}
        c = m.validate(base)
        self.assertEqual((c["port"], c["https"], c["verify_tls"], c["tls_pin"], "password" in c), (443, True, False, "", False))
        self.assertTrue(m.validate({**base, "https": False})["https"])                   # TrueNAS is always TLS
        for bad in ({"api_key": ""}, {"user": ""}, {"host": ""}, {"port": 0}, {"port": True}, {"port": "x"}, {"timeout": 99}, {"name": ""},
                    {"type": "nas9"}, {"type": ["truenas"]}, {"api_key": "a\nb"}, {"user": ["x"]}):
            with self.assertRaises(ValueError, msg=str(bad)): m.validate({**base, **bad})

    def test_omv_rules(self):
        base = {"type": "omv", "name": "O", "host": "192.0.2.6", "user": "admin", "password": "p"}
        c = m.validate(base); self.assertEqual((c["https"], c["port"], "api_key" in c), (True, 443, False))
        self.assertFalse(m.validate({**base, "https": False, "port": 80})["https"])
        with self.assertRaises(ValueError): m.validate({**base, "password": ""})

    def test_edit_keeps_secrets_and_cannot_change_type(self):
        cur = {**m.validate({"type": "truenas", "name": "T", "host": "192.0.2.5", "user": "admin", "api_key": "KEEP"}), "id": "i1", "tls_pin": "ab" * 32}
        n = m.validate({"name": "T2", "api_key": ""}, cur); self.assertEqual((n["api_key"], n["name"], n["tls_pin"]), ("KEEP", "T2", ""))
        with self.assertRaisesRegex(ValueError, "cannot be changed"): m.validate({"type": "omv"}, cur)
        old = {"id": "s1", "name": "S", "host": "192.0.2.7", "port": 161, "version": "2c", "community": "public"}                    # saved before types existed
        self.assertEqual(m.validate({"name": "S2"}, old)["type"], "synology")
        with self.assertRaisesRegex(ValueError, "cannot be changed"): m.validate({"type": "truenas"}, old)

    def test_public_view_has_no_secrets(self):
        p = m.public({**m.validate({"type": "omv", "name": "O", "host": "192.0.2.6", "user": "admin", "password": "TopSecret1"}), "tls_pin": "cd" * 32, "id": "x"})
        self.assertNotIn("TopSecret1", json.dumps(p)); self.assertNotIn("cd" * 32, json.dumps(p))
        self.assertEqual((p["has_password"], p["has_api_key"], p["tls_pinned"], p["type"]), (True, False, True, "omv"))
        self.assertEqual(m.public({"id": "o", "name": "old", "host": "h", "community": "c"})["type"], "synology")

@unittest.skipUnless(HAVE_OPENSSL, "openssl not installed")
class HttpRemote(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        m.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.started = []; cls._ep, m.ensure_poller = m.ensure_poller, lambda n: cls.started.append(n["id"])
        cls.admin, cls.ro = support.make_user("nradm", ADMIN), support.make_user("nrro", READONLY)
        cls.srv = support.Server(m.H)
    @classmethod
    def tearDownClass(cls): m.ensure_poller = cls._ep; cls.srv.close()
    def setUp(self): m.save_nas([])

    def test_create_test_edit_and_secrets_stay_server_side(self):
        tn = TnMock(CERT_A); self.addCleanup(tn.close); c = self.srv.call
        body = {"type": "truenas", "name": "Main TN", "host": "127.0.0.1", "port": tn.port, "user": "admin", "api_key": "KEY", "timeout": 5}
        s, j = c("POST", "/api/test", body, token=self.admin); self.assertEqual((s, j["ok"], j["model"]), (200, True, "TRUENAS-MINI-X"), j)
        s, j = c("POST", "/api/nas", body, token=self.admin); self.assertEqual(s, 201, j)
        nid = j["nas"]["id"]; self.assertNotIn("KEY", json.dumps(j)); self.assertEqual(j["nas"]["type"], "truenas")
        self.assertEqual(c("POST", "/api/nas", body, token=self.admin)[0], 409)
        s, j = c("GET", "/api/nas", token=self.ro); self.assertNotIn('"KEY"', json.dumps(j)); self.assertTrue(j["nas"][0]["has_api_key"])
        s, j = c("POST", "/api/test", {"id": nid, "api_key": ""}, token=self.admin); self.assertTrue(j["ok"], j)                    # saved key is used
        s, j = c("POST", "/api/nas/" + nid, {"name": "Renamed", "api_key": ""}, token=self.admin); self.assertEqual(s, 200, j)
        st = m.load_nas()[0]; self.assertEqual((st["name"], st["api_key"], st["tls_pin"]), ("Renamed", "KEY", ""))
        self.assertEqual(oct(stat.S_IMODE(os.stat(m.DATA_FILE).st_mode)), "0o600")
        self.assertEqual(c("POST", "/api/nas/" + nid, {"type": "omv"}, token=self.admin)[0], 400)
        self.assertEqual(c("POST", "/api/nas", body, token=self.ro)[0], 403)

    def test_wrong_credentials_are_reported_in_the_test(self):
        tn = TnMock(CERT_A); self.addCleanup(tn.close)
        s, j = self.srv.call("POST", "/api/test", {"type": "truenas", "name": "x", "host": "127.0.0.1", "port": tn.port, "user": "admin", "api_key": "bad"}, token=self.admin)
        self.assertEqual((s, j["ok"]), (200, False)); self.assertIn("Authentication failed", j["error"]); self.assertNotIn("bad", j["error"].replace("Authentication", ""))

    def test_pin_is_learned_by_the_poller_path_and_kept(self):
        tn = TnMock(CERT_A); self.addCleanup(tn.close)
        cfg = {**tn_cfg(tn.port), "id": "pin1"}; m.save_nas([cfg])
        m.collect(cfg, {}); self.assertEqual(len(m.load_nas()[0]["tls_pin"]), 64)

    def test_old_records_without_type_still_listed(self):
        m.save_nas([{"id": "old1", "name": "Syn", "host": "192.0.2.9", "port": 161, "version": "2c", "community": "public", "timeout": 5}])
        s, j = self.srv.call("GET", "/api/nas", token=self.ro); self.assertEqual((s, j["nas"][0]["type"], j["nas"][0]["has_community"]), (200, "synology", True))

class EventsAndAlerts(unittest.TestCase):
    def test_timeline_events_use_the_text_status(self):
        seen = []
        orig_rec, orig_chg = m.auth.record_event, m.auth.state_changed
        m.auth.record_event = lambda mod, lv, text, kind, **kw: seen.append((lv, text, kw))
        m.auth.state_changed = lambda key, lv: True
        try:
            snap = {"alerts": [], "raids": [{"idx": "1", "name": "tank", "status": None, "status_text": "DEGRADED", "lv": "warn"}],
                    "disks": [{"idx": "1", "name": "sdb", "status": None, "status_text": "BAD_SECTOR", "lv": "warn"}]}
            m._events({"id": "n1", "name": "NAS1"}, snap)
        finally:
            m.auth.record_event, m.auth.state_changed = orig_rec, orig_chg
        texts = [t for _, t, _ in seen]
        self.assertIn("NAS1/tank: volume status DEGRADED", texts); self.assertIn("NAS1/sdb: disk status BAD_SECTOR", texts)
        self.assertFalse(any("None" in t for t in texts))

    def test_deeply_nested_json_from_the_nas_is_an_error_not_a_crash(self):
        srv = OmvMock(None, deep=True); self.addCleanup(srv.close)
        with self.assertRaisesRegex(remote.RemoteError, "Unexpected answer"): m.collect(omv_cfg(srv.port, https=False), {})

class WsClientUnit(unittest.TestCase):
    def test_fragmented_messages_and_ping(self):
        a, b = socket.socketpair(); ws = remote.WsClient({"host": "x", "port": 1, "timeout": 2}, "/"); ws.sock = a
        b.sendall(bytes([0x01, 3]) + b"hel" + bytes([0x89, 1]) + b"p" + bytes([0x80, 2]) + b"lo")      # "hel" + ping + "lo"
        self.assertEqual(ws.recv_text(), "hello")
        op = b.recv(16); self.assertEqual(op[0], 0x8A)                                                  # pong came back, masked
        a.close(); b.close()

    def test_rejects_extensions_and_oversized_messages(self):
        a, b = socket.socketpair(); ws = remote.WsClient({"host": "x", "port": 1, "timeout": 2}, "/"); ws.sock = a
        b.sendall(bytes([0xC1, 0]));
        with self.assertRaisesRegex(remote.RemoteError, "extension"): ws.recv_text()
        a2, b2 = socket.socketpair(); ws2 = remote.WsClient({"host": "x", "port": 1, "timeout": 2}, "/"); ws2.sock = a2
        b2.sendall(bytes([0x81, 127]) + struct.pack(">Q", remote.MAX_MSG + 1))
        with self.assertRaisesRegex(remote.RemoteError, "too large"): ws2.recv_text()
        for s in (a, b, a2, b2): s.close()

    def test_close_frame_ends(self):
        a, b = socket.socketpair(); ws = remote.WsClient({"host": "x", "port": 1, "timeout": 2}, "/"); ws.sock = a
        b.sendall(bytes([0x88, 0]))
        with self.assertRaisesRegex(remote.RemoteError, "closed"): ws.recv_text()
        a.close(); b.close()

if __name__ == "__main__":
    unittest.main()
