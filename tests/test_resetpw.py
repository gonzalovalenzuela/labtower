"""labtower-resetpw: restablece la contraseña desde la consola (misma lógica que el Admin Panel)."""
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "auth" / "resetpw.py"

def run(env, *args, stdin=None):
    e = {k: v for k, v in os.environ.items() if not k.startswith("LABTOWER_")}
    e.update(env)
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, env=e, input=stdin, timeout=60)

class ResetPw(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp()) / "auth"; self.d.mkdir()
        self.env = {"LABTOWER_USERS": str(self.d / "users.json")}
        prep = ("import sys; sys.path.insert(0, %r); import auth\n"
                "with auth.users_lock():\n"
                " u = {'admin': {'password_hash': auth._hash('old-password-1'), 'permissions': {'wol': 'admin'}, 'must_change_password': False, 'totp': {'secret': 'JBSWY3DPEHPK3PXP', 'last': 0, 'since': 1, 'recovery': []}},\n"
                "      'ana': {'password_hash': auth._hash('ana-password-1'), 'permissions': {}, 'must_change_password': False}}\n"
                " auth.save_users(u)\n"
                "s = auth._load_sessions(); s['tok-ana'] = {'username': 'ana', 'expires': 9999999999}; s['tok-adm'] = {'username': 'admin', 'expires': 9999999999}; auth._save_sessions(s)\n"
                "auth.throttle_fail('u:ana')\n" % str(ROOT / "auth"))
        r = subprocess.run([sys.executable, "-c", prep], capture_output=True, text=True, env={**{k: v for k, v in os.environ.items() if not k.startswith("LABTOWER_")}, **self.env}, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
    def users(self): return json.loads((self.d / "users.json").read_text())

    def test_random_password_forces_change_and_closes_only_that_users_sessions(self):
        r = run(self.env, "ana")
        self.assertEqual(r.returncode, 0, r.stderr)
        pw = [l for l in r.stdout.splitlines() if l.startswith("New password: ")][0].split(": ", 1)[1]
        self.assertGreaterEqual(len(pw), 12)
        u = self.users()
        self.assertTrue(u["ana"]["must_change_password"])
        self.assertTrue(u["ana"]["password_hash"].startswith("scrypt$"))
        self.assertNotIn(pw, json.dumps(u))
        s = json.loads((self.d / "sessions.json").read_text())
        self.assertTrue(all(v["username"] != "ana" for v in s.values())); self.assertEqual(len(s), 1)
        self.assertIn("password_reset", (self.d / "audit.log").read_text())

    def test_default_user_is_admin_and_2fa_is_kept_unless_asked(self):
        self.assertEqual(run(self.env).returncode, 0)
        self.assertIn("totp", self.users()["admin"])
        r = run(self.env, "--disable-2fa", "admin")
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("2FA disabled", r.stdout)
        self.assertNotIn("totp", self.users()["admin"])

    def test_unknown_user_and_list(self):
        r = run(self.env, "nadie")
        self.assertEqual(r.returncode, 1); self.assertIn("does not exist", r.stderr); self.assertIn("ana", r.stderr)
        r = run(self.env, "--list")
        self.assertEqual(r.returncode, 0); self.assertIn("admin  (2FA on)", r.stdout); self.assertIn("ana", r.stdout)
        self.assertEqual(run(self.env, "--list", "--no-change").returncode, 0)

    def test_ask_checks_the_password_policy(self):
        code = ("import sys; sys.path.insert(0, %r); import resetpw\n"
                "for args, exc in ((('ana', 'short'), ValueError), (('nadie',), KeyError)):\n"
                "    try: resetpw.reset(*args)\n"
                "    except exc: pass\n"
                "    else: sys.exit('no error for %%r' %% (args,))\n"
                "pw, _ = resetpw.reset('ana', '  a-good-password-9  ', must_change=False)\n"
                "assert pw == 'a-good-password-9', pw\n" % str(ROOT / "auth"))
        e = {k: v for k, v in os.environ.items() if not k.startswith("LABTOWER_")}; e.update(self.env)
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=e, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertFalse(self.users()["ana"]["must_change_password"])

    def test_wrapper_script(self):
        t = (ROOT / "scripts" / "labtower-resetpw").read_text()
        self.assertIn("runuser -u labtower-auth", t); self.assertIn('id -u', t); self.assertIn("python3 -I", t)

if __name__ == "__main__":
    unittest.main()
