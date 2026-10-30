"""Aislamiento entre módulos (2.1.3) / module isolation: authentication service, data layout, units and migration."""
import contextlib, json, os, re, socket, sqlite3, subprocess, sys, tempfile, textwrap, threading, time, unittest
from pathlib import Path
from tests import support
auth = support.auth
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "auth"))
import authrpc, migrate_layout  # noqa: E402


def sock_path():
    d = tempfile.mkdtemp(prefix="lt-rpc-")
    return os.path.join(d, "a.sock")


class FakeAuth:
    """Records what the service asks of the authentication layer (no files involved)."""
    def __init__(self): self.events = []
    def record_event(self, caller, level, text, k=None, **params): self.events.append((caller, level, text, k, params))
    def read_events(self, mods, limit): return [{"m": "x"}]
    def get_session(self, tok, allow_pending=False): return {"username": "u", "permissions": {}} if tok == "good" else None
    def delete_session(self, tok): self.deleted = tok


class ServiceLogic(unittest.TestCase):
    def setUp(self):
        self.fa = FakeAuth(); self.svc = authrpc.Service(self.fa)

    def test_event_module_comes_from_the_caller_not_from_the_request(self):
        r = self.svc.handle("wol", {"op": "event", "level": "warn", "text": "x", "module": "net", "k": "a", "params": {"module": "nut", "n": 1}})
        self.assertEqual(r, {"ok": True})
        caller, level, text, k, params = self.fa.events[0]
        self.assertEqual(caller, "wol"); self.assertNotIn("module", params)

    def test_reserved_parameter_names_cannot_collide_with_record_event_arguments(self):
        r = self.svc.handle("net", {"op": "event", "level": "info", "text": "t", "params": {"level": "crit", "text": "z", "k": "q", "self": 1, "ok": 2}})
        self.assertEqual(r, {"ok": True})
        self.assertEqual(self.fa.events[0][4], {"ok": 2})

    def test_bad_events_are_refused(self):
        for bad in ({"level": "boom", "text": "x"}, {"level": "info", "text": 5}, {"level": "info"}):
            self.assertEqual(self.svc.handle("wol", {"op": "event", **bad}), {"error": "bad event"})
        self.assertEqual(self.svc.handle("root", {"op": "event", "level": "info", "text": "x"}), {"error": "forbidden"})

    def test_only_the_overview_reads_the_timeline(self):
        self.assertEqual(self.svc.handle("wol", {"op": "events"}), {"error": "forbidden"})
        self.assertEqual(self.svc.handle("overview", {"op": "events", "limit": 5})["events"], [{"m": "x"}])

    def test_session_lookup_validates_the_token_type(self):
        self.assertEqual(self.svc.handle("wol", {"op": "session", "token": "good"})["session"]["username"], "u")
        for tok in (None, 5, "", "x" * 200, ["good"]):
            self.assertEqual(self.svc.handle("wol", {"op": "session", "token": tok}), {"session": None})

    def test_there_is_no_operation_that_creates_a_session_or_reads_users(self):
        for op in ("create_session", "load_users", "users", "save_users", "authenticate", "../x", "", "a" * 40, None, 5):
            self.assertEqual(self.svc.handle("wol", {"op": op}), {"error": "unknown operation"})
        self.assertEqual(self.svc.handle("wol", ["session"]), {"error": "unknown operation"})
        ops = sorted(n[3:] for n in dir(authrpc.Service) if n.startswith("op_"))
        self.assertEqual(ops, ["audit", "event", "events", "health", "login", "logout", "session"])

    def test_login_input_is_validated(self):
        for r in ({"username": 5, "password": "x"}, {"username": "a", "password": None}, {"username": "a" * 300, "password": "x"},
                  {"username": "a", "password": "p" * 2000}):
            self.assertEqual(self.svc.handle("wol", {"op": "login", **r})["status"], 400)

    def test_identity_is_taken_from_the_uid(self):
        self.assertEqual(authrpc.identify_by_uid(0), "root")
        self.assertIsNone(authrpc.identify_by_uid(4242424))
        import pwd
        try: nobody = pwd.getpwnam("nobody").pw_uid
        except KeyError: self.skipTest("no nobody user")
        self.assertIsNone(authrpc.identify_by_uid(nobody))          # a user without the labtower- prefix is never accepted

    def test_client_address_is_sanitised(self):
        self.assertEqual(authrpc._clean_ip("198.51.100.7"), "198.51.100.7")
        for bad in ("a b", "x" * 100, "1.2.3.4\nX", None, 5, ""):
            self.assertEqual(authrpc._clean_ip(bad), "unknown")


class Transport(unittest.TestCase):
    def serve(self, identify=lambda uid: "wol", **patch):
        self.saved = {k: getattr(authrpc, k) for k in patch}
        for k, v in patch.items(): setattr(authrpc, k, v)
        self.addCleanup(lambda: [setattr(authrpc, k, v) for k, v in self.saved.items()])
        self.path = sock_path()
        self.srv = authrpc.serve(self.path, FakeAuth(), identify)
        self.addCleanup(self.srv.close)
        return self.path

    def test_round_trip_and_socket_mode(self):
        p = self.serve()
        self.assertEqual(oct(os.stat(p).st_mode & 0o777), "0o660")
        self.assertEqual(authrpc.call(p, "session", token="good")["session"]["username"], "u")

    def test_unknown_uid_is_refused_before_anything_is_read(self):
        p = self.serve(identify=lambda uid: None)
        self.assertEqual(authrpc.call(p, "session", token="good"), {"error": "forbidden"})

    def test_oversized_request_is_not_processed(self):
        p = self.serve()
        try: r = authrpc.call(p, "session", retries=1, token="x" * (authrpc.MAX_REQUEST + 10))
        except authrpc.AuthUnavailable: return                                  # connection dropped while sending
        self.assertEqual(r, {"error": "bad request"})

    def test_garbage_does_not_stop_the_service(self):
        p = self.serve()
        s = socket.socket(socket.AF_UNIX); s.connect(p); s.sendall(b"\xff\xfe not json\n"); self.assertIn(b"bad request", s.recv(100)); s.close()
        self.assertEqual(authrpc.call(p, "session", token="good")["session"]["username"], "u")

    def test_a_silent_client_cannot_hold_a_connection_forever(self):
        p = self.serve(TIMEOUT=0.6)
        s = socket.socket(socket.AF_UNIX); s.connect(p); s.settimeout(5)
        t0 = time.monotonic()
        s.recv(10)                                           # the server answers with an error and closes, or just closes
        self.assertLess(time.monotonic() - t0, 3)
        s.close()

    def test_a_client_dripping_bytes_hits_the_total_deadline(self):
        p = self.serve(TIMEOUT=0.8)
        s = socket.socket(socket.AF_UNIX); s.connect(p); s.settimeout(5)
        t0 = time.monotonic()
        try:
            for _ in range(40):                              # one byte every 0.2 s would last 8 s if the timeout were per byte
                s.sendall(b" "); time.sleep(0.2)
        except OSError:
            pass
        self.assertLess(time.monotonic() - t0, 3.5)
        s.close()

    def test_concurrent_connections_are_capped(self):
        p = self.serve(MAX_CONNS=2, TIMEOUT=10)
        held = []
        for _ in range(2):
            s = socket.socket(socket.AF_UNIX); s.connect(p); held.append(s)
        time.sleep(0.3)
        extra = socket.socket(socket.AF_UNIX); extra.connect(p); extra.settimeout(3)
        self.assertEqual(extra.recv(10), b"")                # refused: closed at once
        extra.close()
        for s in held: s.close()
        time.sleep(0.3)
        self.assertEqual(authrpc.call(p, "session", token="good")["session"]["username"], "u")   # slots are released


class RemoteClient(unittest.TestCase):
    """auth.py in module mode against a real service running in another process."""
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp(prefix="lt-auth-")
        cls.sock = os.path.join(cls.dir, "a.sock")
        code = textwrap.dedent(f"""
            import sys, time
            sys.path.insert(0, {str(ROOT / "auth")!r})
            import auth, authrpc
            with auth.users_lock():
                u = auth.load_users()
                u["alice"] = {{"password_hash": auth._hash("Sup3r-secret-pass"), "permissions": {{"wol": "admin", "nut": "readonly"}}, "created": 1, "must_change_password": False}}
                auth.save_users(u)
            ident = lambda uid: "overview" if open({os.path.join(cls.dir, "who")!r}).read().strip() == "overview" else "wol"
            authrpc.serve({cls.sock!r}, auth, ident)
            print("ready", flush=True)
            time.sleep(120)
        """)
        Path(cls.dir, "who").write_text("wol")
        env = dict(os.environ, LABTOWER_USERS=os.path.join(cls.dir, "auth", "users.json"), LABTOWER_DATA=cls.dir)
        env.pop("LABTOWER_AUTH_SOCKET", None); env.pop("LABTOWER_MODULE", None)
        os.makedirs(os.path.join(cls.dir, "auth"), mode=0o700)
        cls.proc = subprocess.Popen([sys.executable, "-I", "-c", code], env=env, stdout=subprocess.PIPE, text=True)
        assert cls.proc.stdout.readline().strip() == "ready"

    @classmethod
    def tearDownClass(cls):
        cls.proc.kill(); cls.proc.wait()

    def setUp(self):
        self.saved = (auth.REMOTE, auth.AUTH_SOCKET)
        auth.REMOTE, auth.AUTH_SOCKET = True, self.sock
        auth._remote_cache.clear()
        self.addCleanup(lambda: setattr(auth, "REMOTE", self.saved[0]) or setattr(auth, "AUTH_SOCKET", self.saved[1]))

    class H:
        client_address = ("127.0.0.1", 1); headers = {"X-Real-IP": "198.51.100.77", "User-Agent": "ua"}

    def test_login_session_logout_through_the_service(self):
        r, err = auth.login_session(self.H(), "alice", "Sup3r-secret-pass", False)
        self.assertIsNone(err); self.assertEqual(r["username"], "alice"); self.assertEqual(r["permissions"]["wol"], "admin")
        tok = r["token"]
        s = auth.get_session(tok)
        self.assertEqual(s["username"], "alice")
        auth.delete_session(tok)
        self.assertIsNone(auth.get_session(tok))             # the logout drops the 1 s cache too

    def test_wrong_password_and_unknown_user(self):
        for u, p in (("alice", "nope-nope-nope"), ("ghost", "whatever-12345")):
            r, err = auth.login_session(self.H(), u, p, False)
            self.assertIsNone(r); self.assertIn(err[0], (401, 429))

    def test_forged_token_is_not_a_session(self):
        for t in ("a" * 43, "0" * 64, "../x"):
            self.assertIsNone(auth.get_session(t))

    def test_a_module_cannot_run_the_local_only_functions(self):
        for fn, args in ((auth.load_users, ()), (auth.create_session, ("alice", {}, 60)), (auth.save_users, ({},)), (auth.list_sessions, ())):
            with self.assertRaises(RuntimeError): fn(*args)

    def test_events_go_through_the_service_under_the_callers_name(self):
        auth.record_event("net", "warn", "from-wol-process", "k.test", n=3)
        authrpc.call(self.sock, "event", level="warn", text="forged-module", module="nut", params={"module": "nut"})    # a hostile client
        Path(self.dir, "who").write_text("overview")
        try: ev = auth.read_events(None, 50)
        finally: Path(self.dir, "who").write_text("wol")
        mine = [e for e in ev if e.get("tx") in ("from-wol-process", "forged-module")]
        self.assertEqual(len(mine), 2)
        self.assertEqual({e["m"] for e in mine}, {"wol"})                   # never "net" / "nut": the name comes from the operating system user

    def test_a_flood_of_bogus_tokens_does_not_grow_the_cache_without_bound(self):
        for i in range(2300): auth.get_session("%064x" % i)
        self.assertLessEqual(len(auth._remote_cache), 2048)

    def test_service_down_fails_closed_and_the_breaker_avoids_piling_up(self):
        auth.AUTH_SOCKET = os.path.join(self.dir, "missing.sock")
        auth._rpc_down_until = 0.0
        self.addCleanup(lambda: setattr(auth, "_rpc_down_until", 0.0))
        orig = authrpc.call
        calls = []
        authrpc.call = lambda path, op, retries=6, **f: (calls.append(op), orig(path, op, retries=1, **f))[1]
        try:
            self.assertIsNone(auth.get_session("b" * 43))
            r, err = auth.login_session(self.H(), "alice", "Sup3r-secret-pass", False)
            self.assertIsNone(r); self.assertEqual(err[0], 503)
            t0 = time.monotonic()
            for i in range(50): self.assertIsNone(auth.get_session("%064x" % i))
            self.assertLess(time.monotonic() - t0, 0.5)
            self.assertEqual(calls, ["session"])           # the breaker let only the first one through
        finally:
            authrpc.call = orig


class PublishedFiles(unittest.TestCase):
    def test_reader_rejects_links_big_files_and_wrong_types(self):
        d = Path(tempfile.mkdtemp())
        ok = d / "ok.json"; ok.write_text('[{"mac": "aa"}]')
        self.assertEqual(auth.read_published(ok, [], list), [{"mac": "aa"}])
        self.assertEqual(auth.read_published(ok, "dflt", dict), "dflt")                    # wrong top-level type
        link = d / "link.json"; link.symlink_to(ok)
        self.assertEqual(auth.read_published(link, "dflt", list), "dflt")                  # symlink: not followed
        big = d / "big.json"; big.write_bytes(b"[" + b"1," * (auth.PUBLISHED_MAX // 2) + b"1]")
        self.assertEqual(auth.read_published(big, "dflt", list), "dflt")                   # over the cap
        (d / "bad.json").write_text("{not json")
        self.assertEqual(auth.read_published(d / "bad.json", "dflt", dict), "dflt")
        self.assertEqual(auth.read_published(d, "dflt", dict), "dflt")                     # a directory
        self.assertEqual(auth.read_published(d / "missing", "dflt", dict), "dflt")


class MetricsSplit(unittest.TestCase):
    @staticmethod
    def q(path, sql):
        with contextlib.closing(sqlite3.connect(path)) as c: return c.execute(sql).fetchall()

    def make_old(self, d):
        src = os.path.join(d, "metrics.db")
        with contextlib.closing(sqlite3.connect(src)) as c:
            c.executescript("""CREATE TABLE pi_samples(ts INTEGER PRIMARY KEY, temp REAL, flags INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE wan_samples(ts INTEGER PRIMARY KEY, up INTEGER NOT NULL); CREATE INDEX wi ON wan_samples(up);
        CREATE TABLE pve_samples(cid TEXT, node TEXT, ts INTEGER); CREATE TABLE secret_notes(x TEXT);
        INSERT INTO pi_samples VALUES (1, 40.5, 0), (2, 41.0, 1); INSERT INTO wan_samples VALUES (5, 1); INSERT INTO pve_samples VALUES ('c','n',9);
        INSERT INTO secret_notes VALUES ('must not be copied anywhere');""")
            c.commit()
        return src

    def test_each_module_only_gets_its_own_tables(self):
        d = tempfile.mkdtemp(); src = self.make_old(d); out = os.path.join(d, "out")
        res = migrate_layout.split_metrics(src, out)
        self.assertEqual(res, {"overview": ["pi_samples"], "proxmox-monitor": ["pve_samples"], "wan-monitor": ["wan_samples"]})
        self.assertEqual(sorted(os.listdir(out)), ["overview.db", "proxmox-monitor.db", "wan-monitor.db"])
        for f in os.listdir(out):
            p = os.path.join(out, f)
            self.assertEqual(os.stat(p).st_mode & 0o777, 0o600)
            names = {r[0] for r in self.q(p, "SELECT name FROM sqlite_master")}
            self.assertNotIn("secret_notes", names)
        self.assertEqual(self.q(os.path.join(out, "overview.db"), "SELECT COUNT(*) FROM pi_samples")[0][0], 2)
        self.assertIn("wi", {r[0] for r in self.q(os.path.join(out, "wan-monitor.db"), "SELECT name FROM sqlite_master")})

    def test_the_source_is_never_modified(self):
        d = tempfile.mkdtemp(); src = self.make_old(d)
        before = Path(src).read_bytes()
        migrate_layout.split_metrics(src, os.path.join(d, "o"))
        self.assertEqual(Path(src).read_bytes(), before)

    def test_wal_source_with_rows_only_in_the_log(self):
        d = tempfile.mkdtemp(); src = os.path.join(d, "metrics.db")
        c = sqlite3.connect(src); c.execute("PRAGMA journal_mode=WAL"); c.execute("PRAGMA wal_autocheckpoint=0")
        c.execute("CREATE TABLE pi_samples(ts INTEGER PRIMARY KEY, temp REAL, flags INTEGER NOT NULL DEFAULT 0)")
        c.executemany("INSERT INTO pi_samples VALUES (?, 1.5, 0)", [(i,) for i in range(1, 51)]); c.commit()
        self.assertTrue(os.path.getsize(src + "-wal") > 0)                          # the rows live in the -wal, not in the main file
        try:
            before = Path(src).read_bytes()
            migrate_layout.split_metrics(src, os.path.join(d, "o"))
            self.assertEqual(self.q(os.path.join(d, "o", "overview.db"), "SELECT COUNT(*) FROM pi_samples")[0][0], 50)
            self.assertEqual(Path(src).read_bytes(), before)
        finally:
            c.close()

    def test_damaged_source_is_refused(self):
        d = tempfile.mkdtemp(); src = os.path.join(d, "metrics.db"); Path(src).write_bytes(b"not a database" * 100)
        with self.assertRaises(Exception): migrate_layout.split_metrics(src, os.path.join(d, "o"))


class Packaging(unittest.TestCase):
    postinst = (ROOT / "debian" / "postinst").read_text()
    MODULES = {  # unit: (user, data dir, code dir)
        "wol-console": ("labtower-wol", "wol-console"), "labtower-ups": ("labtower-nut", "nut-monitor"),
        "admin-panel": ("labtower-auth", "auth"), "net-monitor": ("labtower-net", "net-monitor"),
        "proxmox-monitor": ("labtower-pve", "proxmox-monitor"), "nas-monitor": ("labtower-nas", "nas-monitor"),
        "dns-monitor": ("labtower-dns", "dns-monitor"), "wan-monitor": ("labtower-wan", "wan-monitor"),
        "labtower-overview": ("labtower-overview", "overview"),
    }

    def test_every_service_has_its_own_user_and_folder(self):
        users = set()
        for unit, (user, datadir) in self.MODULES.items():
            m = re.search(r'^install_service "%s"\s+.*$' % re.escape(unit), self.postinst, re.M)
            self.assertTrue(m, unit)
            self.assertIn(user, m.group(0)); self.assertTrue(m.group(0).rstrip().endswith(datadir), unit)
            users.add(user)
        self.assertEqual(len(users), 9)                      # nobody shares a user
        self.assertNotRegex(self.postinst, r"(?m)^User=labtower$")

    def test_modules_may_only_write_their_own_folder(self):
        self.assertIn("ReadWritePaths=${DATA_DIR}/${datadir}", self.postinst)
        self.assertNotRegex(self.postinst, r"ReadWritePaths=\$\{DATA_DIR\}\n")

    def test_only_the_panel_user_may_run_the_teleporter_as_root(self):
        self.assertRegex(self.postinst, r"(?m)^labtower-auth ALL=\(root\) NOPASSWD: /usr/local/bin/teleporter\.sh gui-backup, /usr/local/bin/teleporter\.sh gui-restore \*$")
        self.assertNotRegex(self.postinst, r"(?m)^labtower ALL=")

    def test_modules_get_the_socket_and_the_panel_creates_it(self):
        self.assertIn("LABTOWER_AUTH_LISTEN=/run/labtower/auth.sock", self.postinst)
        self.assertIn("LABTOWER_AUTH_SOCKET=/run/labtower/auth.sock", self.postinst)
        self.assertIn("RuntimeDirectoryMode=0750", self.postinst)

    def test_shell_syntax_of_every_maintainer_script(self):
        for f in ("postinst", "preinst", "prerm", "postrm"):
            self.assertEqual(subprocess.run(["bash", "-n", str(ROOT / "debian" / f)]).returncode, 0, f)

    def test_modules_never_touch_the_authentication_files(self):
        bad = re.compile(r"auth\.(USERS_FILE|SESSIONS_FILE|THROTTLE_FILE|EVENTS_FILE|INITIAL_PW_FILE|load_users|save_users|create_session|users_lock|authenticate|login\()")
        for mod in ("wol-console", "nut-monitor", "net-monitor", "proxmox-monitor", "nas-monitor", "dns-monitor", "wan-monitor", "overview"):
            for f in (ROOT / mod).glob("*.py"):
                self.assertIsNone(bad.search(f.read_text()), f"{f} uses an authentication-only function")

    def test_published_files_are_group_readable_not_world_readable(self):
        self.assertIn("mode=0o640", (ROOT / "wol-console/server.py").read_text())
        self.assertIn("mode=0o640", (ROOT / "net-monitor/server.py").read_text())
        self.assertNotIn("0o644", (ROOT / "net-monitor/server.py").read_text())


class TeleporterLayout(unittest.TestCase):
    def build(self, d):
        import io, tarfile, hashlib
        old = os.path.join(d, "old-metrics.db")
        MetricsSplit().make_old(d); os.rename(os.path.join(d, "metrics.db"), old)
        users = json.dumps({"admin": {"password_hash": "scrypt$x", "permissions": {"wol": "admin"}}}).encode()
        members = {"data/users.json": users, "data/metrics.db": Path(old).read_bytes()}
        members["backup.json"] = json.dumps({"hostname": "t", "date": "d", "teleporter_version": "x", "package_version": "y"}).encode()
        sums = "".join("%s  %s\n" % (hashlib.sha256(v).hexdigest(), k) for k, v in sorted(members.items()) if k != "backup.json")
        sums += "%s  backup.json\n" % hashlib.sha256(members["backup.json"]).hexdigest()
        members["SHA256SUMS"] = sums.encode()
        arc = os.path.join(d, "old.tar.gz")
        with tarfile.open(arc, "w:gz") as t:
            for k, v in members.items():
                ti = tarfile.TarInfo(k); ti.size = len(v); t.addfile(ti, io.BytesIO(v))
        return arc

    def test_old_backup_restores_into_the_new_layout(self):
        d = tempfile.mkdtemp(); arc = self.build(d)
        data = os.path.join(d, "var"); os.makedirs(data)
        env = dict(os.environ, LABTOWER_HOME=str(ROOT), LABTOWER_DATA=data, LABTOWER_AUTH_LINK=os.path.join(d, "authlink"),
                   LABTOWER_SAFETY_DIR=os.path.join(d, "safe"), LABTOWER_LOCK=os.path.join(d, "lock"), LABTOWER_RESTORE_LOG=os.path.join(d, "r.log"),
                   TELEPORTER_SKIP_SYSTEM="1", LABTOWER_NGINX_CONF=os.path.join(d, "n.conf"), LABTOWER_NGINX_ENABLED=os.path.join(d, "ne.conf"),
                   LABTOWER_NUT_DIR=os.path.join(d, "nut"))
        env.pop("SUDO_USER", None)
        r = subprocess.run(["bash", str(ROOT / "scripts" / "teleporter.sh"), "restore", arc, "-y"], env=env, capture_output=True, text=True, timeout=120)
        self.assertIn("RESULT:", r.stdout, r.stdout + r.stderr)
        self.assertTrue(os.path.isfile(os.path.join(data, "auth", "users.json")), r.stdout + r.stderr)
        self.assertFalse(os.path.exists(os.path.join(data, "users.json")))
        self.assertTrue(os.path.isfile(os.path.join(data, "overview", "metrics.db")), r.stdout)
        self.assertTrue(os.path.isfile(os.path.join(data, "wan-monitor", "metrics.db")))
        self.assertFalse(os.path.exists(os.path.join(data, "metrics.db")))
        self.assertEqual(oct(os.stat(os.path.join(data, "auth", "users.json")).st_mode & 0o777), "0o600")

    def test_backup_of_a_wal_database_passes_its_own_check(self):
        d = tempfile.mkdtemp(); data = os.path.join(d, "var")
        for sub in ("auth", "overview"): os.makedirs(os.path.join(data, sub))
        Path(data, "auth", "users.json").write_text(json.dumps({"admin": {"password_hash": "scrypt$x", "permissions": {"wol": "admin"}}}))
        db = os.path.join(data, "overview", "metrics.db")
        c = sqlite3.connect(db); c.execute("PRAGMA journal_mode=WAL")
        c.execute("CREATE TABLE pi_samples(ts INTEGER PRIMARY KEY, temp REAL, flags INTEGER NOT NULL DEFAULT 0)"); c.execute("INSERT INTO pi_samples VALUES (1, 40, 0)"); c.commit()
        env = dict(os.environ, LABTOWER_HOME=str(ROOT), LABTOWER_DATA=data, LABTOWER_SAFETY_DIR=os.path.join(d, "safe"), LABTOWER_LOCK=os.path.join(d, "lock"),
                   TELEPORTER_SKIP_SYSTEM="1", LABTOWER_NGINX_CONF=os.path.join(d, "n"), LABTOWER_NUT_DIR=os.path.join(d, "nut"))
        env.pop("SUDO_USER", None)
        arc = os.path.join(d, "b.tar.gz")
        try:
            r = subprocess.run(["bash", str(ROOT / "scripts" / "teleporter.sh"), "backup", arc], env=env, capture_output=True, text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("SQLite OK", subprocess.run(["bash", str(ROOT / "scripts" / "teleporter.sh"), "check", arc], env=env, capture_output=True, text=True, timeout=120).stdout)
        finally:
            c.close()

    def test_a_wal_image_in_an_old_backup_still_validates(self):
        d = tempfile.mkdtemp(); src = os.path.join(d, "w.db")
        c = sqlite3.connect(src); c.execute("PRAGMA journal_mode=WAL"); c.execute("CREATE TABLE pi_samples(ts INTEGER PRIMARY KEY)"); c.commit()
        snap = os.path.join(d, "snap.db"); t = sqlite3.connect(snap); c.backup(t); t.close(); c.close()        # a WAL-mode image, like the old backups hold
        self.assertEqual(Path(snap).read_bytes()[18:20], b"\x02\x02")
        env = dict(os.environ); env["TELEPORTER_SKIP_SYSTEM"] = "1"
        src_sh = (ROOT / "scripts" / "teleporter.sh").read_text()
        fn = src_sh[src_sh.index("validate_sqlite() {"):src_sh.index("users_have_admin() {")]
        helpers = src_sh[src_sh.index("as_service() {"):src_sh.index("is_secret() {")]
        helpers2 = src_sh[src_sh.index("in_dir_as_service() {"):src_sh.index("validate_json() {")]
        script = 'SKIP_SYSTEM=1; DROP_FORCE=0\n' + helpers + helpers2 + fn + 'validate_sqlite "$1"\n'
        r = subprocess.run(["bash", "-c", script, "x", snap], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_owner_mapping_and_modes(self):
        src = (ROOT / "scripts" / "teleporter.sh").read_text()
        for needle in ("auth|teleporter) echo labtower-auth", "wol-console) echo labtower-wol", "overview) echo labtower-overview",
                       "*/wol-console/devices.json|*/net-monitor/hosts.json) echo 640", "wol-console|net-monitor) echo 710"):
            self.assertIn(needle, src)
        self.assertNotIn("SERVICE_USER", src)


if __name__ == "__main__":
    unittest.main()
