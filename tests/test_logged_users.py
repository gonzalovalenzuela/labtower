"""Usuarios conectados: respaldo por la lista de procesos cuando no hay utmp ni logind (DietPi, Debian 13)."""
import os, tempfile, unittest, pathlib, sys
from tests import support

auth = support.load("auth/auth.py")

def fake_proc(root, pid, cmd, tty_nr=0, start=1000):
    d = pathlib.Path(root, str(pid)); d.mkdir()
    d.joinpath("cmdline").write_bytes(cmd.encode().replace(b" ", b" ") + b"\0")
    # pid (comm) state ppid pgrp session tty_nr … starttime is field 22 (index 19 after the state)
    f = ["S", "1", "1", "1", str(tty_nr)] + ["0"] * 14 + [str(start * 100)]
    d.joinpath("stat").write_text(f"{pid} (x) " + " ".join(f) + "\n")

class LoggedUsers(unittest.TestCase):
    def test_ssh_and_login_shell(self):
        with tempfile.TemporaryDirectory() as r:
            pathlib.Path(r, "stat").write_text("cpu 1\nbtime 1700000000\n")
            fake_proc(r, 100, "sshd-session: root@pts/0")
            fake_proc(r, 101, "sshd-session: root [priv]")        # helper of the session: not a user
            fake_proc(r, 102, "sshd: ana@pts/3")
            fake_proc(r, 103, "-bash", tty_nr=(4 << 8) | 1)       # console tty1, owner = this test's user
            fake_proc(r, 104, "python3 server.py")
            got = auth._proc_users(r)
            self.assertTrue({("root", "pts/0"), ("ana", "pts/3")} <= {(u["user"], u["tty"]) for u in got})
            self.assertTrue(any(u["tty"] == "tty1" for u in got))
            self.assertFalse(any("priv" in u["user"] for u in got))
            self.assertTrue(all(u["since"] >= 1700000000 for u in got))
    def test_missing_proc(self):
        self.assertEqual(auth._proc_users("/nonexistent-proc"), [])

if __name__ == "__main__": unittest.main()
