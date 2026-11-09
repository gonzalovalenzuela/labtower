"""2.1.4l: reglas de alerta del Resumen / Overview alert rules."""
import json
import subprocess
import textwrap
import unittest
from pathlib import Path
from typing import ClassVar

from tests import support

ov = support.load("overview/server.py")
ROOT = Path(__file__).resolve().parent.parent

class Clean(unittest.TestCase):
    ok: ClassVar[dict] = {"m": "pi_temp", "o": ">", "v": 65, "lv": "warn", "on": True}
    def test_valid(self):
        r, e = ov.clean_rules([self.ok, {**self.ok, "m": "ups_charge", "o": "<", "v": 50.5, "lv": "crit", "on": False}])
        self.assertEqual(len(r), 2); self.assertEqual(e, "")
    def test_rejects_bad_rules(self):
        for bad in ({**self.ok, "m": "nope"}, {**self.ok, "o": "=="}, {**self.ok, "lv": "info"}, {**self.ok, "v": "65"}, {**self.ok, "v": True},
                    {**self.ok, "v": float("nan")}, {**self.ok, "v": 1e12}, {**self.ok, "on": "yes"}, "x"):
            self.assertIsNone(ov.clean_rules([bad])[0], bad)
        self.assertIsNone(ov.clean_rules("x")[0])
        self.assertIsNone(ov.clean_rules([self.ok] * (ov.RULES_MAX + 1))[0])
    def test_extra_keys_are_dropped(self):
        r, _ = ov.clean_rules([{**self.ok, "x": "<script>"}]); self.assertEqual(set(r[0]), {"m", "o", "v", "lv", "on"})

class Api(unittest.TestCase):
    def test_get_and_post(self):
        s = support.Server(ov.H)
        adm = support.make_user("rlA", support.ADMIN); ro = support.make_user("rlR", support.READONLY)
        self.assertEqual(s.call("GET", "/api/rules", None, token=ro)[1]["can_edit"], False)
        self.assertEqual(s.call("POST", "/api/rules", {"rules": [Clean.ok]}, token=ro)[0], 403)
        st, _body = s.call("POST", "/api/rules", {"rules": [Clean.ok]}, token=adm); self.assertEqual(st, 200)
        g = s.call("GET", "/api/rules", None, token=ro)[1]; self.assertEqual(g["rules"], [Clean.ok])
        self.assertEqual(s.call("POST", "/api/rules", {"rules": [{**Clean.ok, "m": "bad"}]}, token=adm)[0], 400)
        s.call("POST", "/api/rules", {"rules": []}, token=adm)

class Client(unittest.TestCase):
    def test_metric_lists_match(self):
        src = (ROOT / "overview/static/rules.js").read_text()
        import re
        keys = set(re.findall(r"\b([a-z]+_[a-z]+): \['", src))
        self.assertEqual(keys, set(ov.RULE_METRICS))
    def test_eval_in_node(self):
        js = textwrap.dedent("""
          const fs=require('fs');let issues=[];const lang='en',esc=s=>s,$=()=>null,jget=async()=>({rules:[
            {m:'pi_temp',o:'>',v:65,lv:'warn',on:true},{m:'ups_charge',o:'<',v:50,lv:'crit',on:true},{m:'nas_cpu',o:'>',v:10,lv:'warn',on:false}],can_edit:false});
          global.window=global;global.document={addEventListener(){}};
          eval(fs.readFileSync('overview/static/rules.js','utf8'));
          (async()=>{await rulesUpdate();
            const ok=(v)=>({status:'fulfilled',value:v});
            const R={sys:ok({temp:70,mem:{pct:10}}),nut:ok({servers:[{status:{ups:{u1:{'battery.charge':'40'},u2:{'battery.charge':'90'}}}}]}),nas:ok({nas:[{name:'n',snap:{data:{cpu:{pct:99}}}}]})};
            const sev=rulesEval(R);console.log(JSON.stringify({sev,n:issues.length,lv:issues.map(i=>i.lv)}));})();""")
        out = subprocess.run(["node", "-e", js], cwd=ROOT, capture_output=True, text=True, timeout=30, check=False)
        self.assertEqual(json.loads(out.stdout.strip().splitlines()[-1]), {"sev": "crit", "n": 2, "lv": ["warn", "crit"]}, out.stderr)

if __name__ == "__main__":
    unittest.main()
