"""Coherencia del repositorio: versión única, copias compartidas idénticas, textos en los dos idiomas y sintaxis de JS y shell."""
import hashlib
import re
import shutil
import subprocess
import unittest
from pathlib import Path
from typing import ClassVar

ROOT = Path(__file__).resolve().parents[1]
MODULES = ["wol-console", "nut-monitor", "net-monitor", "proxmox-monitor", "nas-monitor", "dns-monitor", "wan-monitor", "vpn-monitor", "uptime-monitor", "overview", "auth"]

class Versions(unittest.TestCase):
    def test_version_file_control_and_changelog_agree(self):
        v = (ROOT / "VERSION").read_text().strip()
        self.assertRegex(v, r"^\d+\.\d+(\.\d+)?[a-z]?$")
        ctrl = re.search(r"^Version:\s*(\S+)", (ROOT / "debian/control").read_text(), re.MULTILINE).group(1)
        top = re.search(r"^## (\S+)", (ROOT / "CHANGELOG.md").read_text(), re.MULTILINE).group(1)
        self.assertEqual((ctrl, top), (v, v), "VERSION, debian/control y la primera entrada del CHANGELOG deben coincidir")

class License(unittest.TestCase):
    """Desde la 1.3 el proyecto es PolyForm Noncommercial 1.0.0 (uso comercial solo con permiso del autor)."""
    def test_license_file_and_docs_agree(self):
        lic = (ROOT / "LICENSE").read_text()
        self.assertTrue(lic.startswith("Required Notice: Copyright"), "PolyForm exige la línea «Required Notice:»")
        for clave in ("PolyForm Noncommercial License 1.0.0", "Noncommercial Purposes", "Personal Uses", "No Liability", "polyformproject.org/licenses/noncommercial/1.0.0"):
            self.assertIn(clave, lic)
        self.assertNotIn("Permission is hereby granted, free of charge", lic, "quedó texto de la licencia MIT")
        for readme in ("README.md", "README.en.md"):
            txt = (ROOT / readme).read_text()
            self.assertIn("PolyForm Noncommercial 1.0.0", txt, readme)
            self.assertNotRegex(txt, r"(?m)^MIT\b", f"{readme} todavía dice MIT")

    def test_debian_copyright_names_the_same_license(self):
        c = (ROOT / "debian/copyright").read_text()
        self.assertIn("License: PolyForm-Noncommercial-1.0.0", c)
        self.assertIn("Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/", c)

class SharedAssets(unittest.TestCase):
    """Estos archivos se copian a mano a varias carpetas: si una copia cambia sola, la página se comporta distinto según el módulo."""
    SHARED = ("charts.js", "timefmt.js", "csp-bind.js", "footer.js", "ipcard.js", "ipcard.css", "theme.js", "theme.css", "nav.js", "nav.css")
    def test_copies_are_identical(self):
        for name in self.SHARED:
            with self.subTest(file=name):
                digests = {m: hashlib.sha256(p.read_bytes()).hexdigest() for m in MODULES if (p := ROOT / m / "static" / name).is_file()}
                if name.startswith("nav"):
                    extras = (ROOT / "assets" / name,)
                elif name == "footer.js":           # la página de inicio también la lleva / the home page carries it too
                    extras = (ROOT / "home" / name,)
                elif name.startswith("theme"):      # además de la copia maestra y la página de inicio / plus the master copy and the home page
                    extras = (ROOT / "assets/theme" / name, ROOT / "home" / name)
                else: extras = ()
                for extra in extras: digests[str(extra.relative_to(ROOT))] = hashlib.sha256(extra.read_bytes()).hexdigest()
                self.assertGreaterEqual(len(digests), 2, f"{name} no se encontró en varios módulos")
                self.assertEqual(len(set(digests.values())), 1, f"{name} difiere entre módulos: {digests}")

    def test_every_page_shows_the_version_footer(self):
        """Todas las páginas con sesión (módulos, Resumen/kiosko, inicio, cambio de contraseña) cargan footer.js."""
        pages = [ROOT / m / "static" / "index.html" for m in MODULES] + [ROOT / "home/index.html", ROOT / "auth/static/change-password.html"]
        for page in pages:
            with self.subTest(page=str(page.relative_to(ROOT))):
                self.assertIn('src="footer.js"', page.read_text())
                self.assertTrue((page.parent / "footer.js").is_file())

    def test_every_script_in_index_exists(self):
        for m in MODULES:
            idx = ROOT / m / "static" / "index.html"
            if not idx.is_file(): continue
            for src in re.findall(r'<script[^>]+src="([^"]+)"', idx.read_text()):
                with self.subTest(module=m, script=src):
                    self.assertTrue((ROOT / m / "static" / src).is_file() or src.startswith(("/", "http")), f"{m}: falta {src}")

    def test_no_inline_script_or_handlers(self):      # CSP estricta: script-src 'self'
        for m in MODULES:
            idx = ROOT / m / "static" / "index.html"
            if not idx.is_file(): continue
            html = idx.read_text()
            with self.subTest(module=m):
                self.assertEqual(re.findall(r"<script(?![^>]*\bsrc=)[^>]*>", html), [], "script en línea")
                self.assertEqual(re.findall(r'\son(?:click|change|input|load|error|submit|keydown|keyup)=', html), [], "manejador en línea")

NODE_KEYS = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[1], 'utf8');
const m = /\bconst (LANG|TXT)\s*=\s*\{/.exec(src);
if (!m) { console.log(JSON.stringify({missing: true})); process.exit(0); }
let i = m.index + m[0].length - 1, depth = 0, q = null, esc = false;
for (let j = i; j < src.length; j++) {
  const c = src[j];
  if (q) { if (esc) esc = false; else if (c === '\\') esc = true; else if (c === q) q = null; continue; }
  if (c === "'" || c === '"' || c === '`') { q = c; continue; }
  if (c === '{') depth++;
  if (c === '}' && --depth === 0) { var lit = src.slice(i, j + 1); break; }
}
const o = new Function('return ' + lit)();
console.log(JSON.stringify({en: Object.keys(o.en || {}), es: Object.keys(o.es || {})}));
"""

@unittest.skipUnless(shutil.which("node"), "node no está instalado")
class Languages(unittest.TestCase):
    def test_en_and_es_have_the_same_keys(self):
        import json
        for m in MODULES:
            f = ROOT / m / "static" / "app.js"
            with self.subTest(module=m):
                r = subprocess.run(["node", "-e", NODE_KEYS, str(f)], capture_output=True, text=True, check=False)
                self.assertEqual(r.returncode, 0, r.stderr[-300:])
                d = json.loads(r.stdout)
                self.assertFalse(d.get("missing"), "no se encontró la tabla de textos (const LANG / TXT)")
                self.assertGreater(len(d["en"]), 20)
                self.assertEqual(sorted(set(d["en"]) - set(d["es"])), [], "faltan en español")
                self.assertEqual(sorted(set(d["es"]) - set(d["en"])), [], "faltan en inglés")

@unittest.skipUnless(shutil.which("node"), "node no está instalado")
class JavaScriptSyntax(unittest.TestCase):
    def test_all_static_js_parses(self):
        for f in sorted(ROOT.glob("*/static/*.js")):
            with self.subTest(file=str(f.relative_to(ROOT))):
                r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True, check=False)
                self.assertEqual(r.returncode, 0, r.stderr[-300:])

@unittest.skipUnless(shutil.which("bash"), "bash no está instalado")
class ShellSyntax(unittest.TestCase):
    def test_scripts_parse(self):
        files = [*ROOT.glob("scripts/*"), *(ROOT / "debian").glob("p*")]
        for f in files:
            if not f.is_file() or f.suffix == ".py": continue
            head = f.read_text(errors="ignore").splitlines()[:1]
            if not head or "sh" not in head[0]: continue
            with self.subTest(file=str(f.relative_to(ROOT))):
                self.assertEqual(subprocess.run(["bash", "-n", str(f)], capture_output=True, text=True, check=False).returncode, 0)
if __name__ == "__main__": unittest.main()


class Rename(unittest.TestCase):
    """El proyecto se llamaba Pi Console hasta la 1.4. El nombre viejo solo puede quedar donde sirve para migrar o para leer cosas antiguas."""
    ALLOWED: ClassVar[set] = {"CHANGELOG.md", "CHANGELOG.en.md", "README.md", "README.en.md", "RELEASE_NOTES_2.0.md", "debian/postinst", "debian/postrm", "debian/control", "auth/auth.py",
               "auth/teleporter_api.py", "scripts/teleporter.sh", "tests/test_repo_consistency.py", "tests/test_service_names.py"}
    def test_old_name_only_where_it_is_needed(self):
        out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
        bad = []
        for rel in out:
            p = ROOT / rel
            if rel in self.ALLOWED or not p.is_file() or p.suffix in (".png", ".jpg", ".ico"):
                continue
            if re.search(r"pi-console|Pi Console|PICONSOLE|piconsole", p.read_text(errors="ignore"), re.IGNORECASE):
                bad.append(rel)
        self.assertEqual(bad, [], "nombre antiguo fuera de los archivos de migración")

    def test_old_backup_names_are_still_accepted(self):
        api = (ROOT / "auth/teleporter_api.py").read_text()
        sh = (ROOT / "scripts/teleporter.sh").read_text()
        for name, text in (("teleporter_api.py", api), ("teleporter.sh", sh)):
            self.assertIn("(labtower|pi-console)-", text, name)
        pat = re.compile(re.search(r'NAME_RE\s*=\s*re\.compile\(r"([^"]+)"\)', api).group(1))
        for ok in ("labtower-host-20261027_101500.tar.gz", "pi-console-host-20260901_020000.tar.gz", "upload-20261027_101500.tar.gz"):
            self.assertRegex(ok, pat)
        self.assertNotRegex("../pi-console-x.tar.gz", pat)

    def test_package_replaces_old_package(self):
        ctrl = (ROOT / "debian/control").read_text()
        self.assertRegex(ctrl, r"(?m)^Package: labtower$")
        self.assertRegex(ctrl, r"(?m)^Conflicts: pi-console$")
        self.assertRegex(ctrl, r"(?m)^Replaces: pi-console$")

class Python39(unittest.TestCase):
    """debian/control declara python3 (>= 3.9): el código empaquetado debe importar en 3.9.
    EN: debian/control declares python3 (>= 3.9): packaged code must import on 3.9."""
    def test_packaged_code_runs_on_python_39(self):
        import ast
        ctrl = (ROOT / "debian/control").read_text()
        self.assertIn("python3 (>= 3.9)", ctrl, "si cambia el mínimo, ajusta este test")
        files = subprocess.run(["git", "ls-files", "*.py"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
        # tests/ no se empaqueta; assets/brand es una herramienta de desarrollo.
        # EN: tests/ is not packaged; assets/brand is a development tool.
        files = [f for f in files if not f.startswith(("tests/", "assets/brand/"))]
        self.assertTrue(files)
        for f in files:
            src = (ROOT / f).read_text()
            tree = ast.parse(src, f, feature_version=(3, 9))
            if "from __future__ import annotations" in src:
                continue
            for n in ast.walk(tree):
                anns = [n.annotation] if isinstance(n, (ast.AnnAssign, ast.arg)) else [n.returns] if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) else []
                for a in anns:
                    bad = a is not None and any(isinstance(x, ast.BinOp) and isinstance(x.op, ast.BitOr) for x in ast.walk(a))
                    self.assertFalse(bad, f"{f}:{a.lineno if a else 0}: «X | Y» en una anotación necesita «from __future__ import annotations» en Python 3.9")
