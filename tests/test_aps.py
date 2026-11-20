"""AP Monitor: drivers contra equipos simulados (OpenWrt, MitraStar, Instant On), validación, avisos de caída, permisos y página.
EN: AP Monitor: drivers against simulated devices (OpenWrt, MitraStar, Instant On), validation, down alerts, permissions and page."""
import hashlib
import json
import os
import stat
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import ClassVar

from tests import support

ap = support.load("net-monitor/aps.py")


def serve(handler_cls):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"127.0.0.1:{srv.server_address[1]}"


def _send(h, code, body, ctype="text/html"):
    b = body.encode() if isinstance(body, str) else body
    h.send_response(code); h.send_header("Content-Type", ctype); h.send_header("Content-Length", str(len(b))); h.end_headers(); h.wfile.write(b)


# ---------------------------------------------------------------- OpenWrt (ubus) simulado
class UbusHandler(BaseHTTPRequestHandler):
    calls: ClassVar[list] = []
    def log_message(self, *a): pass
    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        sid, obj, method, args = req["params"]
        self.calls.append((obj, method, args.get("device")))
        if obj == "session":
            res = [0, {"ubus_rpc_session": "s" * 32}] if args.get("password") == "pw" else [6]
        elif sid != "s" * 32:
            res = [6]
        else:
            res = {("system", "board"): [0, {"model": "Cisco Meraki MR33", "release": {"description": "OpenWrt 23.05.3"}}],
                   ("system", "info"): [0, {"uptime": 3725}],
                   ("iwinfo", "devices"): [0, {"devices": ["phy0-ap0", "phy1-ap0", "phy1-sta0"]}],
                   ("iwinfo", "survey"): [0, {"results": [{"mhz": 5180, "active_time": 1000, "busy_time": 250}]}]}.get((obj, method))
            if (obj, method) == ("iwinfo", "info"):
                res = [0, {"phy0-ap0": {"mode": "Master", "ssid": "Lab", "frequency": 2437, "channel": 6, "htmode": "HT20", "txpower": 20},
                           "phy1-ap0": {"mode": "Master", "ssid": "Lab", "frequency": 5180, "channel": 36, "htmode": "VHT80", "txpower": 23},
                           "phy1-sta0": {"mode": "Client", "ssid": "Up", "frequency": 5180, "channel": 36}}[args["device"]]]
            elif (obj, method) == ("iwinfo", "assoclist"):
                res = [0, {"results": [{"mac": "AA:BB:CC:00:00:01", "signal": -58, "noise": -95, "rx": {"rate": 433300}, "tx": {"rate": 866700}, "connected_time": 120}]
                           if args["device"] == "phy1-ap0" else []}]
        body = {"jsonrpc": "2.0", "id": req["id"], "result": res} if res else {"jsonrpc": "2.0", "id": req["id"], "error": {"code": -32000, "message": "Object not found"}}
        _send(self, 200, json.dumps(body), "application/json")


class OpenWrt(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.srv, cls.host = serve(UbusHandler)
    @classmethod
    def tearDownClass(cls): cls.srv.shutdown(); cls.srv.server_close()

    def test_snapshot_reads_radios_ssids_and_clients(self):
        UbusHandler.calls.clear()
        a = ap.OpenWrtDriver({"name": "Meraki", "host": self.host, "user": "root", "password": "pw"}).snapshot()[0]
        self.assertEqual((a["model"], a["fw"], a["uptime"]), ("Cisco Meraki MR33", "OpenWrt 23.05.3", 3725))
        self.assertEqual([(r["band"], r["channel"], r["width"], r["clients"]) for r in a["radios"]], [("2.4", 6, "HT20", 0), ("5", 36, "VHT80", 1)])
        self.assertEqual(a["radios"][1]["util"], 25)
        self.assertEqual(a["ssids"], [{"name": "Lab", "bands": ["2.4", "5"]}])
        c = a["clients"][0]
        self.assertEqual((c["mac"], c["band"], c["signal"], c["snr"], c["rate"], c["connected"]), ("aa:bb:cc:00:00:01", "5", -58, 37, 867, 120))
        self.assertNotIn(("iwinfo", "assoclist", "phy1-sta0"), UbusHandler.calls)       # the uplink (client mode) is not an AP radio

    def test_wrong_password(self):
        with self.assertRaisesRegex(ap.APError, "wrong user or password"):
            ap.OpenWrtDriver({"name": "x", "host": self.host, "password": "bad"}).snapshot()


# ---------------------------------------------------------------- OpenWrt 19.07 con LuCI (respuestas reales saneadas: sin clave Wi-Fi, MAC y SSID genéricos)
# EN: OpenWrt 19.07 with LuCI (real answers, sanitised: no Wi-Fi key, generic MACs and SSIDs). No /ubus: LuCI's ubus; root may not call
#     iwinfo devices/info/survey, only luci-rpc getWirelessDevices and iwinfo assoclist.
LUCI_WD = {"radio0": {"iwinfo": {"txpower": 21, "channel": 6, "frequency": 2437}, "config": {"hwmode": "11g", "htmode": "HT40", "channel": "auto"}, "up": True,
                      "interfaces": [{"ifname": "wlan0", "iwinfo": {"ssid": "Lab_2.4G", "txpower": 21, "channel": 6, "mode": "Master", "frequency": 2437},
                                      "config": {"key": "not-a-real-key", "encryption": "psk2", "mode": "ap", "ssid": "Lab_2.4G"}}]},
           "radio1": {"iwinfo": {"txpower": 19, "channel": 44, "frequency": 5220}, "config": {"hwmode": "11a", "htmode": "HT40", "channel": "auto"}, "up": True,
                      "interfaces": [{"ifname": "wlan1", "iwinfo": {"ssid": "Lab_5G", "mode": "Master", "txpower": 19, "channel": 44, "frequency": 5220},
                                      "config": {"key": "not-a-real-key", "mode": "ap", "ssid": "Lab_5G"}}]}}
LUCI_ASSOC = [{"mac": "02:00:00:00:00:03", "signal": -42, "noise": -95, "connected_time": 1287723, "inactive": 70, "rx": {"rate": 6000}, "tx": {"rate": 58500}},
              {"mac": "02:00:00:00:00:06", "signal": -71, "noise": -95, "connected_time": 862943, "inactive": 3310, "rx": {"rate": 65000}, "tx": {"rate": 65000}}]


class LuciHandler(BaseHTTPRequestHandler):
    calls: ClassVar[list] = []
    def log_message(self, *a): pass
    def do_POST(self):
        if self.path != "/cgi-bin/luci/admin/ubus":
            return _send(self, 404, "<h1>Not Found</h1>")
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        sid, obj, method, args = req["params"]
        self.calls.append((obj, method))
        out = {"jsonrpc": "2.0", "id": req["id"]}
        if obj == "session":
            out["result"] = [0, {"ubus_rpc_session": "l" * 32}] if args.get("password") == "pw" else [6]
        elif sid != "l" * 32 or (obj, method) not in (("system", "board"), ("system", "info"), ("luci-rpc", "getWirelessDevices"), ("iwinfo", "assoclist")):
            out["error"] = {"message": "Access denied", "code": -32002}
        else:
            out["result"] = [0, {("system", "board"): {"model": "Meraki MR16", "release": {"description": "OpenWrt 19.07.5 r11257-5090152ae3"}},
                                 ("system", "info"): {"uptime": 2539853}, ("luci-rpc", "getWirelessDevices"): LUCI_WD,
                                 ("iwinfo", "assoclist"): {"results": LUCI_ASSOC if args.get("device") == "wlan0" else []}}[(obj, method)]]
        _send(self, 200, json.dumps(out), "application/json")


class OpenWrtLuci(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.srv, cls.host = serve(LuciHandler)
    @classmethod
    def tearDownClass(cls): cls.srv.shutdown(); cls.srv.server_close()

    def test_uses_lucis_ubus_and_does_not_keep_the_wifi_key(self):
        LuciHandler.calls.clear()
        d = ap.OpenWrtDriver({"name": "Meraki", "host": self.host, "user": "root", "password": "pw"})
        a = d.snapshot()[0]
        self.assertEqual(d.path, "/cgi-bin/luci/admin/ubus")
        self.assertEqual((a["model"], a["uptime"]), ("Meraki MR16", 2539853))
        self.assertEqual([(r["band"], r["channel"], r["width"], r["txpower"], r["util"], r["clients"]) for r in a["radios"]],
                         [("2.4", 6, "HT40", 21, None, 2), ("5", 44, "HT40", 19, None, 0)])
        self.assertEqual(a["ssids"], [{"name": "Lab_2.4G", "bands": ["2.4"]}, {"name": "Lab_5G", "bands": ["5"]}])
        self.assertEqual([(c["signal"], c["snr"], c["rate"], c["band"]) for c in a["clients"]], [(-42, 53, 58, "2.4"), (-71, 24, 65, "2.4")])
        self.assertNotIn("not-a-real-key", json.dumps(a))
        logins, surveys = LuciHandler.calls.count(("session", "login")), LuciHandler.calls.count(("iwinfo", "survey"))
        d.snapshot()                                                           # survey is refused: not asked again, no extra logins
        self.assertEqual(LuciHandler.calls.count(("session", "login")), logins)
        self.assertEqual(LuciHandler.calls.count(("iwinfo", "survey")), surveys)


# ---------------------------------------------------------------- MitraStar simulado
SYSINFO = """<html><body><div>MENÚ</div><a href="logout.cgi">Cerrar sesión</a><h2>Información de equipo</h2>
<table><tr><td>Nombre del equipo:</td><td>Ext 1</td></tr><tr><td>Modelo:</td><td>HGW-500SN2A4-Qv3</td></tr>
<tr><td>Serial Number:</td><td>SN0001</td></tr><tr><td>Versión Hardware:</td><td>1.0</td></tr><tr><td>Versión Software:</td><td>GL_g8.5_100WZA0b25</td></tr>
<tr><td>Versión Firmware:</td><td>GL_g8.5_100WZA0b25</td></tr><tr><td>Código de país:</td><td>CL</td></tr><tr><td>Estado:</td><td>Punto de Acceso</td></tr></table>
<h2>Información Red WiFi Plus</h2><table><tr><td>Estado WiFi:</td><td><img src="on.png"></td></tr><tr><td>Identificador Red Inalámbrica (SSID):</td><td>Lab_5G</td></tr>
<tr><td>Modo:</td><td>PUNTO DE ACCESO</td></tr><tr><td>Ocultar SSID:</td><td></td></tr><tr><td>Tipo cifrado:</td><td></td></tr><tr><td>Encriptación:</td><td></td></tr><tr><td>Canal Uso:</td><td>149</td></tr></table>
<h2>Información Red Local</h2><table><tr><td>Dirección IP (Gateway):</td><td>192.0.2.8</td></tr><tr><td>Máscara de subred:</td><td>255.255.255.0</td></tr><tr><td>Cliente DHCP:</td><td>DESACTIVADO</td></tr></table>
<h2>Información Red WiFi</h2><table><tr><td>Estado WiFi:</td><td></td></tr><tr><td>Identificador Red Inalámbrica (SSID):</td><td>Lab_2.4G</td></tr><tr><td>Ocultar SSID:</td><td></td></tr>
<tr><td>Tipo cifrado:</td><td></td></tr><tr><td>Encriptación:</td><td></td></tr><tr><td>Canal Uso:</td><td>11</td></tr></table><p>© Telefónica</p></body></html>"""


class MSHandler(BaseHTTPRequestHandler):
    """Como el equipo real: login correcto = 302 a wifi5g.cgi con una cookie de sesión HttpOnly; sin ella, 302 al login.
    EN: Like the real unit: a good login = 302 to wifi5g.cgi with an HttpOnly session cookie; without it, 302 to the login."""
    state: ClassVar[dict] = {"logged": False, "hits": [], "form": None}
    def log_message(self, *a): pass
    def _redirect(self, to, cookie=None):
        self.send_response(302); self.send_header("Location", to)
        if cookie: self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", "0"); self.end_headers()
    def do_GET(self):
        p = self.path.lstrip("/")
        self.state["hits"].append(p)
        has = "sess=abc123" in (self.headers.get("Cookie") or "")
        if p == "index.cgi": return _send(self, 200, "<script>function ButtonSumbit(value){var sid='4e74f030';}</script><form action='index.cgi'></form>")
        if p == "logout.cgi": self.state["logged"] = False; return _send(self, 200, "bye")
        if p in ("sysinfo.cgi", "wifi5g.cgi"):
            return _send(self, 200, SYSINFO) if self.state["logged"] and has else self._redirect("index.cgi")
        _send(self, 404, "")
    def do_POST(self):
        f = urllib.parse.parse_qs(self.rfile.read(int(self.headers["Content-Length"])).decode())
        self.state["form"] = f
        ok = f.get("login_password") == [hashlib.md5(b"pw:4e74f030").hexdigest()]  # nosec B324 - device format
        self.state["logged"] = ok and not self.state.get("busy")             # one session at a time / una sesión a la vez
        if ok: return self._redirect("wifi5g.cgi", "sess=abc123; Path=/; HttpOnly")
        _send(self, 200, '<div id="tab_fail" class="finBox"><div class="artBox">Su contraseña es incorrecta</div></div>')


class MitraStar(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.srv, cls.host = serve(MSHandler)
    @classmethod
    def tearDownClass(cls): cls.srv.shutdown(); cls.srv.server_close()

    def test_parse(self):
        d = ap.parse_mitrastar(SYSINFO)
        self.assertEqual((d["model"], d["fw"], d["serial"], d["mode"]), ("HGW-500SN2A4-Qv3", "GL_g8.5_100WZA0b25", "SN0001", "Punto de Acceso"))
        self.assertEqual(d["radios"], [{"band": "2.4", "channel": 11, "width": None, "txpower": None, "util": None, "clients": None},
                                       {"band": "5", "channel": 149, "width": None, "txpower": None, "util": None, "clients": None}])
        self.assertEqual(d["ssids"], [{"name": "Lab_2.4G", "bands": ["2.4"]}, {"name": "Lab_5G", "bands": ["5"]}])
        with self.assertRaises(ap.APError):
            ap.parse_mitrastar("<html>other device</html>")

    def test_login_reads_and_always_logs_out(self):
        MSHandler.state.update(logged=False, hits=[])
        a = ap.MitraStarDriver({"name": "Ext", "host": self.host, "mode": "web", "password": "pw"}).snapshot()[0]
        self.assertEqual((a["model"], a["serial"], a["clients"], a["uptime"]), ("HGW-500SN2A4-Qv3", "SN0001", None, None))
        self.assertEqual(MSHandler.state["form"]["submitValue"], ["1"])
        self.assertNotIn("login_password_old", {k for k, v in MSHandler.state["form"].items() if v != [""]})   # the clear password is never sent
        self.assertEqual(MSHandler.state["hits"][-3:], ["wifi5g.cgi", "sysinfo.cgi", "logout.cgi"])    # follows the login redirect, with the cookie
        MSHandler.state["hits"].clear()
        with self.assertRaisesRegex(ap.APError, "^wrong password"):
            ap.MitraStarDriver({"name": "Ext", "host": self.host, "mode": "web", "password": "bad"}).snapshot()
        self.assertNotIn("sysinfo.cgi", MSHandler.state["hits"])                # a refused password reads nothing more
        MSHandler.state.update(busy=True, hits=[])
        try:
            with self.assertRaisesRegex(ap.APError, "password accepted.*cookies: sess.*one session at a time"):
                ap.MitraStarDriver({"name": "Ext", "host": self.host, "mode": "web", "password": "pw"}).snapshot()
        finally: MSHandler.state["busy"] = False
        self.assertEqual(MSHandler.state["hits"][-1], "logout.cgi")

    def test_ping_mode_never_logs_in(self):
        o = ap.ping
        try:
            ap.ping = lambda h: h == "192.0.2.8"
            a = ap.MitraStarDriver({"name": "Ext", "host": "192.0.2.8", "mode": "ping"}).snapshot()[0]
            self.assertTrue(a["online"]); self.assertEqual(a["note"], "ping"); self.assertIsNone(a["clients"])
        finally: ap.ping = o


# ---------------------------------------------------------------- Instant On (portal simulado)
INV = {"elements": [
    {"id": "aa:00:00:00:00:01", "deviceType": "accessPoint", "name": "Living", "model": "AP-303", "deviceSoftwareVersion": "3.4.2.0", "serialNumber": "SN-A",
     "ipAddress": "192.0.2.14", "macAddress": "aa:00:00:00:00:01", "status": "up", "uptimeInSeconds": 51168,
     "radios": [{"band": "5ghz", "channel": 64, "channelWidth": "80mhz", "txPowerEirpInDbm": 21.6, "utilizationPercent": 12, "wirelessClientsCount": 1}],
     "wirelessNetworks": [{"networkName": "Lab", "enabledRadioBands": ["2.4ghz", "5ghz"]}], "uplinkSummary": {}},
    {"id": "aa:00:00:00:00:02", "deviceType": "accessPoint", "name": "Bedroom", "model": "AP-303", "macAddress": "aa:00:00:00:00:02", "status": "down",
     "radios": [], "wirelessNetworks": [], "uplinkSummary": {"name": "Living", "radioBand": "5ghz"}},
    {"id": "sw1", "deviceType": "switch", "name": "Switch"}]}
CLIENTS = {"elements": [
    {"macAddress": "bb:00:00:00:00:01", "name": "bb:00:00:00:00:01", "hostName": "phone", "ipAddress": "192.0.2.50", "deviceId": "aa:00:00:00:00:01",
     "wirelessNetworkId": "n1", "wirelessNetworkName": "Lab", "wirelessBand": "5ghz", "snrInDb": 32, "signalQuality": "good", "stateDurationInSeconds": 600},
    {"macAddress": "bb:00:00:00:00:02", "deviceId": "aa:00:00:00:00:01", "wirelessNetworkId": None},
    {"macAddress": "bb:00:00:00:00:03", "name": "gone", "deviceId": "aa:00:00:00:00:01", "wirelessNetworkId": "n1", "status": "down", "wirelessBand": "2.4ghz"},
    {"macAddress": "bb:00:00:00:00:04", "name": "bb:00:00:00:00:04", "hostName": "BB:00:00:00:00:04", "ipAddress": "0.0.0.0", "status": "up",  # nosec B104 - test data
     "deviceId": "aa:00:00:00:00:01", "wirelessNetworkId": "n1", "wirelessBand": "2.4ghz", "snrInDb": 20, "signalQuality": "fair"}]}


class InstantOn(unittest.TestCase):
    def drv(self, **kw):
        d = ap.InstantOnDriver({"name": "Aruba", "mode": "cloud", "user": "x@example.lan", "password": "pw", **kw})
        d.api = lambda path: {"sites": {"elements": [{"id": "s1", "name": "Home"}, {"id": "s2", "name": "Office"}]},
                              "sites/s1/inventory": INV, "sites/s1/clientSummary": CLIENTS, "sites/s2/inventory": {"elements": []}}.get(path, {"elements": []})
        return d

    def test_snapshot_lists_only_access_points_with_their_clients(self):
        aps = self.drv(site="home").snapshot()
        self.assertEqual([a["name"] for a in aps], ["Living", "Bedroom"])
        a, b = aps
        self.assertTrue(a["online"]); self.assertFalse(b["online"])
        self.assertEqual((a["model"], a["fw"], a["serial"], a["uptime"]), ("AP-303", "3.4.2.0", "SN-A", 51168))
        self.assertEqual(a["radios"], [{"band": "5", "channel": 64, "width": "80mhz", "txpower": 21, "util": 12, "clients": 1}])
        self.assertEqual(a["ssids"], [{"name": "Lab", "bands": ["2.4", "5"]}])
        self.assertEqual(len(a["clients"]), 2)                                   # the wired and the gone ("down") clients are left out
        c = a["clients"][0]
        self.assertEqual((a["clients"][1]["name"], a["clients"][1]["ip"]), (None, None))   # name repeating the MAC and 0.0.0.0 -> empty
        self.assertEqual((c["name"], c["ip"], c["band"], c["ssid"], c["snr"], c["quality"]), ("phone", "192.0.2.50", "5", "Lab", 32, "good"))
        self.assertEqual(b["note"], "mesh → Living")
        with self.assertRaisesRegex(ap.APError, "site not found"):
            self.drv(site="nope").snapshot()

    def test_api_logs_in_again_once_on_401(self):
        d = ap.InstantOnDriver({"name": "Aruba", "mode": "cloud", "user": "x@example.lan", "password": "pw"})
        logins, seen = [], []
        def login(): logins.append(1); d.token = f"t{len(logins)}"; d.settings = {"restApiUrl": "https://api.example.lan"}
        class R:
            def __init__(self, b): self.b = b
            def read(self, n): return self.b
            def __enter__(self): return self
            def __exit__(self, *a): return False
        def opener(req, follow=True):
            seen.append((req.full_url, req.headers.get("Authorization"), req.headers.get("X-ion-api-version")))
            if req.headers.get("Authorization") == "Bearer t1": raise urllib.error.HTTPError(req.full_url, 401, "", {}, None)
            return R(b'{"elements": []}')
        d._login, d._open = login, opener
        self.assertEqual(d.api("sites"), {"elements": []})
        self.assertEqual(len(logins), 2)
        self.assertEqual(seen[-1], ("https://api.example.lan/api/sites", "Bearer t2", "7"))

    def test_login_flow_uses_pkce_and_reads_the_code_from_the_redirect(self):
        d = ap.InstantOnDriver({"name": "Aruba", "mode": "cloud", "user": "x@example.lan", "password": "pw"})
        posts, auth_q = [], {}
        def j(url, data=None, headers=None):
            if url.endswith("/settings.json"):
                return {"ssoFqdn": "https://sso.example.lan", "ssoClientIdAuthZ": "cid", "ssoRedirectUrl": "https://portal.example.lan", "restApiUrl": "https://api.example.lan"}
            posts.append((url, data))
            return {"access_token": "session" if "validate" in url else "bearer"}
        def opener(req, follow=True):
            self.assertFalse(follow)
            auth_q.update(urllib.parse.parse_qs(urllib.parse.urlparse(req.full_url).query))
            raise urllib.error.HTTPError(req.full_url, 302, "", {"Location": "https://portal.example.lan/?code=abc&state=x"}, None)
        d._json, d._open = j, opener
        d._login()
        self.assertEqual(d.token, "bearer")
        self.assertEqual(posts[0], ("https://sso.example.lan/aio/api/v1/mfa/validate/full", {"username": "x@example.lan", "password": "pw"}))
        tok = posts[1][1]
        self.assertEqual((tok["code"], tok["grant_type"], tok["client_id"]), ("abc", "authorization_code", "cid"))
        import base64
        self.assertEqual(auth_q["code_challenge"][0], base64.urlsafe_b64encode(hashlib.sha256(tok["code_verifier"].encode()).digest()).rstrip(b"=").decode())
        self.assertEqual((auth_q["sessionToken"][0], auth_q["code_challenge_method"][0]), ("session", "S256"))


# ---------------------------------------------------------------- Validación y gestor / validation and manager
class Config(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self._vt = ap.auth.valid_target
        ap.auth.valid_target = lambda h, *a, **k: h != "127.0.0.1"
        self.events = []
        self.m = ap.Manager(self.d, hooks={"event": lambda *a, **k: self.events.append(a[3]), "changed": self._changed,
                                            "hosts": lambda: {"bb0000000001": {"ip": "192.0.2.77", "name": "My phone"}}})
        self.seen = {}
    def tearDown(self): ap.auth.valid_target = self._vt; self.m.stop()
    def _changed(self, key, state):
        old = self.seen.get(key); self.seen[key] = state
        return (old, state) if old is not None and old != state else None

    def test_validate(self):
        ok = ap.validate({"name": "Ext", "driver": "mitrastar", "mode": "ping", "host": "192.0.2.8"})
        self.assertEqual((ok["mode"], "password" in ok), ("ping", False))
        self.assertEqual(ap.validate({"name": "Mk", "driver": "openwrt", "host": "192.0.2.9", "password": "x"})["user"], "root")
        cl = ap.validate({"name": "Ar", "driver": "instanton", "mode": "cloud", "user": "a@example.lan", "password": "x", "site": "Home"})
        self.assertNotIn("host", cl); self.assertEqual(cl["site"], "Home")
        for bad in ({"name": "", "driver": "openwrt", "host": "192.0.2.9", "password": "x"}, {"name": "A", "driver": "unifi", "host": "192.0.2.9"},
                    {"name": "A", "driver": "openwrt", "mode": "ping", "host": "192.0.2.9"}, {"name": "A", "driver": "openwrt", "host": "192.0.2.9"},
                    {"name": "A", "driver": "openwrt", "host": "127.0.0.1", "password": "x"}, {"name": "A", "driver": "instanton", "mode": "cloud", "user": "nomail", "password": "x"}):
            with self.assertRaises(ValueError, msg=bad):
                ap.validate(bad)
        cur = ap.validate({"name": "Mk", "driver": "openwrt", "host": "192.0.2.9", "password": "keep"})
        self.assertEqual(ap.validate({"name": "Mk2"}, cur)["password"], "keep")                  # empty password keeps the stored one

    def test_save_is_private_and_redacted(self):
        out = self.m.save({"name": "Mk", "driver": "openwrt", "host": "192.0.2.9", "password": "secret", "enabled": False})
        self.assertNotIn("password", out); self.assertTrue(out["has_password"])
        self.assertEqual(stat.S_IMODE(os.stat(os.path.join(self.d, "aps.json")).st_mode), 0o600)
        self.assertNotIn("secret", json.dumps(self.m.list_config()))
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.m.save({"name": "mk", "driver": "openwrt", "host": "192.0.2.10", "password": "x"})
        self.m.delete(out["id"]); self.assertEqual(self.m.list_config()["aps"], [])

    def test_down_after_two_failures_and_back(self):
        cfg = self.m.save({"name": "Mk", "driver": "openwrt", "host": "192.0.2.9", "password": "x", "enabled": False})
        aid, c = cfg["id"], self.m._find(cfg["id"])
        self.m._ingest(aid, c, [ap._ap("main", "Mk", clients=[])])
        self.m._fail(aid, c, ap.APError("timeout"))
        self.assertEqual(self.events, [])
        self.m._fail(aid, c, ap.APError("timeout"))
        self.assertEqual(self.events, ["ap_down"])
        self.m._ingest(aid, c, [ap._ap("main", "Mk", clients=[])])
        self.assertEqual(self.events, ["ap_down", "ap_up"])

    def test_cloud_ap_down_needs_two_readings(self):
        cfg = self.m.save({"name": "Ar", "driver": "instanton", "mode": "cloud", "user": "a@example.lan", "password": "x", "enabled": False})
        aid, c = cfg["id"], self.m._find(cfg["id"])
        self.m._ingest(aid, c, [ap._ap("s:1", "Living"), ap._ap("s:2", "Bedroom")])
        self.m._ingest(aid, c, [ap._ap("s:1", "Living"), ap._ap("s:2", "Bedroom", online=False)])
        self.assertEqual(self.events, [])
        self.m._ingest(aid, c, [ap._ap("s:1", "Living"), ap._ap("s:2", "Bedroom", online=False)])
        self.assertEqual(self.events, ["ap_down"])

    def test_state_hides_serial_and_names_clients(self):
        cfg = self.m.save({"name": "Ar", "driver": "instanton", "mode": "cloud", "user": "a@example.lan", "password": "x"})
        self.m.stop()
        c = self.m._find(cfg["id"])
        self.m._ingest(cfg["id"], c, [ap._ap("s:1", "Living", serial="SN-A", clients=[{"mac": "bb:00:00:00:00:01", "ip": None, "name": None}])])
        a = self.m.state()["aps"][0]
        self.assertIsNone(a["serial"]); self.assertTrue(a["online"]); self.assertEqual(a["nclients"], 1)
        self.assertEqual((a["clients"][0]["name"], a["clients"][0]["ip"]), ("My phone", "192.0.2.77"))
        self.assertEqual(self.m.state(serials=True)["aps"][0]["serial"], "SN-A")
        self.m.save({"id": cfg["id"], "enabled": False})
        p = self.m.state()["aps"][0]
        self.assertTrue(p["paused"]); self.assertFalse(p["down"])


# ---------------------------------------------------------------- API de Net Monitor / Net Monitor API
class Api(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.net = support.load("net-monitor/server.py")
        cls.adm = support.make_user("apadm", support.ADMIN)
        cls.ro = support.make_user("apro", support.READONLY)
        cls.srv = support.Server(cls.net.H)
    @classmethod
    def tearDownClass(cls): cls.srv.close()

    def test_permissions(self):
        self.assertEqual(self.srv.call("GET", "/api/aps")[0], 401)
        s, j = self.srv.call("GET", "/api/aps", token=self.ro)
        self.assertEqual(s, 200); self.assertIn("aps", j)
        self.assertEqual(self.srv.call("GET", "/api/aps/config", token=self.ro)[0], 403)
        self.assertEqual(self.srv.call("POST", "/api/aps/save", {"name": "x"}, token=self.ro)[0], 403)
        self.assertEqual(self.srv.call("POST", "/api/aps/refresh", {}, token=self.ro)[0], 200)
        s, j = self.srv.call("POST", "/api/aps/save", {"name": "", "driver": "openwrt"}, token=self.adm)
        self.assertEqual(s, 400)
        self.assertEqual(self.srv.call("POST", "/api/aps/nope", {}, token=self.adm)[0], 404)


class Page(unittest.TestCase):
    def test_tab_script_and_backups(self):
        r = lambda p: (support.ROOT / p).read_text(encoding="utf-8")
        html, sw, js = r("net-monitor/static/index.html"), r("net-monitor/static/switches.js"), r("net-monitor/static/aps.js")
        self.assertIn('data-view="aps" data-i18n="tabAps"', html)
        self.assertIn('<div class="content" id="view-aps" hidden></div>', html)
        self.assertLess(html.index('src="aps.js"'), html.index('src="switches.js"'))
        self.assertIn("const VIEWS = ['hosts', 'switches', 'aps'];", sw)
        self.assertIn("document.dispatchEvent(new CustomEvent('netview', { detail: SW.view }));", sw)
        self.assertIn("document.addEventListener('netview'", js)
        self.assertNotRegex(js, r"\son[a-z]+=")                                  # CSP: no inline handlers
        self.assertIn("if (AP.busy) { AP.again = true; return; }", js)          # a click during a refresh is not lost
        self.assertIn("apQ: { good: 'buena', fair: 'regular', poor: 'mala' }", js)
        for f in ("debian/preinst", "debian/prerm", "scripts/teleporter.sh"):
            self.assertIn("net-monitor/aps.json", r(f), f)
        ov = r("overview/static/app.js")
        self.assertEqual(ov.count("ap_down:"), 2); self.assertEqual(ov.count("ap_up:"), 2)
