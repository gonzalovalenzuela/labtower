"""2.1.3f: segundo factor TOTP (RFC 6238), códigos de recuperación y registro de auditoría."""
import json, time, unittest
from tests.support import auth, load, make_user, Server, ADMIN

class Req:
    client_address = ("127.0.0.1", 1)
    headers = {"X-Real-IP": "198.51.100.9", "User-Agent": "t"}

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
        self.user = "tf%d" % (time.time_ns() % 10**9)
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
        u, err = auth.login(Req(), self.user, "wrong-wrong-wrong")
        self.assertEqual(err, (401, "Invalid credentials"))

    def test_wrong_codes_lock_the_account(self):
        self.enable()
        errs = [auth.login(Req(), self.user, "Passw0rd-long-1", "000000")[1] for _ in range(auth.ACCOUNT_FAILS + 1)]
        self.assertEqual(errs[0], (401, "Invalid code"))
        self.assertEqual(errs[-1][0], 429)
        auth.throttle_clear("ip:198.51.100.9"); auth.throttle_clear("u:" + self.user)

    def test_recovery_code_works_once(self):
        sec, rec = self.enable()
        u, err = auth.login(Req(), self.user, "Passw0rd-long-1", rec[0].upper())
        self.assertIsNone(err)
        u, err = auth.login(Req(), self.user, "Passw0rd-long-1", rec[0])
        self.assertEqual(err[0], 401)
        self.assertEqual(auth.totp_status(self.user)["recovery_left"], 9)
        self.assertTrue(any(e["x"] == "2fa_recovery_used" and e["a"] == self.user for e in auth.read_audit(50)))

    def test_disable_and_secret_not_in_login_result_of_other_user(self):
        sec, rec = self.enable()
        self.assertTrue(auth.totp_disable(self.user))
        u, err = auth.login(Req(), self.user, "Passw0rd-long-1")
        self.assertIsNone(err)
        self.assertFalse(auth.totp_disable(self.user))

    def test_login_session_passes_the_code(self):
        sec, rec = self.enable()
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
            for i in range(450): auth.audit("t", "x%d" % i)
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
        self.name = "ap%d" % (time.time_ns() % 10**9)
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
        other = "ot%d" % (time.time_ns() % 10**9)
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

if __name__ == "__main__":
    unittest.main()
