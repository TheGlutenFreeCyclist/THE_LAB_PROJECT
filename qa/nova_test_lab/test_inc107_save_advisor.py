"""INC107 two-track gate: real scientific save boundary and real day advisor.

This is a non-production synthetic regression. It never changes a live issuer,
a personal user report, or DTM. A preview lacking scientific authority results
in an explicitly reported skip, NOT a fabricated end-to-end pass.
"""
import copy
import os
import tempfile
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

for k in ("DATABASE_URL","THE_LAB_OWNER_DATABASE_URL","ICU_API_KEY",
          "ICU_ATHLETE_ID","GARMIN_EMAIL","GARMIN_PASSWORD",
          "ANTHROPIC_API_KEY","THE_LAB_STANDARD_AI_API_KEY",
          "THE_LAB_PLATFORM_AI_API_KEY"):
    os.environ[k] = ""
os.environ["PRODUCT_SECURITY_STRICT"] = "0"
os.environ["SESSION_COOKIE_SECURE"] = "0"

import the_lab_app as nova


class Inc107SaveGuardRealProducer(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="inc107-real-save-")
        self.prev = (nova.SQLITE_PATH, nova._DB_READY, nova.DATABASE_URL,
                     nova.OWNER_PERSONAL_DATABASE_URL)
        nova.SQLITE_PATH = os.path.join(self.tmp.name, "isolated.sqlite")
        nova._DB_READY = False
        nova.DATABASE_URL = ""
        nova.OWNER_PERSONAL_DATABASE_URL = ""
        nova.init_memory_db()

    def tearDown(self):
        (nova.SQLITE_PATH,nova._DB_READY,nova.DATABASE_URL,
         nova.OWNER_PERSONAL_DATABASE_URL) = self.prev
        self.tmp.cleanup()

    def test_save_rejects_unsealed_incomplete_report_without_sql_row(self):
        try:
            nova.save_latest_report(
                {"cross_module_authority_audit":{"final_pass":False},
                 "authority_final_pass":False},
                owner_user_id="inc107-synthetic-alpha")
        except (RuntimeError, ValueError, KeyError, TypeError, AttributeError):
            pass  # The production guard can reject malformed inputs earlier.
        else:
            self.fail("Incomplete scientific report was persisted")
        self.assertIsNone(nova.load_latest_report(
            owner_user_id="inc107-synthetic-alpha"))

    def test_guarded_preview_save_owner_roundtrip_if_authorized(self):
        now = datetime(2026,11,3,9,0,tzinfo=ZoneInfo("Europe/Rome"))
        data = nova.build_preview_data()
        # Never mock, replace or bypass the genuine save-time authority guard.
        validated = nova._v87_cross_module_authority_guard(
            copy.deepcopy(data), repair=True)
        if not (validated.get("cross_module_authority_audit") or {}).get("final_pass"):
            self.skipTest("INC107_NOT_VERIFIED_preview_not_scientifically_saveable")
        meta = nova.save_latest_report(
            validated, now=now, owner_user_id="inc107-synthetic-alpha")
        saved = nova.load_latest_report(owner_user_id="inc107-synthetic-alpha")
        self.assertEqual(saved["generated_at_utc"],meta["generated_at_utc"])
        self.assertTrue((saved.get("data") or {}).get(
            "cross_module_authority_audit",{}).get("final_pass"))
        self.assertIsNone(nova.load_latest_report(
            owner_user_id="inc107-synthetic-beta"))


class Inc107ActualAdvisorNonScheduling(unittest.TestCase):
    @staticmethod
    def baseline(count, ratio=0.12):
        return {
            "coach_clock":{"iso":"2026-11-04","today_activity_count":count,
                           "today_activities_text":"Easy endurance, morning",
                           "rhythm":{"recent":{"double_day_pct":0.8,
                                               "training_days":24}}},
            "energy_today_sessions":count,
            "energy_today_load_ratio":ratio,
            "energy_today_duration_ratio":ratio,
            "physiological_state":{"systems":[
                {"label":"AUTONOMIC","status":"BASELINE","status_class":"green"},
                {"label":"RECOVERY","status":"BASELINE","status_class":"green"},
                {"label":"TRAINING LOAD","status":"BASELINE","status_class":"green"},
            ]},
            "health_observatory":{"signals":{}},
            "next_quality_direction":{"goal_key":"POWER_5",
                                      "direction_only":True},
            "next_quality_offer":None,
            "next_sessions":[],
        }

    def test_one_easy_session_never_completes_day(self):
        data=self.baseline(1)
        before=copy.deepcopy(data)
        result=nova._nova_r196979_quality_day_advisor(data)
        self.assertFalse(result["day_complete"])
        self.assertTrue(result["session_count_is_never_a_veto"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["changes_decision"])
        self.assertFalse(result["changes_prescription"])
        self.assertNotEqual(result["code"],"NOT_SUGGESTED")
        self.assertEqual(data,before)

    def test_recovery_alert_may_warn_without_calendar_mutation(self):
        data=self.baseline(1)
        data["health_observatory"]["acute_red_flag"]=True
        result=nova._nova_r196979_quality_day_advisor(data)
        self.assertEqual(result["code"],"NOT_SUGGESTED")
        self.assertFalse(result["changes_decision"])
        self.assertFalse(result["changes_prescription"])
        self.assertNotIn("date",result)


if __name__=="__main__":
    unittest.main(verbosity=2)
