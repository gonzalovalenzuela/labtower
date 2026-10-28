"""Switch Monitor: drivers contra equipos simulados, tasas, eventos, topología, historial y API de Net Monitor."""
import json, os, sqlite3, stat, tempfile, threading, time, unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from tests import support

sw = support.load("net-monitor/switches.py")


def serve(handler_cls):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"127.0.0.1:{srv.server_address[1]}"


# ---------------------------------------------------------------- ZX310S simulado
def zx_site(state):
    def pk(n): return str(n)
    stats = {"PortNum": "10"}
    cfg, loop, stp = {}, {}, {"stp_enable": "1"}
    for j in range(1, 11):
        up = j in (3, 4, 7, 9)
        stats[f"Port_{j}"] = {"Link_Status": "10GbpsFull" if j in (9, 7) else "1000MbpsFull" if up else "Link Down", "Port_Status": "Enabled",
                              "TxGoodPkt": pk(1000 * j + state["tick"] * 100), "TxBadPkt": pk(3 if j == 4 else 0),
                              "RxGoodPkt": pk(2000 * j + state["tick"] * 200), "RxBadPkt": pk(181 + state["new_err"] if j == 4 else 0)}
        cfg[f"Port_{j}"] = {"Spd_Duplex_Cfg": "Auto", "Flow_Ctrl_Actual": "Off"}
        loop[f"Violdetd_{j}"] = "1" if j in (7, 8) else "0"
        stp[f"Port_{j}"] = {f"Stp_Status_{j}": "Forwarding" if up else "Disabled"}
    macs = {"total_entries": 2,
            "Idx_0": {"Dynamic_mac_addr": "B8:27:EB:00:00:01", "Dynamic_portid": "3", "Dynamic_fid": "1", "Dynamic_age_timer": "300"},
            "Idx_1": {"Dynamic_mac_addr": "AA:BB:CC:DD:EE:07", "Dynamic_portid": "13", "Dynamic_fid": "1", "Dynamic_age_timer": "280"}}   # ID 13 = frontal 9
    return {"status.json": {"modle": "ZX310S-8T2XS", "des": "lab", "sys_macaddr": "AA:BB:CC:DD:EE:00", "sys_ipv4": "192.0.2.6",
                            "fw_ver": "1.0.0.6", "hw_ver": "A0", "temperature": str(state["temp"])},
            "port_statistics.json": stats, "port_setting_load.json": cfg, "port_loop_status.json": loop, "stp.json": stp,
            "mac_get_dynamic_mac_entries.json": macs}


class ZXHandler(BaseHTTPRequestHandler):
    state = {"tick": 0, "temp": 74, "new_err": 0, "expire_once": False, "hits": []}
    def log_message(self, *a): pass
    def do_GET(self):
        path = self.path.lstrip("/").split("?")[0]
        self.state["hits"].append(path)
        if path == "authorize": body = "ok"
        elif self.state["expire_once"] and path == "status.json":
            self.state["expire_once"] = False; body = "<script>location='login.html'</script>"
        else: body = json.dumps(zx_site(self.state).get(path, {}))
        b = body.encode(); self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)


# ---------------------------------------------------------------- HC simulado
def table(rows): return "<table>" + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows) + "</table>"

class HCHandler(BaseHTTPRequestHandler):
    posts = []
    def log_message(self, *a): pass
    def _send(self, body):
        b = body.encode(); self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0); self.posts.append((self.path, self.rfile.read(n).decode()))
        self._send("<html>ok</html>")
    def do_GET(self):
        p = self.path.lstrip("/")
        if p == "info.cgi":
            body = table([["Device Model", "HC-SWTGW218AS"], ["MAC Address", "AA:BB:CC:DD:FF:00"], ["IP Address", "192.0.2.4"], ["Firmware Version", "V1.9.1"], ["Hardware Version", "V1.1"]])
        elif p == "port.cgi?page=stats":
            body = table([["Port", "State", "Link Status", "TxGoodPkt", "TxBadPkt", "RxGoodPkt", "RxBadPkt"],
                          ["Port 1", "Enable", "Link Up", "100", "0", "200", "0"], ["Port 2", "Enable", "Link Down", "0", "0", "0", "0"],
                          ["Port 3", "Enable", "Link Up", "50", "1", "70", "2"]])
        elif p == "port.cgi":
            body = table([["Port 1", "Enable", "Auto", "2500Full", "Off", "Off"], ["Port 2", "Enable", "Auto", "Link Down", "Off", "Off"], ["Port 3", "Enable", "Auto", "100Full", "Off", "Off"]])
        elif p == "loop.cgi?page=stp_port":
            body = table([["Port 1", "Forwarding", "x"], ["Port 2", "Disabled", "x"], ["Port 3", "Forwarding", "x"]])
        elif p == "mac.cgi?page=fwd_tbl":
            body = table([["No.", "MAC", "VLAN", "Type", "Port"], ["1", "AA:BB:CC:DD:EE:00", "1", "Dynamic", "1"], ["2", "B8:27:EB:00:00:09", "1", "Dynamic", "3"]])
        else: body = "<html></html>"
        self._send(body)


class FakeSNMP:
    def __init__(self, data): self.d = data
    def get(self, oids): return {o: self.d[o] for o in oids if o in self.d}
    def walk(self, base, max_rep=20):
        pre = base.strip(".") + "."
        return {o[len(pre):]: v for o, v in self.d.items() if o.startswith(pre)}


def snmp_data():
    d = {"1.3.6.1.2.1.1.1.0": b"TL-SG3428, 24 ports", "1.3.6.1.2.1.1.3.0": 8640000, "1.3.6.1.2.1.1.5.0": b"tplink",
         "1.3.6.1.2.1.17.1.1.0": bytes.fromhex("AABBCCDDEE00")[:5] + b"\x20"}
    IF, IFX = "1.3.6.1.2.1.2.2.1", "1.3.6.1.2.1.31.1.1.1"
    for i, (up, rx, tx) in {1: (1, 10_000_000, 5_000_000), 2: (2, 0, 0)}.items():
        d[f"{IF}.3.{i}"], d[f"{IF}.2.{i}"] = 6, f"gi{i}".encode()
        d[f"{IF}.7.{i}"], d[f"{IF}.8.{i}"] = 1, up
        d[f"{IF}.14.{i}"], d[f"{IF}.20.{i}"], d[f"{IF}.13.{i}"], d[f"{IF}.19.{i}"] = 0, 0, 0, 0
        d[f"{IF}.5.{i}"] = 1_000_000_000
        d[f"{IFX}.1.{i}"], d[f"{IFX}.6.{i}"], d[f"{IFX}.10.{i}"], d[f"{IFX}.15.{i}"] = f"Gi1/0/{i}".encode(), rx, tx, 1000
        for c in (7, 8, 9, 11, 12, 13): d[f"{IFX}.{c}.{i}"] = 10
        d[f"1.3.6.1.2.1.17.1.4.1.2.{i}"] = i
    d[f"{IF}.3.99"] = 24                                          # loopback: no es un puerto físico
    d["1.3.6.1.2.1.17.7.1.2.2.1.2.1.170.187.204.221.238.1"] = 1     # MAC AA:BB:CC:DD:EE:01 en el puerto 1
    return d


class Drivers(unittest.TestCase):
    def test_zx_snapshot_maps_crossed_sfp_and_reads_temperature(self):
        ZXHandler.state.update(tick=0, temp=74, new_err=0, expire_once=False, hits=[])
        srv, host = serve(ZXHandler)
        snap = sw.ZXDriver("zx", host, "admin", "pw", gap=0).snapshot()
        srv.shutdown(); srv.server_close()
        self.assertEqual(snap["system"]["temperature_c"], 74.0)
        self.assertEqual(snap["system"]["model"], "ZX310S-8T2XS")
        by = {p["port"]: p for p in snap["ports"]}
        self.assertEqual(len(by), 10)
        # JSON Port_9 (10 GbE, up) = frontal 10; el JSON Port_10 (abajo) = frontal 9
        self.assertEqual((by[10]["link_up"], by[10]["speed_mbps"]), (True, 10000))
        self.assertFalse(by[9]["link_up"])
        self.assertEqual((by[4]["rx_bad_pkts"], by[4]["tx_bad_pkts"]), (181, 3))
        self.assertTrue(by[7]["loop_detected"])
        self.assertEqual(by[3]["stp_state"], "Forwarding")
        macs = {m["mac"]: m["port"] for m in snap["macs"]}
        self.assertEqual(macs["AA:BB:CC:DD:EE:07"], 9)          # ID de MAC 13 = frontal 9
        self.assertEqual(macs["B8:27:EB:00:00:01"], 3)

    def test_zx_relogin_when_session_expires_and_never_hits_dangerous_urls(self):
        ZXHandler.state.update(tick=0, temp=60, new_err=0, expire_once=True, hits=[])
        srv, host = serve(ZXHandler)
        d = sw.ZXDriver("zx", host, "admin", "pw", gap=0)
        d.snapshot(with_macs=False)
        srv.shutdown(); srv.server_close()
        self.assertEqual(ZXHandler.state["hits"].count("authorize"), 2)       # login inicial + relogin
        for bad in ZXHandler.state["hits"]: self.assertNotIn("clear", bad)
        with self.assertRaises(ValueError): d._open("clear_statistics.json")
        with self.assertRaises(ValueError): d._open("clear_statistics.json?x=1")

    def test_hc_snapshot_and_mac_clear_guard(self):
        HCHandler.posts.clear()
        srv, host = serve(HCHandler)
        d = sw.HCDriver("hc", host, "admin", "pw", gap=0)
        snap = d.snapshot()
        srv.shutdown(); srv.server_close()
        by = {p["port"]: p for p in snap["ports"]}
        self.assertEqual((by[1]["speed_mbps"], by[1]["link_up"], by[1]["rx_good_pkts"]), (2500, True, 200))
        self.assertEqual((by[3]["speed_mbps"], by[3]["rx_bad_pkts"], by[3]["tx_bad_pkts"]), (100, 2, 1))
        self.assertFalse(by[2]["link_up"])
        self.assertIsNone(by[1]["loop_detected"])
        self.assertEqual(snap["system"]["fw"], "V1.9.1")
        self.assertEqual({m["port"] for m in snap["macs"]}, {1, 3})
        for path, _ in HCHandler.posts: self.assertTrue(path.startswith("login.cgi") or path == "/login.cgi")
        with self.assertRaises(ValueError): d._fetch("mac.cgi?page=fwd_tbl", {"cmd": "mactblclr"})   # esto borraría la tabla MAC
        with self.assertRaises(ValueError): d._fetch("port.cgi", {"x": "1"})

    def test_hc_login_post_400_is_tolerated_when_the_cookie_is_enough(self):
        d = sw.HCDriver("hc", "192.0.2.4", "admin", "pw", gap=0)
        calls = []
        def fake(path, data=None):
            calls.append(path)
            if path == "login.cgi": raise OSError("el switch respondió HTTP 400 a POST /login.cgi")
            return "<html>" + "x" * 800 + "</html>"          # info.cgi con contenido real: sesión válida
        d._open = fake
        d.login()
        self.assertTrue(d.logged_in)
        fake2 = lambda path, data=None: (_ for _ in ()).throw(OSError("HTTP 400 login")) if path == "login.cgi" else "<script>location='/login.cgi'</script>"
        d2 = sw.HCDriver("hc", "192.0.2.4", "admin", "pw", gap=0); d2._open = fake2
        with self.assertRaises(RuntimeError) as cm: d2.login()
        self.assertIn("HTTP 400", str(cm.exception))

    def test_snmp_snapshot_has_bytes_and_bridge_mac(self):
        d = sw.SNMPDriver("tplink", "192.0.2.3", "public")
        d.snmp = FakeSNMP(snmp_data())
        snap = d.snapshot()
        self.assertEqual([p["port"] for p in snap["ports"]], [1, 2])          # el loopback (ifType 24) no cuenta
        p1 = snap["ports"][0]
        self.assertEqual((p1["rx_bytes"], p1["tx_bytes"], p1["speed_mbps"], p1["link_up"]), (10_000_000, 5_000_000, 1000, True))
        self.assertEqual(snap["system"]["mac"], "AA:BB:CC:DD:EE:20")
        self.assertEqual(snap["system"]["name"], "tplink")
        self.assertEqual([(m["mac"], m["port"], m["vlan"]) for m in snap["macs"]], [("AA:BB:CC:DD:EE:01", 1, 1)])

    def test_snmp_tplink_style_ifindex_and_vlan_interface(self):
        # Caso real (T2600G-18TS): ifIndex 49153…, nombre «gigabitEthernet 1/0/N : copper», una «Vlan-interface1» declarada ethernet,
        # y la tabla MAC usa los números 1…16 / EN: real case: ifIndex 49153…, vlan interface declared as ethernet, MAC table uses 1…16
        IF, IFX = "1.3.6.1.2.1.2.2.1", "1.3.6.1.2.1.31.1.1.1"
        d = {"1.3.6.1.2.1.1.1.0": b"JetStream", "1.3.6.1.2.1.1.3.0": 100, "1.3.6.1.2.1.1.5.0": b"T2600G"}
        d[f"{IF}.3.1"], d[f"{IF}.2.1"], d[f"{IFX}.1.1"] = 6, b"Vlan-interface1", b"Vlan-interface1"
        for n in (1, 2):
            i = 49152 + n
            d[f"{IF}.3.{i}"], d[f"{IF}.2.{i}"], d[f"{IFX}.1.{i}"] = 6, b"x", f"gigabitEthernet 1/0/{n} : copper".encode()
            d[f"{IF}.7.{i}"], d[f"{IF}.8.{i}"], d[f"{IFX}.15.{i}"] = 1, 1, 1000
            d[f"1.3.6.1.2.1.17.1.4.1.2.{i}"] = i
        d["1.3.6.1.2.1.17.7.1.2.2.1.2.1.170.187.204.221.238.2"] = 2
        drv = sw.SNMPDriver("t", "192.0.2.3", "public"); drv.snmp = FakeSNMP(d)
        snap = drv.snapshot()
        self.assertEqual([p["port"] for p in snap["ports"]], [1, 2])
        self.assertEqual(snap["macs"][0]["port"], 2)

    def test_every_driver_has_the_same_shape(self):
        d = sw.SNMPDriver("t", "192.0.2.3", "public"); d.snmp = FakeSNMP(snmp_data())
        keys = {"port", "admin_up", "link_up", "link", "speed_mbps", "rx_good_pkts", "tx_good_pkts", "rx_bad_pkts", "tx_bad_pkts", "loop_detected", "stp_state"}
        for p in d.snapshot()["ports"]: self.assertTrue(keys <= set(p), keys - set(p))


# ---------------------------------------------------------------- Gestor
def mk_snap(sid_name, ts, ports, mac="AA:BB:CC:DD:EE:00", macs=None, temp=None):
    return {"switch": sid_name, "driver": "zx", "host": "x", "timestamp": ts, "scrape_seconds": 1.0,
            "system": {"model": "M", "mac": mac, "temperature_c": temp, "fw": "1"}, "ports": ports, "macs": macs}

def mk_port(n, up=True, rx=0, tx=0, rxe=0, txe=0, loop=None, rxb=None, txb=None):
    return {"port": n, "admin_up": True, "link_up": up, "link": "1000Full" if up else "Link Down", "speed_mbps": 1000 if up else 0,
            "rx_good_pkts": rx, "tx_good_pkts": tx, "rx_bad_pkts": rxe, "tx_bad_pkts": txe, "loop_detected": loop, "stp_state": None,
            "rx_bytes": rxb, "tx_bytes": txb}


class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.events, self.seen = [], {}
        def changed(k, st):
            old = self.seen.get(k); self.seen[k] = st
            return None if old is None or old == st else (old, st)
        self.m = sw.Manager(self.d, hooks={"event": lambda mod, lv, tx, k=None, **p: self.events.append((lv, k, p)), "changed": changed,
                                           "hosts": lambda: {"b827eb000001": {"ip": "192.0.2.50", "name": "Pi-hole"}}})
        self.m.reconcile = lambda: None            # sin hilos: se alimenta con _ingest
        self.m._db_init()

    def add(self, name="zx310s", driver="zx"):
        body = {"name": name, "driver": driver, "host": "192.0.2.6", "user": "admin", "password": "secreto"} if driver != "snmp" else \
               {"name": name, "driver": "snmp", "host": "192.0.2.3", "community": "public"}
        return self.m.save_switch(body)

    def feed(self, sid, snap, macs=True):
        cfg = self.m._find(sid)
        self.m._ingest(sid, cfg, snap, macs)

    def test_config_is_private_and_never_leaks_secrets(self):
        out = self.add()
        self.assertNotIn("password", out); self.assertTrue(out["has_password"])
        self.assertNotIn("secreto", json.dumps(self.m.list_config()))
        self.assertEqual(stat.S_IMODE(os.stat(os.path.join(self.d, "switches.json")).st_mode), 0o600)
        # editar sin contraseña conserva la guardada
        self.m.save_switch({"id": out["id"], "name": "zx310s", "host": "192.0.2.7"})
        self.assertEqual(self.m._find(out["id"])["password"], "secreto")
        self.assertEqual(self.m._find(out["id"])["host"], "192.0.2.7")

    def test_validation(self):
        bad = [{"name": "", "driver": "zx", "host": "h", "password": "p"}, {"name": "ok", "driver": "telnet", "host": "h"},
               {"name": "ok", "driver": "zx", "host": "a b", "password": "p"}, {"name": "ok", "driver": "zx", "host": "h/x", "password": "p"},
               {"name": "ok", "driver": "zx", "host": "h"}, {"name": "ok", "driver": "snmp", "host": "h:99", "community": "c"},
               {"name": "ok", "driver": "snmp", "host": "h", "community": "c", "port": 70000}]
        for b in bad:
            with self.assertRaises(ValueError, msg=b): self.m.save_switch(b)
        self.add()
        with self.assertRaises(ValueError): self.add()              # nombre repetido

    def test_rates_counter_reset_and_new_errors(self):
        sid = self.add()["id"]
        t = 1_000_000.0
        self.feed(sid, mk_snap("zx310s", t, [mk_port(1, rx=1000, tx=500, rxe=5)]))
        self.feed(sid, mk_snap("zx310s", t + 60, [mk_port(1, rx=7000, tx=3500, rxe=5)]))
        p = self.m.state()["switches"][0]["ports"][0]
        self.assertAlmostEqual(p["rx_pps"], 100.0); self.assertAlmostEqual(p["tx_pps"], 50.0)
        self.assertEqual(p["err_1h"], 0)                            # los 5 errores viejos no cuentan como nuevos
        self.assertFalse([e for e in self.events if e[1] == "sw_err"])
        self.feed(sid, mk_snap("zx310s", t + 120, [mk_port(1, rx=8000, tx=4000, rxe=9)]))
        p = self.m.state()["switches"][0]["ports"][0]
        self.assertEqual(p["err_1h"], 4); self.assertEqual(p["flag"], "warn")
        ev = [e for e in self.events if e[1] == "sw_err"]
        self.assertEqual(len(ev), 1); self.assertEqual(ev[0][2]["d"], 4)
        # más errores a los 60 s: el aviso se limita a uno cada 10 min
        self.feed(sid, mk_snap("zx310s", t + 180, [mk_port(1, rx=9000, tx=4500, rxe=12)]))
        self.assertEqual(len([e for e in self.events if e[1] == "sw_err"]), 1)
        # reinicio del equipo: los contadores bajan → sin tasa, sin errores negativos
        self.feed(sid, mk_snap("zx310s", t + 240, [mk_port(1, rx=10, tx=5, rxe=0)]))
        p = self.m.state()["switches"][0]["ports"][0]
        self.assertIsNone(p["rx_pps"]); self.assertGreaterEqual(p["err_1h"], 0)

    def test_bytes_become_bits_per_second(self):
        sid = self.add("tplink", "snmp")["id"]
        t = 2_000_000.0
        self.feed(sid, mk_snap("tplink", t, [mk_port(1, rxb=0, txb=0)]))
        self.feed(sid, mk_snap("tplink", t + 10, [mk_port(1, rxb=1_250_000, txb=250_000)]))
        s = self.m.state()["switches"][0]
        self.assertTrue(s["has_bytes"])
        self.assertAlmostEqual(s["ports"][0]["rx_bps"], 1_000_000.0); self.assertAlmostEqual(s["ports"][0]["tx_bps"], 200_000.0)

    def test_temperature_alert_levels_and_events(self):
        sid = self.add()["id"]
        t = 3_000_000.0
        self.feed(sid, mk_snap("zx310s", t, [mk_port(1)], temp=60))
        self.assertEqual(self.m.state()["switches"][0]["temp_level"], "ok")
        self.feed(sid, mk_snap("zx310s", t + 60, [mk_port(1)], temp=74))
        s = self.m.state()["switches"][0]
        self.assertEqual(s["temp_level"], "warn"); self.assertIn("temp", [a["k"] for a in s["alerts"]])
        self.assertEqual([e[1] for e in self.events if e[1] == "sw_temp"], ["sw_temp"])
        self.feed(sid, mk_snap("zx310s", t + 120, [mk_port(1)], temp=85))
        self.assertEqual(self.m.state()["switches"][0]["temp_level"], "crit")
        self.feed(sid, mk_snap("zx310s", t + 180, [mk_port(1)], temp=50))
        self.assertIn("sw_temp_ok", [e[1] for e in self.events])
        self.assertEqual(self.m.summary()["lv"], "ok")

    def test_switch_down_needs_two_failures_and_recovers(self):
        sid = self.add()["id"]; cfg = self.m._find(sid)
        self.feed(sid, mk_snap("zx310s", 4_000_000.0, [mk_port(1)]))
        self.m._fail(sid, cfg, OSError("timeout"))
        self.assertTrue(self.m.state()["switches"][0]["online"]); self.assertFalse([e for e in self.events if e[1] == "sw_down"])
        self.m._fail(sid, cfg, OSError("timeout"))
        s = self.m.state()["switches"][0]
        self.assertFalse(s["online"]); self.assertEqual(s["alerts"][0]["k"], "down")
        self.assertEqual(self.m.summary()["lv"], "crit")
        self.assertEqual([e[1] for e in self.events if e[1] == "sw_down"], ["sw_down"])
        self.feed(sid, mk_snap("zx310s", 4_000_100.0, [mk_port(1)]))
        self.assertTrue(self.m.state()["switches"][0]["online"]); self.assertIn("sw_up", [e[1] for e in self.events])

    def test_topology_links_and_loop_is_ignored_on_uplinks(self):
        a, b = self.add("zx310s")["id"], self.add("hc218as", "hc")["id"]
        t = 5_000_000.0
        self.feed(a, mk_snap("zx310s", t - 60, [mk_port(8, loop=False)]))     # primera lectura: solo se memoriza, no genera eventos
        # el ZX ve la MAC del HC en el puerto 7 y marca «loop» ahí; el HC ve la MAC del ZX en su puerto 1
        self.feed(a, mk_snap("zx310s", t, [mk_port(3), mk_port(7, loop=True), mk_port(8, loop=True)], mac="AA:BB:CC:DD:EE:00",
                             macs=[{"mac": "B8:27:EB:00:00:01", "port": 3, "vlan": 1}, {"mac": "AA:BB:CC:DD:FF:07", "port": 7, "vlan": 1}]))
        self.feed(b, mk_snap("hc218as", t, [mk_port(1), mk_port(3)], mac="AA:BB:CC:DD:FF:00",
                             macs=[{"mac": "AA:BB:CC:DD:EE:01", "port": 1, "vlan": 1}]))
        st = self.m.state()
        zx = next(s for s in st["switches"] if s["name"] == "zx310s")
        p = {x["port"]: x for x in zx["ports"]}
        self.assertEqual((p[7]["link_to"], p[7]["flag"], p[7]["uplink"]), ("hc218as", "uplink", True))
        self.assertEqual(p[8]["flag"], "loop")                       # puerto 8: sin vecino detectado → sigue marcado como loop
        self.assertEqual(p[3]["neighbors"][0]["name"], "Pi-hole"); self.assertEqual(p[3]["neighbors"][0]["ip"], "192.0.2.50")
        self.assertEqual(st["edges"], [{"a": "zx310s", "a_port": 7, "b": "hc218as", "b_port": 1}] if st["edges"][0]["a"] == "zx310s"
                         else [{"a": "hc218as", "a_port": 1, "b": "zx310s", "b_port": 7}])
        self.assertEqual([e for e in self.events if e[1] == "sw_loop"][0][2]["p"], 8)
        # marcar el puerto 8 como uplink a mano lo saca de las alertas
        self.m.set_port_meta(a, 8, "→ NAS", True)
        zx = next(s for s in self.m.state()["switches"] if s["name"] == "zx310s")
        p8 = next(x for x in zx["ports"] if x["port"] == 8)
        self.assertEqual((p8["flag"], p8["label"]), ("uplink", "→ NAS"))
        self.assertNotIn("loop", [al["k"] for al in zx["alerts"]])

    def test_history_rollup_and_range_reduction(self):
        sid = self.add()["id"]
        now = 10_000_000
        for i in range(0, 60 * 24 * 4):                              # 4 días de muestras de 1 min
            ts = now - i * 60
            self.m._db_write(sid, ts, mk_snap("zx310s", ts, [mk_port(1, rx=i)], temp=50 + (i % 10)),
                             {1: {"rx_pps": 10.0, "tx_pps": 5.0, "rx_bps": None, "tx_bps": None}})
        raw = self.m.history(sid, "1d", 1, now=now)
        self.assertLessEqual(len(raw["sys"]), 1440); self.assertGreater(len(raw["port"]), 100)
        self.m.rollup(now=now)
        con = sqlite3.connect(os.path.join(self.d, "switches.db"))
        n_raw = con.execute("SELECT COUNT(*) FROM sw_sys").fetchone()[0]; n_agg = con.execute("SELECT COUNT(*) FROM sw_sys_agg").fetchone()[0]
        con.close()
        self.assertLessEqual(n_raw, 48 * 60 + 15); self.assertGreater(n_agg, 24 * 4)       # lo viejo quedó resumido cada 15 min
        week = self.m.history(sid, "1w", 1, now=now)
        self.assertGreater(len(week["sys"]), 200)
        self.assertTrue(all(week["sys"][i]["ts"] < week["sys"][i + 1]["ts"] for i in range(len(week["sys"]) - 1)))
        self.assertAlmostEqual(week["port"][-1]["rxp"], 10.0)
        everything = self.m.history(sid, "all", None, now=now)
        self.assertEqual(everything["port"], [])
        self.assertLessEqual(len(everything["sys"]), 4320)

    def test_delete_removes_history_and_rest_still_works(self):
        a, b = self.add("one")["id"], self.add("two")["id"]
        self.m._db_write(a, 1_000_000, mk_snap("one", 1_000_000, [mk_port(1)]), {}); self.m._db_write(b, 1_000_000, mk_snap("two", 1_000_000, [mk_port(1)]), {})
        self.m.delete_switch(a)
        self.assertEqual(self.m.history(a, "all", None, now=1_000_100)["sys"], [])
        self.assertEqual(len(self.m.history(b, "all", None, now=1_000_100)["sys"]), 1)
        self.assertEqual([s["name"] for s in self.m.list_config()["switches"]], ["two"])

    def test_poll_interval_limits(self):
        for bad in (5, 4000, "x"):
            with self.assertRaises(ValueError): self.m.set_poll(bad)
        self.m.set_poll(120); self.assertEqual(sw.Manager(self.d).poll_seconds(), 120)         # se conserva al reiniciar

    def test_real_threads_poll_a_simulated_zx(self):
        ZXHandler.state.update(tick=0, temp=61, new_err=0, expire_once=False, hits=[])
        srv, host = serve(ZXHandler)
        m = sw.Manager(tempfile.mkdtemp(), hooks={})
        orig = sw.build_driver
        sw.build_driver = lambda cfg: sw.ZXDriver(cfg["name"], cfg["host"], cfg["user"], cfg["password"], gap=0)
        try:
            m.start()
            m.save_switch({"name": "zx", "driver": "zx", "host": host, "user": "admin", "password": "pw"})
            for _ in range(100):
                s = m.state()["switches"]
                if s and s[0]["online"]: break
                time.sleep(0.1)
            else: self.fail("el hilo no consultó el switch")
            self.assertEqual(s[0]["ports_total"], 10); self.assertEqual(s[0]["system"]["temperature_c"], 61.0)
        finally:
            sw.build_driver = orig; m.stop(); srv.shutdown(); srv.server_close()


class Api(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        os.environ["LABTOWER_DATA"] = cls.tmp
        cls.net = support.load("net-monitor/server.py")
        cls.net._sw_mgr = sw.Manager(cls.tmp, hooks={"hosts": cls.net._sw_hosts})
        cls.net._sw_mgr.reconcile = lambda: None
        cls.net._sw_mgr._db_init()
        cls.srv = support.Server(cls.net.H)
        cls.admin = support.make_user("sw_admin", support.ADMIN)
        cls.ro = support.make_user("sw_ro", support.READONLY)
        cls.none = support.make_user("sw_none", support.NONE)

    def call(self, method, path, body=None, token=None):
        r = self.srv.call(method, path, body, token=token)
        return r

    def test_permissions(self):
        body = {"name": "api-sw", "driver": "snmp", "host": "192.0.2.9", "community": "secret-community"}
        self.assertEqual(self.call("GET", "/api/switches", token=self.none)[0], 401)
        self.assertEqual(self.call("GET", "/api/switches")[0], 401)
        self.assertEqual(self.call("GET", "/api/switches", token=self.ro)[0], 200)
        self.assertEqual(self.call("POST", "/api/switches/save", body, token=self.ro)[0], 403)
        self.assertEqual(self.call("POST", "/api/switches/delete", {"id": "x"}, token=self.ro)[0], 403)
        self.assertEqual(self.call("POST", "/api/switches/test", body, token=self.ro)[0], 403)
        code, out = self.call("POST", "/api/switches/save", body, token=self.admin)
        self.assertEqual(code, 200); sid = out["switch"]["id"]
        for tok in (self.ro, self.admin):
            raw = json.dumps(self.call("GET", "/api/switches/config", token=tok)[1])
            self.assertNotIn("secret-community", raw)
        self.assertEqual(self.call("GET", f"/api/switches/{sid}/history?range=1d", token=self.ro)[0], 200)
        self.assertEqual(self.call("GET", f"/api/switches/{sid}/history?range=zz", token=self.ro)[0], 400)
        self.assertEqual(self.call("GET", f"/api/switches/{sid}/history?range=1d&port=1;drop", token=self.ro)[0], 400)
        self.assertEqual(self.call("POST", "/api/switches/refresh", {}, token=self.ro)[0], 200)
        self.assertEqual(self.call("POST", "/api/switches/save", {"name": "bad name!!", "driver": "zx", "host": "h", "password": "p"}, token=self.admin)[0], 400)
        self.assertEqual(self.call("POST", "/api/switches/nope", {}, token=self.admin)[0], 404)
        self.assertEqual(self.call("POST", "/api/switches/delete", {"id": sid}, token=self.admin)[0], 200)
        self.assertEqual(self.call("GET", "/api/switches/summary", token=self.ro)[1]["switches"], [])


if __name__ == "__main__":
    unittest.main()
