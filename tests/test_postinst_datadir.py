"""ES: El postinst solo «devuelve» los datos a labtower tras un purge (root:root, modo 700), no en cada actualización (root:labtower, 750).
EN: The postinst hands the data back to labtower only after a purge (root:root, mode 700), not on every upgrade (root:labtower, 750)."""
import pathlib, re, subprocess, tempfile, unittest

SRC = (pathlib.Path(__file__).resolve().parent.parent / "debian" / "postinst").read_text()


class DataDirHandBack(unittest.TestCase):
    def cond(self):
        m = re.search(r'^if (\[ -d "\$DATA_DIR" \].*?); then\n\s+find "\$DATA_DIR" -xdev -exec chown', SRC, re.M)
        self.assertIsNotNone(m, "condition not found in debian/postinst")
        return m.group(1)

    def run_with(self, fake):
        with tempfile.TemporaryDirectory() as d:
            script = f'stat() {{ echo "{fake}"; }}\nDATA_DIR="{d}"\nif {self.cond()}; then echo YES; else echo NO; fi'
            return subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=10).stdout.strip()

    def test_after_a_purge_the_data_is_handed_back(self):
        self.assertEqual(self.run_with("0:0:700"), "YES")

    def test_a_normal_upgrade_leaves_the_data_alone(self):
        for st in ("0:999:750", "0:0:750", "999:999:750", "0:999:700"):
            self.assertEqual(self.run_with(st), "NO", st)


if __name__ == "__main__":
    unittest.main()
