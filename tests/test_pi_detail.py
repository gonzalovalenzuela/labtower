"""Detalle de la Raspberry Pi: lectores de sesiones (utmp y logind), forma de la respuesta y reparto entre administradores y lectores."""
import os, struct, tempfile, time, unittest
from pathlib import Path
from tests import support
auth = support.auth

def utmp_record(user, tty, host, since, typ=7):
    return struct.pack("<hh i 32s 4s 32s 256s hh i ii 16s 20s".replace(" ", ""), typ, 0, 123, tty.encode(), b"id", user.encode(), host.encode(), 0, 0, 0, since, 0, b"", b"")

class SessionReaders(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="sess-")
    def write(self, name, text): Path(self.d, name).write_text(text)

    def test_utmp_record_is_384_bytes_and_parsed(self):
        rec = utmp_record("ana", "pts/9", "10.0.0.5", 1792526000); self.assertEqual(len(rec), 384)
        p = Path(self.d, "utmp"); p.write_bytes(rec + utmp_record("dead", "pts/1", "", 1, typ=8))     # tipo 8 = proceso muerto
        self.assertEqual(auth._utmp_users(str(p)), [{"user": "ana", "tty": "pts/9", "host": "10.0.0.5", "since": 1792526000}])

    def test_utmp_missing_or_empty(self):
        self.assertEqual(auth._utmp_users(os.path.join(self.d, "nope")), [])
        p = Path(self.d, "utmp"); p.write_bytes(b""); self.assertEqual(auth._utmp_users(str(p)), [])

    def test_logind_sessions(self):      # Debian 13 / Raspberry Pi OS nuevo ya no llena utmp
        self.write("42", "UID=1000\nUSER=gonzalo\nSTATE=active\nTYPE=tty\nCLASS=user\nTTY=pts/1\nREMOTE=1\nREMOTE_HOST=192.168.0.69\nREALTIME=1792526000000000\n")
        self.write("c1", "USER=gonzalo\nCLASS=user\nSTATE=active\nTYPE=tty\nTTY=tty1\nREALTIME=1792520000000000\n")
        self.write("c2", "USER=gdm\nCLASS=greeter\nSTATE=active\n")
        self.write("c3", "USER=old\nCLASS=user\nSTATE=closing\n")
        self.write("42.ref", "x")
        r = auth._logind_users(self.d)
        self.assertEqual(sorted((u["user"], u["tty"], u["host"]) for u in r), [("gonzalo", "pts/1", "192.168.0.69"), ("gonzalo", "tty1", "")])
        self.assertEqual([u["since"] for u in r if u["tty"] == "pts/1"], [1792526000])

    def test_logind_missing_dir(self):
        self.assertEqual(auth._logind_users(os.path.join(self.d, "nope")), [])

class SystemDetail(unittest.TestCase):
    def test_shape_for_everyone(self):
        d = auth.system_detail(False)
        for k in ("host", "uptime", "boot", "cpu_total", "cpu_cores", "mem_detail", "disks", "net", "thermal", "time"):
            self.assertIn(k, d)
        self.assertFalse(d["full"])
        for k in ("users", "top_cpu", "top_mem", "failed_units"):
            self.assertNotIn(k, d, f"{k} solo para administradores")
        self.assertTrue(all(n["mac"] is None for n in d["net"]), "la MAC es solo para administradores")

    def test_shape_for_admins(self):
        d = auth.system_detail(True)
        self.assertTrue(d["full"])
        for k in ("users", "top_cpu", "top_mem", "failed_units", "procs_total"):
            self.assertIn(k, d)
        self.assertLessEqual(len(d["top_cpu"]), 8); self.assertLessEqual(len(d["top_mem"]), 8)
        self.assertTrue(all({"pid", "name", "cpu", "rss", "user"} <= set(p) for p in d["top_mem"]))

    def test_no_command_lines_leak(self):
        import json
        self.assertNotIn("cmdline", json.dumps(auth.system_detail(True)))

class OverviewCache(unittest.TestCase):
    def test_detail_is_shared_for_two_seconds(self):
        ov = support.load("overview/server.py"); ov._pd_cache.clear()
        calls = []; real = auth.system_detail
        auth.system_detail = lambda full: (calls.append(full), {"full": full})[1]
        try:
            ov.pi_detail_cached(True); ov.pi_detail_cached(True); ov.pi_detail_cached(False)
        finally:
            auth.system_detail = real; ov._pd_cache.clear()      # no dejar el resultado falso en la caché
        self.assertEqual(calls, [True, False], "dos llamadas seguidas deben compartir el resultado")
if __name__ == "__main__": unittest.main()
