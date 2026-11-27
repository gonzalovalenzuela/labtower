"""2.1.3f: segundo factor TOTP (RFC 6238), códigos de recuperación y registro de auditoría."""
import json
import time
import unittest
from typing import ClassVar

from tests import support
from tests.support import ADMIN, Server, auth, load, make_user


class Req:
    client_address = ("127.0.0.1", 1)
    headers: ClassVar[dict] = {"X-Real-IP": "198.51.100.9", "User-Agent": "t"}

def now_code(secret, off=0):
    return auth.totp_at(secret, int(time.time() // 30) + off)

class Totp(unittest.TestCase):
    def test_rfc6238_vector(self):
        sec = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"          # "12345678901234567890"
        self.assertEqual(auth.totp_at(sec, 59 // 30), "287082")
        self.assertEqual(auth.totp_at(sec, 1111111109 // 30), "081804")

    def test_window_and_replay(self):
        sec = auth.totp_new_secret()
        c = now_code(sec)
        step = auth.totp_check(sec, c)
        self.assertIsNotNone(step)
        self.assertIsNone(auth.totp_check(sec, c, last=step))          # same code twice
        self.assertIsNone(auth.totp_check(sec, now_code(sec, 5)))      # too far
        self.assertIsNone(auth.totp_check(sec, "12345"))
        self.assertIsNone(auth.totp_check(sec, None))
        self.assertIsNotNone(auth.totp_check(sec, " " + c[:3] + " " + c[3:]))

    def test_uri(self):
        u = auth.totp_uri("ana", "ABC")
        self.assertTrue(u.startswith("otpauth://totp/LabTower:ana?secret=ABC"))

class LoginFlow(unittest.TestCase):
    def setUp(self):
        self.user = f"tf{time.time_ns() % 10**9}"
        make_user(self.user, ADMIN, "Passw0rd-long-1")
        auth.throttle_clear("ip:198.51.100.9"); auth.throttle_clear("u:" + self.user)

    def enable(self):
        b = auth.totp_begin(self.user)
        rec, err = auth.totp_enable(self.user, now_code(b["secret"]))
        self.assertIsNone(err)
        return b["secret"], rec

    def test_without_2fa_nothing_changes(self):
        u, err = auth.login(Req(), self.user, "Passw0rd-long-1")
        self.assertIsNone(err); self.assertEqual(u["permissions"]["wol"], "admin")

    def test_enable_needs_pending_secret_and_valid_code(self):
        self.assertEqual(auth.totp_enable(self.user, "123456")[1], "Start the setup first")
        auth.totp_begin(self.user)
        self.assertEqual(auth.totp_enable(self.user, "000000")[1], "Invalid code")
        self.assertFalse(auth.totp_status(self.user)["enabled"])

    def test_code_required_then_accepted_once(self):
        sec, rec = self.enable()
        self.assertEqual(len(rec), 10)
        st = auth.totp_status(self.user); self.assertTrue(st["enabled"]); self.assertEqual(st["recovery_left"], 10)
        u, err = auth.login(Req(), self.user, "Passw0rd-long-1")
        self.assertIsNone(u); self.assertEqual(err, (401, auth.NEED_CODE))
        u, err = auth.login(Req(), self.user, "Passw0rd-long-1", now_code(sec, 1))   # enable() used the current step
        self.assertIsNone(err)
        u, err = auth.login(Req(), self.user, "Passw0rd-long-1", now_code(sec, 1))   # replay
        self.assertEqual(err, (401, "Invalid code"))

    def test_wrong_password_does_not_reveal_2fa(self):
        self.enable()
        _u, err = auth.login(Req(), self.user, "wrong-wrong-wrong")
        self.assertEqual(err, (401, "Invalid credentials"))

    def test_wrong_codes_lock_the_account(self):
        self.enable()
        errs = [auth.login(Req(), self.user, "Passw0rd-long-1", "000000")[1] for _ in range(auth.ACCOUNT_FAILS + 1)]
        self.assertEqual(errs[0], (401, "Invalid code"))
        self.assertEqual(errs[-1][0], 429)
        auth.throttle_clear("ip:198.51.100.9"); auth.throttle_clear("u:" + self.user)

    def test_recovery_code_works_once(self):
        _sec, rec = self.enable()
        _u, err = auth.login(Req(), self.user, "Passw0rd-long-1", rec[0].upper())
        self.assertIsNone(err)
        _u, err = auth.login(Req(), self.user, "Passw0rd-long-1", rec[0])
        self.assertEqual(err[0], 401)
        self.assertEqual(auth.totp_status(self.user)["recovery_left"], 9)
        self.assertTrue(any(e["x"] == "2fa_recovery_used" and e["a"] == self.user for e in auth.read_audit(50)))

    def test_disable_and_secret_not_in_login_result_of_other_user(self):
        _sec, _rec = self.enable()
        self.assertTrue(auth.totp_disable(self.user))
        _u, err = auth.login(Req(), self.user, "Passw0rd-long-1")
        self.assertIsNone(err)
        self.assertFalse(auth.totp_disable(self.user))

    def test_login_session_passes_the_code(self):
        _sec, rec = self.enable()
        r, err = auth.login_session(Req(), self.user, "Passw0rd-long-1", None)
        self.assertEqual(err, (401, auth.NEED_CODE))
        r, err = auth.login_session(Req(), self.user, "Passw0rd-long-1", None, rec[1])
        self.assertIsNone(err); self.assertTrue(r["token"])

class Audit(unittest.TestCase):
    def test_write_read_filter_and_clean(self):
        auth.audit("zed", "user_created", "bob\nx", "a" * 500, "1.2.3.4")
        auth.audit("yan", "user_deleted", "bob")
        e = auth.read_audit(5)
        self.assertEqual(e[0]["x"], "user_deleted")                    # newest first
        self.assertEqual(e[1]["g"], "bob x"); self.assertEqual(len(e[1]["d"]), 200)
        self.assertTrue(all(x["a"] == "zed" for x in auth.read_audit(50, actor="zed")))
        self.assertTrue(all(x["x"] == "user_deleted" for x in auth.read_audit(50, action="user_deleted")))

    def test_trimmed(self):
        old = (auth.AUDIT_MAX, auth._audit_lines[0])
        auth.AUDIT_MAX = 20; auth._audit_lines[0] = 0
        try:
            for i in range(450): auth.audit("t", f"x{i}")
            n = len(auth.AUDIT_FILE.read_text().splitlines())
            self.assertLess(n, 450)
            self.assertEqual(auth.read_audit(1)[0]["x"], "x449")
        finally:
            auth.AUDIT_MAX, auth._audit_lines[0] = old

class AdminPanel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = Server(load("auth/admin_panel.py").H)
    @classmethod
    def tearDownClass(cls): cls.srv.close()
    def setUp(self):
        self.pw = "Passw0rd-long-1"
        self.name = f"ap{time.time_ns() % 10**9}"
        self.tok = make_user(self.name, ADMIN, self.pw)
        auth.throttle_clear("ip:198.51.100.7"); auth.throttle_clear("u:" + self.name)

    def test_full_enroll_login_and_reset(self):
        s = self.srv
        self.assertEqual(s.call("GET", "/api/2fa", token=self.tok)[1]["enabled"], False)
        self.assertEqual(s.call("POST", "/api/2fa/begin", {"current_password": "bad"}, self.tok)[0], 403)
        st, b = s.call("POST", "/api/2fa/begin", {"current_password": self.pw}, self.tok)
        self.assertEqual(st, 200); self.assertIn("otpauth://", b["uri"])
        self.assertEqual(s.call("POST", "/api/2fa/enable", {"code": "000000"}, self.tok)[0], 400)
        st, b2 = s.call("POST", "/api/2fa/enable", {"code": now_code(b["secret"])}, self.tok)
        self.assertEqual(st, 200); self.assertEqual(len(b2["recovery"]), 10)
        self.assertEqual(s.call("POST", "/api/2fa/begin", {"current_password": self.pw}, self.tok)[0], 409)
        # the panel login now asks for the code
        st, b3 = s.call("POST", "/api/login", {"username": self.name, "password": self.pw})
        self.assertEqual((st, b3["error"]), (401, auth.NEED_CODE))
        st, b3 = s.call("POST", "/api/login", {"username": self.name, "password": self.pw, "code": b2["recovery"][0]})
        self.assertEqual(st, 200)
        users = s.call("GET", "/api/users", token=self.tok)[1]["users"]
        self.assertTrue(next(u for u in users if u["username"] == self.name)["totp"])
        self.assertNotIn("secret", json.dumps(users))
        # another admin resets it
        other = f"ot{time.time_ns() % 10**9}"
        tok2 = make_user(other, ADMIN, self.pw)
        auth.throttle_clear("u:" + other)
        st, _ = s.call("POST", "/api/2fa/reset", {"current_password": self.pw, "username": self.name}, tok2)
        self.assertEqual(st, 200)
        self.assertFalse(auth.totp_status(self.name)["enabled"])
        acts = [(e["x"], e["a"], e["g"]) for e in s.call("GET", "/api/audit?limit=50", token=self.tok)[1]["audit"]]
        self.assertIn(("2fa_enabled", self.name, self.name), acts)
        self.assertIn(("2fa_reset", other, self.name), acts)

    def test_audit_needs_admin_and_records_user_changes(self):
        s = self.srv
        self.assertEqual(s.call("GET", "/api/audit")[0], 401)
        st, _ = s.call("POST", "/api/users", {"username": "aud" + self.name[2:], "password": "Another-long-pass-9", "current_password": self.pw}, self.tok)
        self.assertEqual(st, 201)
        st, _ = s.call("DELETE", "/api/users/aud" + self.name[2:], token=self.tok)
        self.assertEqual(st, 200)
        acts = [e["x"] for e in s.call("GET", "/api/audit?limit=20&actor=" + self.name, token=self.tok)[1]["audit"]]
        self.assertIn("user_created", acts); self.assertIn("user_deleted", acts)

class ModuleRpc(unittest.TestCase):
    def test_service_records_audit_as_the_calling_module(self):
        authrpc = load("auth/authrpc.py")
        svc = authrpc.Service(auth, identify=lambda uid: "net")
        r = svc.handle("net", {"op": "audit", "actor": "ana", "action": "device_added", "target": "sw1", "detail": "x", "ip": "1.1.1.1"})
        self.assertEqual(r, {"ok": True})
        e = auth.read_audit(1)[0]
        self.assertEqual((e["m"], e["a"], e["x"]), ("net", "ana", "device_added"))
        self.assertEqual(svc.handle("nobody", {"op": "audit", "actor": "a", "action": "b"}), {"error": "forbidden"})

class Mandatory2fa(unittest.TestCase):
    """Política: los administradores deben activar 2FA; hasta entonces su sesión queda pendiente. / Policy: admins must turn 2FA on first."""
    @classmethod
    def setUpClass(cls): cls.srv = Server(load("auth/admin_panel.py").H)
    @classmethod
    def tearDownClass(cls): cls.srv.close(); auth.write_json(auth.POLICY_FILE, {})
    def setUp(self):
        auth.write_json(auth.POLICY_FILE, {}); self.pw = "Passw0rd-long-1"
        self.boss = f"pb{time.time_ns() % 10**9}"; self.btok = make_user(self.boss, ADMIN, self.pw)
        self.adm = f"pa{time.time_ns() % 10**9}"; self.atok = make_user(self.adm, {**support.READONLY, "dns": "admin"}, self.pw)
        self.ro = f"pr{time.time_ns() % 10**9}"; self.rtok = make_user(self.ro, support.READONLY, self.pw)
        for u in (self.boss, self.adm, self.ro): auth.throttle_clear("u:" + u)
        auth.throttle_clear("ip:198.51.100.7")
    tearDown = lambda self: auth.write_json(auth.POLICY_FILE, {})

    def enable_2fa(self, tok):
        st, b = self.srv.call("POST", "/api/2fa/begin", {"current_password": self.pw}, tok); self.assertEqual(st, 200, b)
        st, b2 = self.srv.call("POST", "/api/2fa/enable", {"code": now_code(b["secret"])}, tok); self.assertEqual(st, 200, b2)

    def test_policy_and_pending_session(self):
        s = self.srv
        body = {"require_2fa_admins": True, "current_password": self.pw}
        self.assertIn(s.call("POST", "/api/policy", body, self.atok)[0], (401, 403))               # not admin of every module
        self.assertEqual(s.call("POST", "/api/policy", body, self.btok)[0], 409)                     # own 2FA off: would lock themselves out
        self.enable_2fa(self.btok)
        self.assertEqual(s.call("POST", "/api/policy", {**body, "current_password": "bad"}, self.btok)[0], 403)
        st, d = s.call("POST", "/api/policy", body, self.btok); self.assertEqual((st, d["policy"]), (200, {"require_2fa_admins": True}))
        self.assertTrue(auth.read_audit(5, self.boss, "policy_2fa_on"))
        # an admin of one module without 2FA: pending everywhere, except turning 2FA on
        self.assertIsNone(auth.get_session(self.atok)); self.assertTrue(auth.get_session(self.atok, allow_pending=True)["must_setup_2fa"])
        self.assertEqual(s.call("GET", "/api/self", token=self.atok)[1]["must_setup_2fa"], True)
        lr = auth.login_session(Req(), self.adm, self.pw)[0]; self.assertTrue(lr["must_setup_2fa"])
        self.assertIsNotNone(auth.get_session(self.rtok))                                            # not an admin: unaffected
        self.assertFalse(auth.login_session(Req(), self.ro, self.pw)[0]["must_setup_2fa"])
        self.assertEqual(s.call("POST", "/api/2fa/disable", {"current_password": self.pw}, self.btok)[0], 409)   # cannot turn it off now
        self.enable_2fa(self.atok)                                                                   # works with the pending session
        self.assertIsNotNone(auth.get_session(self.atok))
        self.assertEqual(s.call("POST", "/api/policy", {"require_2fa_admins": False, "current_password": self.pw}, self.btok)[0], 200)
        self.assertFalse(auth.policy()["require_2fa_admins"])

    def test_page_and_redirects(self):
        root = support.ROOT
        self.assertEqual(self.srv.call("GET", "/setup-2fa")[0], 200)
        for f in ("nas-monitor", "dns-monitor", "net-monitor", "proxmox-monitor", "uptime-monitor", "wol-console", "nut-monitor", "wan-monitor", "vpn-monitor", "overview", "auth"):
            self.assertIn("must_setup_2fa", (root / f / "static/app.js").read_text(encoding="utf-8"), f)
        js = (root / "auth/static/setup-2fa.js").read_text(encoding="utf-8")
        self.assertIn("cspRegister({ begin, confirmCode, done, logout })", js); self.assertNotRegex((root / "auth/static/setup-2fa.html").read_text(), r"\son[a-z]+=")
        for f in ("debian/preinst", "debian/prerm", "scripts/teleporter.sh"): self.assertIn("auth/policy.json", (root / f).read_text(), f)


class ModuleChanges(unittest.TestCase):
    """Cada cambio aceptado en un módulo queda en la auditoría (auth.Audited). / Every accepted change in a module is audited."""
    def test_actions(self):
        a = auth.audit_action
        self.assertEqual(a("POST", "/api/dns", {"name": "Pi-hole", "password": "secret"}), ("item_added", "Pi-hole", "/api/dns"))
        self.assertEqual(a("DELETE", "/api/nas/abc", None)[:2], ("item_deleted", "abc"))
        self.assertEqual(a("PUT", "/api/servers/s1", {"name": "UPS"})[:2], ("item_edited", "UPS"))
        self.assertEqual(a("POST", "/api/monitors/" + "a" * 36 + "/pause", {"paused": False})[0], "item_resumed")
        self.assertEqual(a("POST", "/api/dns/x/blocking", {"enabled": False, "seconds": 300}), ("dns_blocking", "x", "/api/dns/x/blocking seconds=300 enabled=False"))
        self.assertEqual(a("POST", "/api/wake", {"mac": "aa:bb:cc:00:00:01"})[:2], ("wol_wake", "aa:bb:cc:00:00:01"))
        self.assertEqual(a("POST", "/api/snmp", {"community": "x"})[0], "settings_changed")
        self.assertEqual(a("POST", "/api/switches/s1/ports", {})[0], "item_changed")
        self.assertEqual(a("POST", "/api/hosts/update", {"ip": "192.0.2.5", "alias": "NAS"}), ("device_edited", "192.0.2.5", "/api/hosts/update ip=192.0.2.5 alias=NAS"))
        for skip in ("/api/login", "/api/logout", "/api/test", "/api/dns/x/resolve", "/api/rules", "/api/wan/config", "/api/switches/refresh"):
            self.assertIsNone(a("POST", skip, {}), skip)
        self.assertNotIn("secret", str(a("POST", "/api/nas", {"name": "N", "password": "secret", "api_key": "secret"})))

    @staticmethod
    def wait(actor, action=None):
        """The entry is written right after the answer is sent: wait for it a moment."""
        for _ in range(40):
            r = auth.read_audit(5, actor, action)
            if r: return r
            time.sleep(0.05)
        return []

    def test_accepted_changes_are_recorded(self):
        m = load("uptime-monitor/server.py")
        self.assertTrue(issubclass(m.H, auth.Audited)); self.assertEqual(m.H.AUDIT_MODULE, "uptime")
        srv = support.Server(m.H)
        try:
            adm = support.make_user("aud_mod", support.ADMIN); ro = support.make_user("aud_ro", support.READONLY)
            body = {"type": "tcp", "name": "SSH box", "host": "192.0.2.22", "port": 22}
            self.assertEqual(srv.call("POST", "/api/monitors", body, token=ro)[0], 403)                 # refused: not recorded
            st, d = srv.call("POST", "/api/monitors", body, token=adm); self.assertIn(st, (200, 201))
            e = self.wait("aud_mod")[0]
            self.assertEqual((e["x"], e["g"]), ("item_added", "SSH box"))
            self.assertFalse(auth.read_audit(5, "aud_ro"))
            mid = (d.get("monitor") or d).get("id")
            if mid: srv.call("DELETE", "/api/monitors/" + mid, token=adm); self.assertEqual(self.wait("aud_mod", "item_deleted")[0]["x"], "item_deleted")
        finally: srv.close()
        for f in ("nut-monitor", "net-monitor", "proxmox-monitor", "nas-monitor", "dns-monitor", "wan-monitor", "vpn-monitor", "uptime-monitor", "wol-console"):
            self.assertIn("class H(auth.Audited, BaseHTTPRequestHandler):", (support.ROOT / f / "server.py").read_text(encoding="utf-8"), f)


if __name__ == "__main__":
    unittest.main()
