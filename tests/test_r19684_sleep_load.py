"""R196.8.4 — missing sleep must be neutral; mild solo-load warning is not a permanent veto."""
import ast
from pathlib import Path
import unittest
from nova_load_guard import refine_training_state

SRC=Path(__file__).resolve().parents[1]/"the_lab_app.py"

def state(**overrides):
    obj=dict(state="RECOVERY", recovery_drivers=["ACUTE_CHRONIC_LOAD"],
             atl_ctl=1.20,load_ratio=1.06,ctl_delta_28=10.6,ramp_rate=2.2)
    obj.update(overrides)
    return obj

def metrics(sq=None):
    return dict(sleep_quality=sq,personal_baselines={
        "hrv":{"status":"Within baseline","color":"green"},
        "rhr":{"status":"Within baseline","color":"green"},
        "sleep":{"status":"WITHIN HABITUAL","color":"green"}})

class LoadAndSleep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=SRC.read_text(encoding="utf-8")
        cls.src=src
        tree=ast.parse(src)
        cls.score=next(n for n in tree.body if isinstance(n,ast.FunctionDef)
                       and n.name=="compute_race_readiness")

    def check(self,changed=None,m=None,trend=None,context=None):
        return refine_training_state(changed or state(),m or metrics(),trend,context)

    def test_beta_marginal_is_not_automatic_hold(self):
        x=self.check()
        self.assertEqual(x["state"],"BUILD")
        self.assertFalse(x["load_gate_review"]["hard_session_authorized"])

    def test_high_ratio_still_holds(self):
        self.assertEqual(self.check(state(atl_ctl=1.25))["state"],"RECOVERY")

    def test_real_load_spike_still_holds(self):
        self.assertEqual(self.check(state(load_ratio=1.36))["state"],"RECOVERY")

    def test_two_flags_still_hold(self):
        self.assertEqual(self.check(state(recovery_drivers=["ACUTE_CHRONIC_LOAD","RECOVERY_MARKERS"]))["state"],"RECOVERY")

    def test_poor_sleep_still_holds(self):
        self.assertEqual(self.check(m=metrics(4))["state"],"RECOVERY")

    def test_missing_hrv_never_claimed_recovered(self):
        m=metrics();m["personal_baselines"]["hrv"]={}
        self.assertEqual(self.check(m=m)["state"],"RECOVERY")

    def test_active_health_still_holds(self):
        self.assertEqual(self.check(context={"health_override":{"kind":"SICK"}})["state"],"RECOVERY")

    def test_race_still_holds(self):
        self.assertEqual(self.check(context={"next_race":{"days_away":8}})["state"],"RECOVERY")

    def test_bad_feeling_still_holds(self):
        self.assertEqual(self.check(trend={"label":"TRENDING DOWN"})["state"],"RECOVERY")

    def test_growth_absent_still_holds(self):
        self.assertEqual(self.check(state(ctl_delta_28=0))["state"],"RECOVERY")

    def test_ramp_excess_still_holds(self):
        self.assertEqual(self.check(state(ramp_rate=8))["state"],"RECOVERY")

    def test_idempotence(self):
        adjusted=self.check()
        self.assertIs(refine_training_state(adjusted,metrics()),adjusted)

    def test_sleep_missing_neutral_vs_grey_baseline(self):
        g={}
        exec(compile(ast.Module(body=[self.score],type_ignores=[]),str(SRC),"exec"),g)
        pb={"hrv":{"status":"Within baseline"},
            "rhr":{"status":"Within baseline"},
            "sleep":{"color":"grey"},"spo2":{"status":"No current data"}}
        none_score=g["compute_race_readiness"]("grey","grey",None,pb)[0]
        good_score=g["compute_race_readiness"]("grey","grey",2,pb)[0]
        poor_score=g["compute_race_readiness"]("grey","grey",4,pb)[0]
        self.assertEqual(none_score,60)
        self.assertGreater(good_score,none_score)
        self.assertLess(poor_score,none_score)

    def test_no_new_quality_execution_authority(self):
        self.assertIn("_v19684_refine_load(raw, metrics=metrics",self.src)
        self.assertIn("hard_session_authorized",Path(__file__).resolve().parents[1].joinpath("nova_load_guard.py").read_text(encoding="utf-8"))

if __name__=="__main__": unittest.main()
