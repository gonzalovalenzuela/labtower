"""Ningún archivo del repositorio debe llevar referencias a sesiones de Claude; el hook commit-msg las quita de los commits."""
import os, subprocess, tempfile, unittest, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
NEEDLE = "claude.ai/" + "code/session"          # armado a mano para que este archivo no se delate a sí mismo
HOOK = ROOT / "scripts/git-hooks/commit-msg"

def run_hook(text, env=None):
    with tempfile.NamedTemporaryFile("w+", suffix=".msg", delete=False) as f:
        f.write(text); path = f.name
    try:
        subprocess.run(["sh", str(HOOK), path], check=True, env={**os.environ, **(env or {})})
        return pathlib.Path(path).read_text()
    finally: os.unlink(path)

class NoSessionRefs(unittest.TestCase):
    def test_files_are_clean(self):
        files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split("\n")
        bad = []
        for rel in filter(None, files):
            if rel in ("scripts/git-hooks/commit-msg", "tests/test_no_session_refs.py"): continue     # the guard names the thing it blocks
            p = ROOT / rel
            try: t = p.read_text()
            except Exception: continue
            if NEEDLE in t or "Claude-Session:" in t: bad.append(rel)
        self.assertEqual(bad, [])
    def test_hook_strips_references(self):
        msg = "Titulo\n\ncuerpo\n\nCo-Authored-By: X <x@y.z>\nClaude-Session: https://" + NEEDLE + "_01\n"
        out = run_hook(msg)
        self.assertNotIn("Claude-Session", out); self.assertNotIn(NEEDLE, out)
        self.assertIn("Co-Authored-By: X", out); self.assertTrue(out.startswith("Titulo\n\ncuerpo"))
    def test_env_var_allows_them(self):
        msg = "T\n\nClaude-Session: https://" + NEEDLE + "_01\n"
        self.assertEqual(run_hook(msg, {"LABTOWER_ALLOW_CLAUDE_SESSION": "1"}), msg)

if __name__ == "__main__": unittest.main()
