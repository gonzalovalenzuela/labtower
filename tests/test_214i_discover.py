"""2.1.4i: monitores sugeridos en el Resumen / Suggested monitors in the Overview."""
import json, shutil, subprocess, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JS = (ROOT / "overview/static/discover.js").read_text()

# Ejecuta la lógica real de discover.js en node con un DOM mínimo. / Runs the real discover.js logic in node with a minimal DOM.
HARNESS = r"""
const src=require('fs').readFileSync(process.argv[1],'utf8');
const store={};let html='',cls=new Set(['hide']);
global.lang='en';global.esc=s=>String(s);global.lvl=k=>({pve:3,nut:3,dns:3,nas:1})[k]||0;
global.localStorage={getItem:k=>store[k]||null,setItem:(k,v)=>{store[k]=v}};
global.document={addEventListener(){}};
global.$=id=>id==='c-sug'?{classList:{add:c=>cls.add(c),remove:c=>cls.delete(c)},set innerHTML(v){html=v},get innerHTML(){return html}}:null;
global.window=global;
eval(src);
const ok=(v)=>({status:'fulfilled',value:v});
const net={hosts:[
 {ip:'192.0.2.10',hostname:'a',online:true,ports:[{port:8006}]},
 {ip:'192.0.2.11',hostname:'b',online:true,ports:[{port:3493}]},
 {ip:'192.0.2.12',hostname:'c',online:true,ports:[{port:53},{port:443}]},
 {ip:'192.0.2.13',hostname:'d',online:true,ports:[{port:5000}]},
 {ip:'192.0.2.14',hostname:'e',online:true,ports:[{port:53}]},
 {ip:'192.0.2.15',hostname:'f',online:false,ports:[{port:8006}]},
 {ip:'192.0.2.16',hostname:'node9',online:true,ports:[{port:8006}]},
 {ip:'192.0.2.17',hostname:'g',online:true,ports:[3493]}]};
discoverUpdate({net:ok(net),pve:ok({clusters:[{host:'192.0.2.99',snap:{data:{nodes:[{node:'node9'}]}}}]}),nut:ok({servers:[{host:'192.0.2.17'}]}),dns:ok({servers:[]}),nas:ok({nas:[]})});
const rows=[...html.matchAll(/<span class="sug-n"><b>(.*?)<\/b>/g)].map(m=>m[1]);
console.log(JSON.stringify({rows,hidden:cls.has('hide')}));
"""

@unittest.skipUnless(shutil.which("node"), "node not installed")
class Discover(unittest.TestCase):
    def run_node(self):
        out = subprocess.run(["node", "-e", HARNESS, str(ROOT / "overview/static/discover.js")], capture_output=True, text=True, timeout=30)
        self.assertEqual(out.returncode, 0, out.stderr); return json.loads(out.stdout)
    def test_suggests_only_unconfigured_online_services_the_user_can_admin(self):
        r = self.run_node()
        # a (8006) yes; b (3493) yes; c (53+443) yes; d (5000) NO: nas is only readonly; e (53 alone) no; f offline no; node9 already a node of a cluster; g (3493) already configured
        self.assertEqual(r["rows"], ["a", "b", "c"]); self.assertFalse(r["hidden"])
    def test_page_and_hooks(self):
        h = (ROOT / "overview/static/index.html").read_text(); app = (ROOT / "overview/static/app.js").read_text()
        self.assertLess(h.index('src="search.js"'), h.index('src="discover.js"')); self.assertIn('id="c-sug"', h)
        self.assertIn("discoverUpdate(R)", app); self.assertIn("discoverLang()", app)
        self.assertNotIn("onclick=", JS)
    def test_same_keys_in_both_languages(self):
        code = "const s=%s;const m=s.match(/en: \\{(.*?)\\},\\n\\s+es: \\{(.*?)\\}\\n  \\};/s);const k=t=>[...t.matchAll(/(\\w+): '/g)].map(x=>x[1]).sort();console.log(JSON.stringify([k(m[1]),k(m[2])]))" % json.dumps(JS)
        out = subprocess.run(["node", "-e", code], capture_output=True, text=True, timeout=30)
        en, es = json.loads(out.stdout); self.assertEqual(en, es); self.assertGreater(len(en), 8)

if __name__ == "__main__": unittest.main()
