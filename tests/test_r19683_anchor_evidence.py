"""R196.8.3: isolated authority/evidence invariants, no Flask import."""
import ast,copy,unittest
from datetime import date,datetime
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[1]/"the_lab_app.py"
class TestR19683(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  s=SOURCE.read_text(encoding="utf-8");ast.parse(s);cls.src=s
  tree=ast.parse(s)
  cls.functions=[next(n for n in reversed(tree.body) if isinstance(n,ast.FunctionDef) and n.name==name)
   for name in ("_v19683_effective_ledger","build_nova_prescription")]
 def env(self,prescribed=None):
  scope=dict(copy=copy,date=date,get_rome_now=lambda:datetime(2026,10,17),
   _v153_plan_slot=lambda d:(d.get("date"),d.get("period")),
   R19683_SCHEMA="test",_r19683_prescribe_before=lambda *a,**kw:copy.deepcopy(prescribed))
  exec(compile(ast.Module(body=self.functions,type_ignores=[]),str(SOURCE),"exec"),scope)
  return scope
 def ledger(self,day="2026-10-18"):
  a=dict(status="PLANNED",date=day,period="RHYTHM",title="quality",
   main_set="WORK TARGET 335 W",nova_workout_id="q",prescription_fingerprint="fp")
  return dict(primary_anchor=a,prescription_history=[dict(a,prescription_status="ACTIVE")])
 def slot(self,day="2026-10-18",kind="EASY",source="RHYTHM"):
  return [dict(date=day,period="RHYTHM",source=source,intensity=kind,
   intensity_class="recovery" if kind=="EASY" else "threshold",restriction="NONE")]
 def test_historical_watts_preserved_but_not_executable(self):
  prior=self.ledger();before=copy.deepcopy(prior)
  out=self.env()["_v19683_effective_ledger"](prior,self.slot(),now=datetime(2026,10,17))
  self.assertEqual(prior,before)
  self.assertEqual(out["primary_anchor"]["main_set"],"WORK TARGET 335 W")
  self.assertEqual(out["primary_anchor"]["status"],"PLANNED")
  self.assertEqual(out["primary_anchor"]["effective_execution_authority"],"NOT_IN_CURRENT_ATHLETE_PLAN")
  self.assertEqual(out["prescription_history"][0]["effective_status"],"REPLACED_BY_CANONICAL_EASY")
 def test_other_day_untouched(self):
  a=self.ledger();self.assertIs(a,self.env()["_v19683_effective_ledger"](a,self.slot("2026-10-19"),now=datetime(2026,10,17)))
 def test_hard_untouched(self):
  a=self.ledger();self.assertIs(a,self.env()["_v19683_effective_ledger"](a,self.slot(kind="HARD"),now=datetime(2026,10,17)))
 def test_plan_owned_untouched(self):
  a=self.ledger();self.assertIs(a,self.env()["_v19683_effective_ledger"](a,self.slot(source="PLANNED"),now=datetime(2026,10,17)))
 def test_past_untouched(self):
  a=self.ledger("2026-10-16");self.assertIs(a,self.env()["_v19683_effective_ledger"](a,self.slot("2026-10-16"),now=datetime(2026,10,17)))
 def test_quality_deferral_does_not_schedule_test_or_power(self):
  p=dict(status="EASY_ONLY",fail_closed_reason="WORKOUT_LIBRARY_NO_CANDIDATE",
   raw_sessions=[dict(intensity="EASY")],hard_prescription_available=False)
  out=self.env(p)["build_nova_prescription"]({"goal_key":"POWER_20"},{},
   adaptive_roadmap={"test":{"state":"BASELINE BUILD","label":"20-min test"}})
  self.assertEqual(out["raw_sessions"],p["raw_sessions"])
  self.assertTrue(out["evidence_gap_guidance"]["no_test_scheduled"])
  self.assertIn("20-min test",out["evidence_gap_guidance"]["message"])
  self.assertEqual(out["status"],"EASY_ONLY")
 def test_existing_quality_unchanged(self):
  p=dict(status="PRESCRIBED")
  self.assertEqual(self.env(p)["build_nova_prescription"]({},{}),p)
 def test_third_card_only_and_fuel_unchanged(self):
  self.assertIn("if data.nova_prescription and data.nova_prescription.evidence_gap_guidance",self.src)
  self.assertIn("data.nutrition_plan[si]",self.src)
if __name__=="__main__":unittest.main()
