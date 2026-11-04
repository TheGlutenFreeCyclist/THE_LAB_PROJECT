"""R142 isolated scientific/intent stress on the COMMITTED the_lab_app.py.

All external database, AI and activity credentials must be unset in CI.
No production I/O. Fixed PRNG seeds ensure reproducible tests.
"""
import copy
import hashlib
import json
import random
import sqlite3
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import the_lab_app as n

TARGET_SHA = "0fdd92a3d0b5226bfc48dd73fcaa1f9f586db6303190e1dbb67f238da8c42b04"
STAMP = "2026-11-04T12:00:00Z"
NOW = datetime(2026,11,4,15,0,tzinfo=n.ROME_TZ)
WID = "P5_5X3_EASYREC"
GOAL = "POWER_5"

def plan(minutes=75, day="2026-11-05", part="EVENING"):
    return {"schema": n.R142_AVAILABILITY_SCHEMA, "kind":"PLAN", "scope":"ONCE",
            "workout_id":WID,"goal_key":GOAL,"minutes":minutes,
            "local_date":day,"daypart":part,"saved_at_utc":STAMP}

def usual(minutes=50):
    return dict(plan(minutes),kind="TOO_LONG",scope="USUAL",
                local_date=None,daypart=None)

def slots():
    return {"next_slots":[
        {"date":"2026-11-05","start_minute":1100,"duration_hint_min":60.5,
         "restriction":"NONE","source":"RHYTHM","timing_confidence":"HIGH"},
        {"date":"2026-11-05","start_minute":1190,"duration_hint_min":60.5,
         "restriction":"NONE","source":"RHYTHM"},
        {"date":"2026-11-06","start_minute":360,"duration_hint_min":45.,
         "restriction":"NONE","source":"RHYTHM"},
        {"date":"2026-11-07","start_minute":1100,"duration_hint_min":70.,
         "restriction":"NO_INTENSITY","source":"RHYTHM"}]}

class QualityAvailabilityR142(unittest.TestCase):
    def test_00_code_hash_and_import(self):
        actual=hashlib.sha256(Path(n.__file__).read_bytes()).hexdigest()
        self.assertEqual(actual,TARGET_SHA)
        self.assertIn("R196.9.142",n.APP_VERSION)

    def test_01_once_window_does_not_double_book(self):
        base=slots(); untouched=copy.deepcopy(base)
        out=n._r142_adjust_slots(base,[plan()],NOW)
        self.assertEqual([s["duration_hint_min"] for s in out["next_slots"]],
                         [75,60.5,45.,70.])
        self.assertEqual(len(out["r142_availability_intent_audit"]["slots_adjusted"]),1)
        self.assertEqual(base,untouched)

    def test_02_usual_cap_and_once_override_and_calendar_restriction(self):
        base=slots(); out=n._r142_adjust_slots(base,[usual(),plan()],NOW)
        self.assertEqual([s["duration_hint_min"] for s in out["next_slots"]],
                         [75,50,45,70])
        self.assertFalse(out["r142_availability_intent_audit"]["issued_quality_by_intent"])
        self.assertTrue(out["r142_availability_intent_audit"]["rhythm_learning_unchanged"])

    def test_03_never_change_planned_or_restricted_slots(self):
        base=slots(); base["next_slots"][0]["is_planned_training"]=True
        out=n._r142_adjust_slots(base,[plan(),usual(30)],NOW)
        self.assertEqual(out["next_slots"][0]["duration_hint_min"],60.5)
        self.assertEqual(out["next_slots"][-1]["duration_hint_min"],70)

    def test_04_canonical_template_still_complete(self):
        t=n._R19696_LIBRARY_INDEX[WID]
        self.assertEqual(n._nova_quality_template_required_seconds(t,"DURABILITY")/60,73)
        self.assertEqual(n._nova_quality_template_required_seconds(t,"REPEATABILITY")/60,55)

    def test_05_HMAC_scopes_owner_goal_report_and_card(self):
        raw={"nova_decision":{"goal_key":GOAL},
             "nova_card3_workout_view":{"workout_id":WID}}
        with patch.object(n,"_v4891_prepare_snapshot_for_ui",side_effect=lambda d:d):
            def key(owner= "A", stamp=STAMP, goal=GOAL):
                r=copy.deepcopy(raw);r["nova_decision"]["goal_key"]=goal
                return n._r142_report_binding({"data":r,"generated_at_utc":stamp},owner)["token"]
            self.assertNotEqual(key("A"),key("B"))
            self.assertNotEqual(key(stamp="2026-11-04T12:01:00Z"),key("A"))
            self.assertNotEqual(key(goal="POWER_20"),key("A"))

    def test_06_explanation_evidence_not_fake_approval(self):
        d={"nova_card3_workout_view":{"workout_id":WID},
           "nova_prescription":{"inc120_planned_quality":{"dimension":"DURABILITY"},
             "fail_closed_reason":"NO_SCIENCE_APPROVED_TEMPLATE_FITS_DECLARED_TIME"},
           "quality_offer_integrity":{"state":"WITHHELD_FOR_ALTERNATION","offer_present":False},
           "coach_clock":{"next_slots":[{"duration_hint_min":60.5}]}}
        text=n._r142_card_copy(d)
        self.assertTrue(text["has_proven_time_conflict"])
        self.assertIn("73.0 minutes",text["easy_explanation"])
        self.assertIn("recent quality",text["easy_explanation"])
        d["nova_prescription"]["fail_closed_reason"]=""
        text=n._r142_card_copy(d)
        self.assertFalse(text["has_proven_time_conflict"])

    def test_07_intent_rows_never_calendar_events(self):
        with patch.object(n,"_R142_PLANNING_ITEMS_BEFORE",return_value=[
            {"id":"intent","note":"NOVA_QUALITY_INTENT_V1:{}"},
            {"id":"real","note":"ACTUAL CALENDAR ENTRY"}]):
            self.assertEqual([x["id"] for x in n.load_planning_items()],["real"])

    def test_08_legacy_and_product_SQL_segregation(self):
        captured=[]
        with patch.object(n,"_data_execute",side_effect=lambda owner,sql,params=(),fetch=False:captured.append((sql,params))):
            with patch.object(n,"_owner_personal_data_enabled",return_value=True):
                n._r142_write_intent("owner",plan())
            sql,params=captured.pop()
            self.assertNotIn("excluded.user_id",sql)
            converted,values=n._legacy_owner_storage_sql(sql,params)
            self.assertNotIn("user_id",converted.lower())
            self.assertEqual(converted.count("?"),len(values))
            with patch.object(n,"_owner_personal_data_enabled",return_value=False):
                n._r142_write_intent("owner",plan())
            self.assertIn("WHERE planning_items.user_id=excluded.user_id",captured[-1][0])

    def test_09_real_flask_POST_save_validation_and_stale_report(self):
        report={"data":{"nova_decision":{"goal_key":GOAL},
                        "nova_card3_workout_view":{"workout_id":WID}},
                "generated_at_utc":STAMP}
        with patch.object(n,"_v4891_prepare_snapshot_for_ui",side_effect=lambda d:d):
            binding=n._r142_report_binding(report,"ownerA")
        valid={"offer_binding":binding["token"],"intent_kind":"PLAN",
               "scope":"ONCE","minutes":"75","local_date":"2026-11-05","daypart":"EVENING"}
        saved=[]
        cases=[(valid,True),({**valid,"offer_binding":"0"*64},False),
               ({**valid,"minutes":"999"},False),({**valid,"minutes":"-1"},False),
               ({**valid,"local_date":"2029-11-05"},False),
               ({**valid,"daypart":"NIGHT"},False),
               ({**valid,"scope":"USUAL"},False)]
        with (patch.object(n,"require_login",return_value=True),
              patch.object(n,"load_latest_report",return_value=report),
              patch.object(n,"get_active_training_strategy_plan",return_value={"primary_goal":GOAL}),
              patch.object(n,"_v4891_prepare_snapshot_for_ui",side_effect=lambda d:d),
              patch.object(n,"_R142_PLANNING_ITEMS_BEFORE",return_value=[]),
              patch.object(n,"_r142_write_intent",side_effect=lambda owner,obj:saved.append((owner,obj))),
              patch.object(n,"get_rome_now",return_value=NOW)):
            for form,should_save in cases:
                old_len=len(saved)
                with n.app.test_request_context("/quality/intent",method="POST",data=form):
                    n.session["user_id"]="ownerA"
                    resp=n.r142_quality_intent()
                    self.assertEqual(resp.status_code,303)
                    self.assertIn("/last-report",resp.location)
                    self.assertEqual(len(saved)-old_len,1 if should_save else 0)
            self.assertEqual(len(saved),1)
            self.assertEqual(saved[0][0],"ownerA")
            self.assertTrue(saved[0][1]["not_an_execution_authorization"])
            self.assertTrue(saved[0][1]["not_an_observed_activity"])

    def test_10_stale_goal_and_race_reject_without_writes(self):
        report={"data":{"nova_decision":{"goal_key":GOAL},
                        "nova_card3_workout_view":{"workout_id":WID}},
                "generated_at_utc":STAMP}
        with patch.object(n,"_v4891_prepare_snapshot_for_ui",side_effect=lambda d:d):
            token=n._r142_report_binding(report,"ownerA")["token"]
        params={"offer_binding":token,"intent_kind":"PLAN","scope":"ONCE",
                "minutes":"75","local_date":"2026-11-05","daypart":"EVENING"}
        saved=[]
        with (patch.object(n,"require_login",return_value=True),
              patch.object(n,"load_latest_report",return_value=report),
              patch.object(n,"_v4891_prepare_snapshot_for_ui",side_effect=lambda d:d),
              patch.object(n,"_r142_write_intent",side_effect=lambda *a:saved.append(a)),
              patch.object(n,"get_rome_now",return_value=NOW)):
            with patch.object(n,"get_active_training_strategy_plan",return_value={"primary_goal":"POWER_20"}):
                with n.app.test_request_context("/quality/intent",method="POST",data=params):
                    n.session["user_id"]="ownerA"
                    self.assertEqual(n.r142_quality_intent().status_code,303)
            with (patch.object(n,"get_active_training_strategy_plan",return_value={"primary_goal":GOAL}),
                  patch.object(n,"_R142_PLANNING_ITEMS_BEFORE",return_value=[
                      {"kind":"RACE","start_date":"2026-11-05","end_date":"2026-11-05",
                       "restriction_type":"NONE"}])):
                with n.app.test_request_context("/quality/intent",method="POST",data=params):
                    n.session["user_id"]="ownerA"
                    self.assertEqual(n.r142_quality_intent().status_code,303)
            self.assertEqual(saved,[])

    def test_11_card3_grey_and_no_health_dependency(self):
        self.assertEqual(n.HOME_PAGE.count("nova-card3-grey-placeholder"),1)
        self.assertEqual(n.HOME_PAGE.count("class=\"r142-quality-planning\""),2)
        frag=Path(n.__file__).read_text().split("# INC122 / R196.9.142")[1]
        logic=frag.split("_R142_PANEL = ")[0]
        self.assertNotIn("get('nova_health')",logic)
        self.assertNotIn("build_training_rhythm(",logic)
        self.assertNotIn("build_nova_prescription(",logic)

    def test_12_25k_fuzzed_slot_scenarios(self):
        rng=random.Random(1969142)
        base={"next_slots":[]}
        for days in range(1,9):
            for j in range(4):
                base["next_slots"].append({
                    "date":"2026-11-%02d"%(4+days),
                    "start_minute":360+j*240,
                    "duration_hint_min":40+j*8,
                    "restriction":"NO_INTENSITY" if days%7==0 else "NONE",
                    "source":"RHYTHM","is_planned_training":False})
        original=copy.deepcopy(base)
        for i in range(25000):
            rule=plan(rng.randint(15,360),day="2026-11-%02d"%(5+i%8),
                      part=("MORNING","AFTERNOON","EVENING")[i%3])
            if i%2==0:rule["kind"]="TOO_LONG"
            if i%4==0:rule.update(scope="USUAL",local_date=None,daypart=None)
            out=n._r142_adjust_slots(base,[rule],NOW)
            self.assertEqual(len(out["next_slots"]),len(base["next_slots"]))
            self.assertEqual(base,original)
            self.assertNotIn("nova_health",out)
            self.assertFalse(out["r142_availability_intent_audit"]["issued_quality_by_intent"])
            for src,dest in zip(base["next_slots"],out["next_slots"]):
                self.assertEqual(src["start_minute"],dest["start_minute"])
                self.assertEqual(src["restriction"],dest["restriction"])
                if src["restriction"]!="NONE":
                    self.assertEqual(src["duration_hint_min"],dest["duration_hint_min"])
                self.assertFalse(dest.get("execution_authorized",False))
            if rule["scope"]=="ONCE":
                self.assertLessEqual(len(out["r142_availability_intent_audit"]["slots_adjusted"]),1)

    def test_13_15k_SQLite_retries_with_100_tenants(self):
        db=sqlite3.connect(":memory:")
        db.row_factory=sqlite3.Row
        db.execute("CREATE TABLE planning_items(id TEXT PRIMARY KEY,user_id TEXT,created_at_utc TEXT,kind TEXT,title TEXT,note TEXT,start_date TEXT,end_date TEXT,restriction_type TEXT,active INTEGER)")
        def write(owner,sql,params=(),fetch=False):
            cur=db.execute(sql,params)
            if fetch:return [dict(row) for row in cur.fetchall()]
            db.commit()
            return []
        try:
            with (patch.object(n,"_data_execute",side_effect=write),
                  patch.object(n,"_owner_personal_data_enabled",return_value=False)):
                for i in range(15000):
                    owner="stress-%03d"%(i%100)
                    item=(plan(minutes=15+i%345) if i%2 else usual(15+i%345))
                    n._r142_write_intent(owner,item)
                self.assertEqual(db.execute("SELECT COUNT(*) FROM planning_items").fetchone()[0],100)
                self.assertEqual(db.execute("SELECT COUNT(DISTINCT user_id) FROM planning_items").fetchone()[0],100)
                self.assertTrue(all(len(n._r142_intents("stress-%03d"%i))==1 for i in range(100)))
                self.assertEqual(n._r142_intents("unknown-owner"),[])
        finally:
            db.close()

if __name__=="__main__":
    start=time.monotonic()
    print("R142_STRESS_START",json.dumps({"sha256":TARGET_SHA,"scope":"isolated-branch-synthetic","external_io":False}))
    outcome=unittest.main(verbosity=2,exit=False)
    print("R142_STRESS_END",json.dumps({"tests":outcome.result.testsRun,
            "failures":len(outcome.result.failures),"errors":len(outcome.result.errors),
            "duration_seconds":round(time.monotonic()-start,2)}))
    if not outcome.result.wasSuccessful():raise SystemExit(1)
