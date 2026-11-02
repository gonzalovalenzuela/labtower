"""2.1.5b: en un contenedor, el servicio del panel (que usa sudo) no lleva las opciones de systemd que activan «no new privileges»."""
import os, re, shutil, subprocess, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMPLIES = ("ProtectKernelTunables", "ProtectKernelModules", "ProtectKernelLogs", "ProtectClock", "ProtectHostname", "RestrictRealtime",
           "RestrictSUIDSGID", "RestrictNamespaces", "LockPersonality", "SystemCallArchitectures", "RestrictAddressFamilies")

def units(in_container):
    """Runs install_service from debian/postinst against a temp dir, with a fake systemd-detect-virt."""
    src = (ROOT / "debian/postinst").read_text()
    fn = src[src.index("install_service() {"):]
    fn = fn[:fn.index("\n}\n") + 3]
    tmp = Path(tempfile.mkdtemp())
    try:
        (tmp / "bin").mkdir(); (tmp / "out").mkdir()
        fake = tmp / "bin" / "systemd-detect-virt"
        fake.write_text("#!/bin/sh\nexit %d\n" % (0 if in_container else 1)); fake.chmod(0o755)
        script = fn.replace("/etc/systemd/system/", str(tmp / "out") + "/") + '\nDATA_DIR=/var/lib/labtower PI_HOME=/opt/labtower\n' \
            'install_service admin-panel "Admin Panel" auth admin_panel.py none labtower-auth auth >/dev/null\n' \
            'install_service labtower-ups "UPS Monitor" nut-monitor server.py strict labtower-nut nut-monitor >/dev/null\n'
        r = subprocess.run(["bash", "-c", script], env={**os.environ, "PATH": f"{tmp / 'bin'}:{os.environ['PATH']}"}, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        return {p.name: p.read_text() for p in (tmp / "out").iterdir()}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

@unittest.skipUnless(shutil.which("bash"), "bash no está instalado")
class AdminUnit(unittest.TestCase):
    def test_container_leaves_out_the_options_that_imply_no_new_privileges(self):
        u = units(True)["admin-panel.service"]
        for k in IMPLIES: self.assertNotIn(k + "=", u, k)
        self.assertIn("ProtectControlGroups=true", u); self.assertIn("PrivateTmp=true", u)
    def test_vm_keeps_every_option(self):
        u = units(False)["admin-panel.service"]
        for k in IMPLIES: self.assertIn(k + "=", u, k)
    def test_other_services_keep_every_option_even_in_a_container(self):
        u = units(True)["labtower-ups.service"]
        for k in IMPLIES: self.assertIn(k + "=", u, k)
        self.assertIn("NoNewPrivileges=true", u)

if __name__ == "__main__": unittest.main()
