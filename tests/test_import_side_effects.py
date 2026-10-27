"""Importar un módulo no debe crear archivos, carpetas ni hilos: eso se hace al arrancar (bloque __main__)."""
import os, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
MODULES = ["auth/auth.py", "auth/admin_panel.py", "auth/teleporter_api.py", "wol-console/server.py", "nut-monitor/server.py",
           "net-monitor/server.py", "proxmox-monitor/server.py", "nas-monitor/server.py", "overview/server.py"]
PROBE = r"""
import importlib.util, sys, threading
sys.path.insert(0, sys.argv[2])
before = set(threading.enumerate())
spec = importlib.util.spec_from_file_location("probe_mod", sys.argv[1]); m = importlib.util.module_from_spec(spec); sys.modules["probe_mod"] = m
spec.loader.exec_module(m)
extra = [t.name for t in threading.enumerate() if t not in before]
print("THREADS:" + ",".join(extra))
"""
class ImportSideEffects(unittest.TestCase):
    def test_import_is_quiet(self):
        for rel in MODULES:
            with self.subTest(module=rel), tempfile.TemporaryDirectory() as tmp:
                env = dict(os.environ, PICONSOLE_USERS=os.path.join(tmp, "users.json"), PICONSOLE_SESSIONS=os.path.join(tmp, "sessions.json"))
                r = subprocess.run([sys.executable, "-I", "-c", PROBE, str(ROOT / rel), str(ROOT / "auth")], env=env, capture_output=True, text=True, timeout=60)
                self.assertEqual(r.returncode, 0, r.stderr[-400:])
                self.assertEqual(sorted(os.listdir(tmp)), [], f"{rel} creó archivos al importarse")
                self.assertIn("THREADS:\n", r.stdout + "\n", f"{rel} arrancó hilos al importarse: {r.stdout}")
if __name__ == "__main__": unittest.main()
