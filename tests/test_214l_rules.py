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

class ServerSide(unittest.TestCase):
    """Reglas evaluadas en el servidor: 3 lecturas seguidas abren el evento y la primera normal lo cierra. / Rules evaluated on the server."""
    R: ClassVar[list] = [{"m": "ups_charge", "o": "<", "v": 50, "lv": "crit", "on": True}, {"m": "pi_temp", "o": ">", "v": 65, "lv": "warn", "on": False}]

    def test_three_in_a_row_then_back(self):
        st, low, ok = {}, [("ups_charge", "u1", 40.0), ("pi_temp", "", 90.0)], [("ups_charge", "u1", 80.0)]
        self.assertEqual(ov.rules_tick(self.R, low, state=st), []); self.assertEqual(ov.rules_tick(self.R, low, state=st), [])
        ev = ov.rules_tick(self.R, low, state=st)
        self.assertEqual(ev, [("crit", "rule_on", {"n": "ups_charge", "w": "u1", "v": 40.0, "o": "<", "t": 50, "mod": "nut"})])
        self.assertEqual(ov.rules_tick(self.R, low, state=st), [])                         # still holding: no repeat
        self.assertEqual(ov.rules_tick(self.R, [], state=st), [])                          # no reading: unchanged
        self.assertEqual([e[:2] for e in ov.rules_tick(self.R, ok, state=st)], [("info", "rule_off")])
        self.assertEqual(ov.rules_tick(self.R, ok, state=st), [])

    def test_a_blip_does_not_count_and_muted_modules_are_skipped(self):
        st, low, ok = {}, [("ups_charge", "u1", 40.0)], [("ups_charge", "u1", 80.0)]
        for r in (low, low, ok, low, low): self.assertEqual(ov.rules_tick(self.R, r, state=st), [])
        for _ in range(4): self.assertEqual(ov.rules_tick(self.R, low, muted={"nut"}, state=st), [])
        self.assertEqual(ov.rules_tick([], low, state=st), []); self.assertEqual(st, {})       # removed rules are forgotten

    def test_metrics_store_and_ownership(self):
        auth = support.auth
        with auth._metric_lock: auth._metric_store.clear(); auth._metric_src.clear(); auth._metric_sent[0] = 0
        auth.metrics_report("nut", "s1", [("ups_charge", "u1", 40), ("ups_load", "u1", None), ("nas_cpu", "x", 5)])
        self.assertEqual(auth.metrics_all(), {"nut": [["ups_charge", "u1", 40.0]]})              # None skipped, another module's metric dropped
        auth.metrics_store("dns", [["dns_pct", "a", "9"], ["dns_pct", "b", float("inf")], ["dns_pct", "c", 7]])
        self.assertEqual(auth.metrics_all()["dns"], [["dns_pct", "c", 7.0]])
        self.assertNotIn("nut", auth.metrics_all(now=__import__("time").time() + auth.METRIC_STALE + 1))
        authrpc = support.load("auth/authrpc.py")
        svc = authrpc.Service(auth)
        self.assertEqual(svc.handle("wan", {"op": "metrics", "readings": [["wan_rtt", "", 12]]}), {"ok": True})
        self.assertEqual(svc.handle("overview", {"op": "metrics"})["metrics"]["wan"], [["wan_rtt", "", 12.0]])
        self.assertEqual(svc.handle("someone", {"op": "metrics", "readings": []}), {"error": "forbidden"})
        self.assertEqual(svc.handle("wan", {"op": "metrics"}), {"error": "forbidden"})
        with auth._metric_lock: auth._metric_store.clear(); auth._metric_src.clear()

    def test_modules_report_their_readings(self):
        for f, s in (("nut-monitor/server.py", 'auth.metrics_report("nut"'), ("nas-monitor/server.py", 'auth.metrics_report("nas"'),
                     ("proxmox-monitor/server.py", 'auth.metrics_report("pve"'), ("dns-monitor/server.py", 'auth.metrics_report("dns"'),
                     ("wan-monitor/server.py", 'auth.metrics_report("wan"')):
            self.assertIn(s, (ROOT / f).read_text(encoding="utf-8"), f)
        nas = support.load("nas-monitor/server.py")
        r = nas.rule_readings("N", {"cpu": {"pct": 5}, "mem": {"pct": 60}, "system": {"temp": 41}, "raids": [{"pct": 70}, {"pct": 95, "pool": True}, {"pct": 80}]})
        self.assertEqual(r, [("nas_cpu", "N", 5), ("nas_mem", "N", 60), ("nas_temp", "N", 41), ("nas_vol", "N", 80)])

    def test_rule_events_follow_the_metric_module(self):
        auth = support.auth
        rec = auth.read_events
        auth.read_events = lambda mods, limit: [{"m": "overview", "k": "rule_on", "p": {"mod": "nut"}}, {"m": "overview", "k": "rule_on", "p": {"mod": "pi"}},
                                                {"m": "overview", "k": "rule_on", "p": {"mod": "nas"}}, {"m": "nut", "k": "x"}]
        s = support.Server(ov.H)
        try:
            u = support.make_user("rlEv", {"nut": "readonly"})
            ev = s.call("GET", "/api/events", None, token=u)[1]["events"]
            self.assertEqual([e["p"]["mod"] if e["m"] == "overview" else e["m"] for e in ev], ["nut", "pi", "nut"])
        finally: s.close(); auth.read_events = rec


if __name__ == "__main__":
    unittest.main()
