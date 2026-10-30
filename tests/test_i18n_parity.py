"""Traducciones: cada módulo tiene las mismas claves en inglés y en español, y los textos de los eventos del Resumen también / every module has the same keys in English and Spanish."""
import json, re, shutil, subprocess, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULES = ["auth", "dns-monitor", "nas-monitor", "net-monitor", "nut-monitor", "proxmox-monitor", "wan-monitor", "wol-console"]

JS = r"""
const fs=require('fs'),vm=require('vm');
const src=fs.readFileSync(process.argv[1],'utf8');
const i=src.search(/^const LANG\s*=\s*\{/m); let j=src.indexOf('{',i),d=0,k=j,q=null,e=false;
for(;k<src.length;k++){const c=src[k];
  if(q){if(e){e=false;continue}if(c==='\\'){e=true;continue}if(c===q)q=null;continue}
  if(c==='"'||c==="'"||c==='`'){q=c;continue}
  if(c==='/'&&src[k+1]==='/'){k=src.indexOf('\n',k);continue}
  if(c==='{')d++;if(c==='}'){d--;if(d===0)break}}
const L=vm.runInNewContext('('+src.slice(j,k+1)+')',{});
const flat=(o,p='')=>Object.entries(o).flatMap(([k,v])=>v&&typeof v==='object'?flat(v,p+k+'.'):[[p+k,typeof v]]);
console.log(JSON.stringify({en:flat(L.en).map(x=>x[0]),es:flat(L.es).map(x=>x[0])}));
"""

@unittest.skipUnless(shutil.which("node"), "node not installed")
class Parity(unittest.TestCase):
    def test_every_module_has_the_same_keys_in_en_and_es(self):
        for m in MODULES:
            with self.subTest(module=m):
                out = subprocess.run(["node", "-e", JS, str(ROOT / m / "static" / "app.js")], capture_output=True, text=True, timeout=30)
                self.assertEqual(out.returncode, 0, out.stderr)
                d = json.loads(out.stdout); en, es = set(d["en"]), set(d["es"])
                self.assertEqual(sorted(en - es), [], "missing in ES"); self.assertEqual(sorted(es - en), [], "missing in EN")

    def test_overview_events_have_the_same_keys_and_placeholders(self):
        s = (ROOT / "overview/static/app.js").read_text()
        i = s.index("const EVT"); blk = s[i:i + 40000]
        def part(name):
            a = blk.index(f"{name}:{{"); depth = 0; q = None; esc = False
            for n in range(a + len(name) + 1, len(blk)):
                c = blk[n]
                if q:
                    if esc: esc = False
                    elif c == "\\": esc = True
                    elif c == q: q = None
                    continue
                if c in "\"'`": q = c; continue
                if c == "{": depth += 1
                if c == "}":
                    depth -= 1
                    if depth == 0: return dict(re.findall(r"(\w+):'((?:[^'\\]|\\.)*)'", blk[a + len(name) + 1:n + 1]))
        en, es = part("en"), part("es")
        self.assertEqual(sorted(set(en) ^ set(es)), [])
        for k in en: self.assertEqual(sorted(re.findall(r"\{(\w+)\}", en[k])), sorted(re.findall(r"\{(\w+)\}", es[k])), k)

if __name__ == "__main__":
    unittest.main()
