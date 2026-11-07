"""UPS Monitor: gráfico de autonomía (battery.runtime) por UPS, al final del detalle, solo si la UPS informa runtime; en minutos,
con la batería y la carga en el tooltip.
EN: UPS Monitor: runtime chart (battery.runtime) per UPS, at the end of the detail, only when the UPS reports runtime; in minutes,
with the battery charge and the load in the tooltip."""
import time
import unittest
from pathlib import Path

from tests import support

m = support.load("nut-monitor/server.py")
ROOT = Path(__file__).resolve().parents[1]


class History(unittest.TestCase):
    def test_history_carries_the_runtime(self):
        m.DATA_DIR.mkdir(parents=True, exist_ok=True); m.db_init()
        now = int(time.time())
        with m._db_lock:
            conn = m.db_connect()
            try:
                conn.execute("DELETE FROM history WHERE srv_id='rt'")
                conn.executemany("INSERT INTO history (srv_id,ups,ts,charge,runtime,load,vin,vout,watts,temp) VALUES ('rt','u1',?,100,?,20,220,220,90,0)",
                                 [(now - 120, 1800), (now - 60, 1500)])
                conn.commit()
            finally:
                conn.close()
        rows = m.db_query("rt", "u1", since_ts=now - 3600)
        self.assertEqual([r["runtime"] for r in rows], [1800, 1500])


class Page(unittest.TestCase):
    def setUp(self): self.js = (ROOT / "nut-monitor/static/app.js").read_text()

    def test_chart_is_last_and_only_with_runtime(self):
        i = self.js.index("nutChartHtml(key,'t'):''}")
        self.assertIn("${runtime>0?nutChartHtml(key,'r'):''}", self.js[i:i + 80])
        self.assertIn("r: {pfx:'rchart', tip:'rtooltip', title:'chartTitle_runtime', ranges:rchartRanges}", self.js)

    def test_minutes_and_tooltip(self):
        i = self.js.index("if(type==='r') return")
        part = self.js[i:i + 700]
        for k in ("prep:p=>({rtmin:p.runtime>0?p.runtime/60:null})", "t('gaugeLabel_battery')", "t('gaugeLabel_load')"):
            self.assertIn(k, part, k)
        for k in ("chartTitle_runtime:", "chartLegend_runtime:"): self.assertEqual(self.js.count(k), 2, k)

    def test_every_chart_goes_through_the_table(self):
        self.assertIn("Object.keys(NUT_CH).forEach(ty=>", self.js)
        self.assertNotIn("type==='t' ? 'tchart'", self.js)


if __name__ == "__main__":
    unittest.main()
