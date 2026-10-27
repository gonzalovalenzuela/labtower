"""NAS Monitor: lectura SNMP (con net-snmp simulado y con un snmpd real si existe), validación, secretos, permisos y alertas."""
import json, os, shutil, socket, stat, subprocess, sys, tempfile, textwrap, time, unittest
from pathlib import Path
from tests import support
from tests.support import ADMIN, READONLY, NONE

m = support.load("nas-monitor/server.py")
ROOT = Path(__file__).resolve().parents[1]

# ── net-snmp simulado: scripts «snmpget» y «snmpbulkwalk» que imprimen el formato real de net-snmp (-On) y anotan cómo los llamaron ──
FAKE = textwrap.dedent('''\
    #!%(py)s
    import json, os, sys
    tool = os.path.basename(sys.argv[0]); a = sys.argv[1:]
    d = os.environ.get("SNMPCONFPATH", "")
    conf = open(os.path.join(d, "snmp.conf")).read() if d and os.path.exists(os.path.join(d, "snmp.conf")) else None
    log = os.environ.get("FAKE_LOG")
    if log:
        with open(log, "a") as f:
            f.write(json.dumps({"tool": tool, "argv": a, "conf": conf, "dir_mode": oct(os.stat(d).st_mode & 0o777) if d else None,
                                "conf_mode": oct(os.stat(os.path.join(d, "snmp.conf")).st_mode & 0o777) if conf else None, "dir": d}) + "\\n")
    if os.environ.get("FAKE_FAIL"):
        sys.stderr.write(os.environ["FAKE_FAIL"] + "\\n"); sys.exit(1)
    step = int(open(os.environ["FAKE_STEP"]).read()) if os.environ.get("FAKE_STEP") else 0
    B = ".1.3.6.1.4.1.6574."
    T = {
     ".1.3.6.1.2.1.1.1.0": 'STRING: "Linux DS-FAKE 4.4"', ".1.3.6.1.2.1.1.3.0": "Timeticks: (8640000) 1 day, 0:00:00.00",
     ".1.3.6.1.2.1.1.5.0": 'STRING: "DS-FAKE"', ".1.3.6.1.2.1.25.1.1.0": "Timeticks: (17280000) 2 days, 0:00:00.00",
     ".1.3.6.1.4.1.2021.11.9.0": "INTEGER: 10", ".1.3.6.1.4.1.2021.11.10.0": "INTEGER: 5", ".1.3.6.1.4.1.2021.11.11.0": "INTEGER: 85",
     ".1.3.6.1.4.1.2021.4.5.0": "INTEGER: 8000000", ".1.3.6.1.4.1.2021.4.6.0": "INTEGER: 4000000", ".1.3.6.1.4.1.2021.4.14.0": "INTEGER: 500000",
     ".1.3.6.1.4.1.2021.4.15.0": "INTEGER: 1500000", ".1.3.6.1.4.1.2021.4.3.0": "INTEGER: 2000000", ".1.3.6.1.4.1.2021.4.4.0": "INTEGER: 1900000",
     ".1.3.6.1.4.1.2021.10.1.3.1": 'STRING: 0.50', ".1.3.6.1.4.1.2021.10.1.3.2": 'STRING: 0.40', ".1.3.6.1.4.1.2021.10.1.3.3": 'STRING: 0.30',
     B+"1.1.0": "INTEGER: 1", B+"1.2.0": "INTEGER: 43", B+"1.3.0": "INTEGER: 1", B+"1.4.1.0": "INTEGER: 1", B+"1.4.2.0": "INTEGER: 1",
     B+"1.5.1.0": 'STRING: "DS918+"', B+"1.5.2.0": 'STRING: "SN123"', B+"1.5.3.0": 'STRING: "DSM 7.2-64570"', B+"1.5.4.0": "INTEGER: 1",
     B+"2.1.1.2.1": 'STRING: "Disk 1"', B+"2.1.1.3.1": 'STRING: "WD40 "', B+"2.1.1.4.1": 'STRING: "SATA"', B+"2.1.1.5.1": "INTEGER: 1", B+"2.1.1.6.1": "INTEGER: 61",
     B+"2.1.1.2.2": 'STRING: "Disk 2"', B+"2.1.1.3.2": 'STRING: "WD40"', B+"2.1.1.4.2": 'STRING: "SATA"', B+"2.1.1.5.2": "INTEGER: 5", B+"2.1.1.6.2": "INTEGER: 38",
     B+"3.1.1.2.1": 'STRING: "Volume 1"', B+"3.1.1.3.1": "INTEGER: 1", B+"3.1.1.4.1": "Counter64: 500", B+"3.1.1.5.1": "Counter64: 1000",
     B+"3.1.1.2.2": 'STRING: "Volume 2"', B+"3.1.1.3.2": "INTEGER: 12", B+"3.1.1.4.2": "Counter64: 40", B+"3.1.1.5.2": "Counter64: 1000",
     B+"4.1.1.0": 'STRING: "UPS-X"', B+"4.2.1.0": 'STRING: "OL"', B+"4.3.1.1.0": "Gauge32: 100",
     B+"101.1.1.2.1": 'STRING: "sda"', B+"101.1.1.8.1": "INTEGER: 12",
     ".1.3.6.1.2.1.31.1.1.1.1.1": 'STRING: "lo"', ".1.3.6.1.2.1.31.1.1.1.6.1": "Counter64: 5", ".1.3.6.1.2.1.31.1.1.1.10.1": "Counter64: 5",
     ".1.3.6.1.2.1.31.1.1.1.1.2": 'STRING: "eth0"', ".1.3.6.1.2.1.31.1.1.1.6.2": "Counter64: %%d" %% (1000000 + step * 1250000),
     ".1.3.6.1.2.1.31.1.1.1.10.2": "Counter64: %%d" %% (2000000 + step * 625000), ".1.3.6.1.2.1.31.1.1.1.15.2": "Gauge32: 1000",
     ".1.3.6.1.2.1.31.1.1.1.1.3": 'STRING: "docker0"', ".1.3.6.1.2.1.31.1.1.1.6.3": "Counter64: 9", ".1.3.6.1.2.1.31.1.1.1.10.3": "Counter64: 9",
    }
    oids = [x if x.startswith(".") else "." + x for x in a[[i for i, x in enumerate(a) if x.startswith("udp")][0] + 1:]]
    if tool == "snmpget":
        for o in oids:
            print(o + " = " + T[o] if o in T else o + " = No Such Object available on this agent at this OID")
    else:
        for o in oids:
            for k in sorted(T, key=lambda s: [int(x) for x in s.strip(".").split(".")]):
                if k.startswith(o + "."): print(k + " = " + T[k])
''')

def fake_bin(tmp):
    d = Path(tmp, "bin"); d.mkdir()
    for tool in ("snmpget", "snmpbulkwalk", "snmpwalk"):
        p = d / tool; p.write_text(FAKE % {"py": sys.executable}); p.chmod(0o755)
    return str(d)

CFG3 = {"name": "n", "host": "192.0.2.20", "port": 161, "version": "3", "user": "nasuser", "level": "authPriv", "auth_proto": "SHA",
        "auth_pass": "S3cretAuthKey!", "priv_proto": "AES", "priv_pass": "S3cretPrivKey!", "timeout": 3}

class Parse(unittest.TestCase):
    def test_types_and_noise(self):
        txt = textwrap.dedent('''\
            .1.3.6.1.2.1.1.5.0 = STRING: "DS-X"
            .1.3.6.1.2.1.1.3.0 = Timeticks: (123456) 0:20:34.56
            .1.3.6.1.4.1.6574.1.2.0 = INTEGER: 41
            .1.3.6.1.4.1.6574.3.1.1.5.1 = Counter64: 14500000000000
            .1.3.6.1.4.1.2021.4.5.0 = Gauge32: 7
            .1.3.6.1.4.1.6574.1.5.1.0 = No Such Object available on this agent at this OID
            .1.3.6.1.2.1.1.1.0 = STRING: "first line
            continuation without an OID
            Timeout: No Response from 192.0.2.1
            .1.3.6.1.2.1.2.2.1.6.1 = Hex-STRING: 00 11 22
        ''')
        v = m.parse(txt)
        self.assertEqual(v["1.3.6.1.2.1.1.5.0"], "DS-X")
        self.assertAlmostEqual(v["1.3.6.1.2.1.1.3.0"], 1234.56)
        self.assertEqual(v["1.3.6.1.4.1.6574.1.2.0"], 41)
        self.assertEqual(v["1.3.6.1.4.1.6574.3.1.1.5.1"], 14500000000000)
        self.assertNotIn("1.3.6.1.4.1.6574.1.5.1.0", v)          # «No Such Object» no entra
        self.assertNotIn("1.3.6.1.2.1.2.2.1.6.1", v)             # tipos que no se usan se ignoran
        self.assertEqual(m.parse(""), {})

class Validate(unittest.TestCase):
    def ok(self, **kw): return m.validate({**CFG3, **kw})
    def bad(self, **kw):
        with self.assertRaises(ValueError, msg=str(kw)): m.validate({**CFG3, **kw})

    def test_valid_v3_and_v2c(self):
        self.assertEqual(self.ok()["version"], "3")
        c = m.validate({"name": "a", "host": "nas.lan", "version": "2c", "community": "pub"})
        self.assertEqual((c["version"], c["port"], c["timeout"]), ("2c", 161, 5))

    def test_rejects_bad_input(self):
        self.bad(name=""); self.bad(name="x" * 61); self.bad(name="a\nb")
        self.bad(host=""); self.bad(host="-oProxyCommand=x"); self.bad(host="a b"); self.bad(host="a;b")
        self.bad(port=0); self.bad(port=70000); self.bad(port="x"); self.bad(timeout=0); self.bad(timeout=99)
        self.bad(version="1"); self.bad(version="4")
        self.bad(user=""); self.bad(user="a b"); self.bad(level="bogus"); self.bad(auth_proto="CRC"); self.bad(priv_proto="ROT13")
        self.bad(auth_pass="short"); self.bad(priv_pass="short"); self.bad(auth_pass="has space 1234"); self.bad(auth_pass="x\ny" * 5)
        with self.assertRaises(ValueError): m.validate({"name": "a", "host": "h", "version": "2c", "community": ""})

    def test_levels_need_only_their_secrets(self):
        self.ok(level="noAuthNoPriv", auth_pass="", priv_pass="")
        self.ok(level="authNoPriv", priv_pass="")
        self.bad(level="authPriv", priv_pass="")

    def test_empty_secret_keeps_the_stored_one(self):
        cur = m.validate(CFG3)
        new = m.validate({"name": "n2", "host": "192.0.2.20", "auth_pass": "", "priv_pass": None, "user": "other"}, cur)
        self.assertEqual((new["auth_pass"], new["priv_pass"], new["user"], new["name"]), (CFG3["auth_pass"], CFG3["priv_pass"], "other", "n2"))
        new = m.validate({"auth_pass": "BrandNewKey123"}, cur)
        self.assertEqual(new["auth_pass"], "BrandNewKey123")

    def test_public_view_has_no_secrets(self):
        p = m.public({**m.validate(CFG3), "id": "i"})
        for k in m.SNMP_SECRETS: self.assertNotIn(k, p)
        self.assertTrue(p["has_auth_pass"] and p["has_priv_pass"] and not p["has_community"])
        self.assertNotIn("S3cret", json.dumps(p))

class Collect(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="nas-t-")
        self.old_path = os.environ["PATH"]
        os.environ["PATH"] = fake_bin(self.tmp) + os.pathsep + self.old_path
        os.environ["FAKE_LOG"] = os.path.join(self.tmp, "calls.log"); os.environ["FAKE_STEP"] = os.path.join(self.tmp, "step"); self.step(0)
    def tearDown(self):
        os.environ["PATH"] = self.old_path
        for k in ("FAKE_LOG", "FAKE_STEP", "FAKE_FAIL"): os.environ.pop(k, None)
        shutil.rmtree(self.tmp, ignore_errors=True)
    def step(self, n): Path(self.tmp, "step").write_text(str(n))
    def calls(self): return [json.loads(l) for l in Path(self.tmp, "calls.log").read_text().splitlines()]

    def test_full_reading(self):
        s = m.collect(m.validate(CFG3), {})
        sy = s["system"]
        self.assertEqual((sy["model"], sy["dsm"], sy["temp"], sy["name"]), ("DS918+", "DSM 7.2-64570", 43, "DS-FAKE"))
        self.assertEqual(sy["uptime"], 172800)                                   # hrSystemUptime manda sobre sysUpTime
        self.assertEqual(s["cpu"]["pct"], 15.0)
        self.assertEqual(s["mem"]["total"], 8000000 * 1024)
        self.assertEqual(s["mem"]["used"], (8000000 - 4000000 - 500000 - 1500000) * 1024)   # sin buffers ni caché
        self.assertEqual([d["lv"] for d in s["disks"]], ["ok", "crit"])
        self.assertEqual(s["disks"][0]["model"], "WD40")                          # sin espacios sobrantes
        self.assertEqual([(r["name"], r["lv"], r["pct"]) for r in s["raids"]], [("Volume 1", "ok", 50.0), ("Volume 2", "crit", 96.0)])
        self.assertEqual(s["ups"]["status"], "OL"); self.assertEqual(s["io"], [{"dev": "sda", "load": 12}])
        self.assertEqual([n["name"] for n in s["net"]], ["eth0"])                 # sin lo ni docker0
        self.assertTrue(s["synology"]); self.assertEqual(s["warnings"], [])

    def test_alerts(self):
        types = {(a["type"], a.get("item")) for a in m.collect(m.validate(CFG3), {})["alerts"]}
        self.assertIn(("disk", "Disk 2"), types); self.assertIn(("raid", "Volume 2"), types); self.assertIn(("vol_full", "Volume 2"), types)
        self.assertIn(("disk_temp", "Disk 1"), types); self.assertIn(("upgrade", None), types)
        self.assertNotIn(("raid", "Volume 1"), types)

    def test_network_rate_from_two_readings(self):
        prev = {}; m.collect(m.validate(CFG3), prev)
        first = m.collect(m.validate(CFG3), prev)["net"][0]
        self.assertEqual((first["rx"], first["tx"]), (None, None) if False else (0, 0))      # mismo contador: 0 bit/s
        self.step(1); time.sleep(1.1)
        e = m.collect(m.validate(CFG3), prev)["net"][0]
        self.assertTrue(500_000 < e["rx"] < 12_000_000, e)                         # ~1 250 000 bytes en ~1.1 s
        self.assertTrue(e["tx"] and e["tx"] < e["rx"])
        self.step(0); time.sleep(0.2)                                              # el contador «retrocede» (reinicio del NAS): sin velocidad
        self.assertEqual(m.collect(m.validate(CFG3), prev)["net"][0]["rx"], None)

    def test_secrets_never_on_the_command_line_and_conf_is_private(self):
        m.collect(m.validate(CFG3), {})
        calls = self.calls(); self.assertEqual({c["tool"] for c in calls}, {"snmpget", "snmpbulkwalk"})
        for c in calls:
            self.assertNotIn("S3cret", " ".join(c["argv"]), "las claves no pueden verse en «ps»")
            self.assertEqual((c["dir_mode"], c["conf_mode"]), ("0o700", "0o600"))
            for line in ("defSecurityName nasuser", "defSecurityLevel authPriv", "defAuthType SHA", "defAuthPassphrase S3cretAuthKey!",
                         "defPrivType AES", "defPrivPassphrase S3cretPrivKey!"):
                self.assertIn(line, c["conf"])
            self.assertIn("-v3", c["argv"]); self.assertIn("udp:192.0.2.20:161", c["argv"])
            self.assertFalse(os.path.exists(c["dir"]), "el snmp.conf temporal debe borrarse")

    def test_v2c_and_ipv6_targets(self):
        m.collect(m.validate({"name": "a", "host": "fd00::5", "version": "2c", "community": "pubcomm"}), {})
        for c in self.calls():
            self.assertIn("-v2c", c["argv"]); self.assertIn("udp6:[fd00::5]:161", c["argv"])
            self.assertEqual(c["conf"].strip(), "defCommunity pubcomm"); self.assertNotIn("pubcomm", " ".join(c["argv"]))

    def test_unreachable_nas_raises(self):
        os.environ["FAKE_FAIL"] = "snmpget: Timeout: No Response from 192.0.2.20"
        with self.assertRaisesRegex(m.SnmpError, "No Response"): m.collect(m.validate(CFG3), {})
        os.environ["FAKE_FAIL"] = "snmpget: Authentication failure (incorrect password, community or key)"
        with self.assertRaisesRegex(m.SnmpError, "Authentication failure"): m.test_connection(m.validate(CFG3))

    def test_connection_test(self):
        r = m.test_connection(m.validate(CFG3))
        self.assertEqual((r["model"], r["dsm"], r["synology"]), ("DS918+", "DSM 7.2-64570", True))

class AlertRules(unittest.TestCase):
    def snap(self, **kw):
        s = {"system": {"status": 1, "power": 1, "fan_sys": 1, "fan_cpu": 1, "temp": 40, "upgrade": 2}, "cpu": {"pct": 10}, "mem": {"pct": 30},
             "disks": [], "raids": [], "net": [], "io": [], "ups": None}
        s.update(kw); return s
    def test_quiet_when_all_is_fine(self): self.assertEqual(m.compute_alerts(self.snap()), [])
    def test_thresholds(self):
        a = {(x["type"], x["lv"]) for x in m.compute_alerts(self.snap(
            system={"status": 2, "power": 2, "fan_sys": 2, "fan_cpu": 1, "temp": 75, "upgrade": 1}, cpu={"pct": 90}, mem={"pct": 95},
            raids=[{"name": "V", "lv": "ok", "status": 1, "pct": 96.0}]))}
        for want in [("system", "crit"), ("power", "crit"), ("fan", "warn"), ("temp", "warn"), ("cpu", "warn"), ("mem", "warn"), ("vol_full", "crit"), ("upgrade", "info")]:
            self.assertIn(want, a)
        self.assertEqual([x["lv"] for x in m.compute_alerts(self.snap(raids=[{"name": "V", "lv": "info", "status": 8, "pct": 92.0}]))], ["warn"])   # verificando paridad: solo el aviso de espacio

    def test_full_storage_pool_is_not_an_alert(self):
        pool = {"name": "Storage Pool 1", "lv": "ok", "status": 1, "pct": 99.0, "pool": True}
        self.assertEqual(m.compute_alerts(self.snap(raids=[pool])), [])
        self.assertEqual([x["type"] for x in m.compute_alerts(self.snap(raids=[{**pool, "lv": "crit", "status": 11}]))], ["raid"])   # su estado sí avisa
        self.assertTrue(m._POOL_RE.search("Storage Pool 2") and m._POOL_RE.search("Grupo de almacenamiento 1") and not m._POOL_RE.search("Volume 1"))

class Http(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        m.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.started = []; cls._ep, m.ensure_poller = m.ensure_poller, lambda n: cls.started.append(n["id"])
        cls.admin, cls.ro, cls.none = support.make_user("nadm", ADMIN), support.make_user("nro", READONLY), support.make_user("nnone", NONE)
        cls.srv = support.Server(m.H)
    @classmethod
    def tearDownClass(cls): m.ensure_poller = cls._ep; cls.srv.close()
    def setUp(self): m.save_nas([])

    def test_permissions(self):
        c = self.srv.call
        self.assertEqual(c("GET", "/api/nas")[0], 401); self.assertEqual(c("GET", "/api/nas", token=self.none)[0], 401)
        self.assertEqual(c("GET", "/api/nas", token=self.ro)[0], 200)
        body = {"name": "a", "host": "192.0.2.9", "user": "u", "auth_pass": "12345678", "priv_pass": "12345678"}
        for path, method in (("/api/nas", "POST"), ("/api/test", "POST")):
            self.assertEqual(c(method, path, body, token=self.ro)[0], 403, path); self.assertEqual(c(method, path, body)[0], 401, path)
        self.assertEqual(c("DELETE", "/api/nas/abc", token=self.ro)[0], 403)

    def test_create_edit_delete_and_secrets_stay_server_side(self):
        c = self.srv.call; body = {"name": "Main", "host": "192.0.2.9", "port": 161, "version": "3", "user": "u", "auth_pass": "AuthSecret99", "priv_pass": "PrivSecret99"}
        s, j = c("POST", "/api/nas", body, token=self.admin); self.assertEqual(s, 201, j)
        nid = j["nas"]["id"]; self.assertIn(nid, self.started); self.assertNotIn("Secret99", json.dumps(j))
        self.assertEqual(c("POST", "/api/nas", {**body, "name": "Dup"}, token=self.admin)[0], 409)
        s, j = c("GET", "/api/nas", token=self.ro); self.assertEqual(len(j["nas"]), 1)
        self.assertNotIn("Secret99", json.dumps(j)); self.assertTrue(j["nas"][0]["has_auth_pass"])
        s, j = c("POST", "/api/nas/" + nid, {"name": "Renamed", "auth_pass": ""}, token=self.admin); self.assertEqual(s, 200, j)
        stored = m.load_nas()[0]; self.assertEqual((stored["name"], stored["auth_pass"]), ("Renamed", "AuthSecret99"))
        self.assertEqual(oct(stat.S_IMODE(os.stat(m.DATA_FILE).st_mode)), "0o600")
        self.assertEqual(c("POST", "/api/nas/nope", {"name": "x"}, token=self.admin)[0], 404)
        self.assertEqual(c("DELETE", "/api/nas/" + nid, token=self.admin)[0], 200); self.assertEqual(m.load_nas(), [])
        self.assertEqual(c("DELETE", "/api/nas/" + nid, token=self.admin)[0], 404)

    def test_invalid_bodies(self):
        c = self.srv.call
        for bad in ({}, {"name": "a", "host": "-x", "user": "u"}, {"name": "a", "host": "h", "version": "9"}, {"name": "a", "host": "h", "user": "u", "port": 0}):
            self.assertEqual(c("POST", "/api/nas", bad, token=self.admin)[0], 400, bad)

    def test_connection_test_endpoint_uses_stored_secrets_for_empty_fields(self):
        tmp = tempfile.mkdtemp(); old = os.environ["PATH"]; log = os.path.join(tmp, "l")
        os.environ["PATH"] = fake_bin(tmp) + os.pathsep + old; os.environ["FAKE_LOG"] = log
        try:
            s, j = self.srv.call("POST", "/api/nas", {**CFG3, "name": "T", "host": "192.0.2.77"}, token=self.admin); nid = j["nas"]["id"]
            s, r = self.srv.call("POST", "/api/test", {"id": nid, "name": "T", "host": "192.0.2.77", "version": "3", "user": "nasuser", "auth_pass": "", "priv_pass": ""}, token=self.admin)
            self.assertEqual((s, r["ok"], r["model"]), (200, True, "DS918+"), r)
            self.assertIn("defAuthPassphrase S3cretAuthKey!", json.loads(Path(log).read_text().splitlines()[0])["conf"])
            os.environ["FAKE_FAIL"] = "snmpget: Authentication failure"
            s, r = self.srv.call("POST", "/api/test", {**CFG3, "host": "192.0.2.78"}, token=self.admin)
            self.assertEqual((s, r["ok"]), (200, False)); self.assertIn("Authentication failure", r["error"]); self.assertNotIn("S3cret", json.dumps(r))
        finally:
            os.environ["PATH"] = old; os.environ.pop("FAKE_LOG", None); os.environ.pop("FAKE_FAIL", None); shutil.rmtree(tmp, ignore_errors=True)

    def test_cross_site_post_is_blocked(self):
        s, _ = self.srv.call("POST", "/api/nas", {"name": "a", "host": "192.0.2.9", "user": "u"}, token=self.admin, headers={"Sec-Fetch-Site": "cross-site"})
        self.assertEqual(s, 403)

    def test_health_is_public_but_shows_levels_only(self):
        s, j = self.srv.call("GET", "/api/health"); self.assertIn(s, (200, 503)); self.assertNotIn("detail", json.dumps(j))

# ── Con un snmpd real (si está instalado): SNMPv3 authPriv y v2c de punta a punta, sin simulaciones ──
def free_udp_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p

@unittest.skipUnless(shutil.which("snmpd") and shutil.which("snmpget") and shutil.which("snmpbulkwalk"), "net-snmp (snmp y snmpd) no está instalado")
class RealSnmpd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="snmpd-"); cls.port = free_udp_port()
        fake = Path(cls.tmp, "fake_syno.py"); shutil.copyfile(ROOT / "tests/fixtures/fake_syno.py", fake); fake.chmod(0o755)
        conf = Path(cls.tmp, "snmpd.conf")
        conf.write_text(f"agentaddress udp:127.0.0.1:{cls.port}\nrocommunity simcomm 127.0.0.1 .1\n"
                        'createUser nasuser SHA "authpass123" AES "privpass123"\nrouser nasuser priv .1\n'
                        f"pass .1.3.6.1.4.1.6574 {fake}\nsysName DS-SIM\n")
        cls.proc = subprocess.Popen(["snmpd", "-f", "-C", "-c", str(conf), "-Lf", os.path.join(cls.tmp, "log"), "-p", os.path.join(cls.tmp, "pid")],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=dict(os.environ, SNMP_PERSISTENT_DIR=cls.tmp))
        cfg = m.validate({"name": "s", "host": "127.0.0.1", "port": cls.port, "version": "2c", "community": "simcomm", "timeout": 2})
        for _ in range(60):
            try:
                if m.snmp_get(cfg, ["1.3.6.1.2.1.1.5.0"]): break
            except Exception: pass
            time.sleep(0.5)
        else:
            cls.proc.kill(); raise unittest.SkipTest("snmpd no arrancó en este entorno")
    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        try: cls.proc.wait(5)
        except Exception: cls.proc.kill()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def check(self, cfg):
        s = m.collect(cfg, {})
        self.assertEqual((s["system"]["model"], s["system"]["name"], s["system"]["temp"]), ("DS920+", "DS-SIM", 41))
        self.assertEqual(len(s["disks"]), 4); self.assertEqual([r["name"] for r in s["raids"]], ["Volume 1", "Volume 2"])
        self.assertEqual(s["raids"][0]["total"], 14500000000000); self.assertEqual(s["disks"][3]["lv"], "crit")
        self.assertTrue(s["synology"]); self.assertIsNotNone(s["mem"])
        self.assertEqual(m.test_connection(cfg)["dsm"], "DSM 7.2.1-69057 Update 5")

    def test_snmpv3_authpriv(self):
        self.check(m.validate({"name": "s", "host": "127.0.0.1", "port": self.port, "version": "3", "user": "nasuser", "level": "authPriv",
                               "auth_proto": "SHA", "auth_pass": "authpass123", "priv_proto": "AES", "priv_pass": "privpass123", "timeout": 3}))
    def test_snmpv2c(self):
        self.check(m.validate({"name": "s", "host": "127.0.0.1", "port": self.port, "version": "2c", "community": "simcomm", "timeout": 3}))
    def test_wrong_keys_fail_cleanly(self):
        with self.assertRaisesRegex(m.SnmpError, "(?i)authentication|decrypt|Unknown user|incorrect"):
            m.collect(m.validate({"name": "s", "host": "127.0.0.1", "port": self.port, "version": "3", "user": "nasuser", "auth_pass": "wrongpass12", "priv_pass": "privpass123", "timeout": 2}), {})

if __name__ == "__main__":
    unittest.main()
