"""INC106: actual R136 issuer-MAC contract, owner-scoped report SQL and fuel oracle.

All people, workouts and secrets are synthetic. Authenticated production owner
storage, issuer provenance, athlete clinical decisions and signed live snapshots
remain separate gates; do not label this as a genuine E2E issuance.
"""
import copy
import json
import os
import tempfile
import unittest
from unittest.mock import patch

for key in ("DATABASE_URL", "THE_LAB_OWNER_DATABASE_URL", "ICU_API_KEY",
            "ICU_ATHLETE_ID", "GARMIN_EMAIL", "GARMIN_PASSWORD",
            "ANTHROPIC_API_KEY", "THE_LAB_STANDARD_AI_API_KEY",
            "THE_LAB_PLATFORM_AI_API_KEY"):
    os.environ[key] = ""
os.environ["PRODUCT_SECURITY_STRICT"] = "0"
os.environ["SESSION_COOKIE_SECURE"] = "0"
import the_lab_app as nova

STAGE_KEY = "inc106-staging-issuer-contract-key-with-more-than-32-chars"


def fully_compiled_synthetic_offer():
    composition = {
        "state":"COMPLETE","total_seconds":3600,
        "total_min_low":60,"total_min_high":60,
        "primary_work_seconds":900,"interval_recovery_seconds":600,
        "blocks":[
            {"type":"PREPARATION","duration_seconds":900},
            {"type":"CANONICAL_INTERVALS","duration_seconds":1500,
             "quality_work_seconds":900,"recovery_seconds":600},
            {"type":"COOLDOWN","duration_seconds":1200},
        ]
    }
    workout = {
        "nova_workout_id":"INC106_SYNTHETIC_5X3",
        "nova_canonical_plan_id":"inc106-fake-plan",
        "title":"INC106 invented 5 x 3 minutes",
        "duration":"60 min","intensity_class":"vo2",
        "main_set":"5 x 180 s hard with controlled recovery",
        "date":None,"power_prescription":{
            "low_watts":300,"high_watts":320,"source":"SYNTHETIC_DO_NOT_EXECUTE"},
        "session_composition":composition,
    }
    return {"offer_id":"inc106-fake-offer","workout_id":workout["nova_workout_id"],
            "dose_fingerprint":"inc106-synthetic-fingerprint",
            "canonical_plan_id":"inc106-fake-plan","source":"SYNTHETIC_INTEGRITY_ONLY",
            "offer_status":"OFFERED","workout":workout}


class Inc106IssuerMacContract(unittest.TestCase):
    def test_actual_issuer_hmac_binds_audit_owner_and_workout(self):
        offer = fully_compiled_synthetic_offer()
        audit = {"state":"PASS","science_origin":"SYNTHETIC_ONLY",
                 "canonical_quality":"NOT_AN_ISSUANCE"}
        self.assertTrue(nova._nova_inc075_valid_compiled_duration(offer["workout"]))
        with patch.object(nova, "SECRET_KEY", STAGE_KEY):
            digest = nova._nova_inc076_composition_digest(offer,"stage-alpha")
            self.assertIsInstance(digest,str)
            self.assertEqual(len(digest),64)
            seal = nova._nova_inc080_issuer_mac(offer,"stage-alpha",audit)
            self.assertEqual(len(seal or ""),64)
            self.assertEqual(seal,nova._nova_inc080_issuer_mac(
                copy.deepcopy(offer),"stage-alpha",copy.deepcopy(audit)))
            self.assertNotEqual(seal,nova._nova_inc080_issuer_mac(
                offer,"stage-beta",audit),"wrong owner accepted")
            changed = copy.deepcopy(offer)
            changed["workout"]["power_prescription"]["high_watts"] += 10
            self.assertNotEqual(seal,nova._nova_inc080_issuer_mac(
                changed,"stage-alpha",audit),"wattage was not MAC-bound")
            changed = copy.deepcopy(offer)
            changed["workout"]["date"] = "2026-11-05"
            self.assertNotEqual(seal,nova._nova_inc080_issuer_mac(
                changed,"stage-alpha",audit),"calendar insertion was not MAC-bound")
            changed = copy.deepcopy(offer)
            changed["workout"]["session_composition"]["blocks"][1]["quality_work_seconds"] = 870
            self.assertNotEqual(seal,nova._nova_inc080_issuer_mac(
                changed,"stage-alpha",audit),"duration alteration was not MAC-bound")
            altered_audit = dict(audit, science_origin="INVENTED_DIFFERENT_SOURCE")
            self.assertNotEqual(seal,nova._nova_inc080_issuer_mac(
                offer,"stage-alpha",altered_audit),"audit/provenance not MAC-bound")
            failed_audit = dict(audit,state="FAIL")
            self.assertNotEqual(seal,nova._nova_inc080_issuer_mac(
                offer,"stage-alpha",failed_audit))
        # No claim of a real issued offer: this exercises the actual signer.

    def test_no_mac_with_untrusted_key_or_invalid_composition(self):
        offer=fully_compiled_synthetic_offer()
        audit={"state":"PASS"}
        with patch.object(nova,"SECRET_KEY","change-this-key"):
            self.assertIsNone(nova._nova_inc080_issuer_mac(offer,"stage-alpha",audit))
        with patch.object(nova,"SECRET_KEY",STAGE_KEY):
            bad=copy.deepcopy(offer)
            bad["workout"]["session_composition"]["total_seconds"]=4200
            self.assertIsNone(nova._nova_inc080_issuer_mac(bad,"stage-alpha",audit))
            self.assertIsNone(nova._nova_inc080_issuer_mac(offer,"stage-alpha",None))
            self.assertIsNone(nova._nova_inc080_issuer_mac(offer,None,audit))


class Inc106OwnerScopedSqlite(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="nova-inc106-reports-")
        self.old=(nova.SQLITE_PATH,nova._DB_READY,nova.DATABASE_URL,
                  nova.OWNER_PERSONAL_DATABASE_URL)
        nova.SQLITE_PATH=os.path.join(self.tmp.name,"owner-staging.sqlite")
        nova._DB_READY=False
        nova.DATABASE_URL=""
        nova.OWNER_PERSONAL_DATABASE_URL=""
        nova.init_memory_db()

    def tearDown(self):
        (nova.SQLITE_PATH,nova._DB_READY,nova.DATABASE_URL,
         nova.OWNER_PERSONAL_DATABASE_URL)=self.old
        self.tmp.cleanup()

    def test_load_latest_report_uses_real_owner_where_and_does_not_expose_qa(self):
        for owner,marker in (("inc106-alpha","A"),("inc106-beta","B")):
            # This is an explicitly seeded storage fixture, not a claim that
            # the issuer/save guard generated a valid report.
            payload=json.dumps({"synthetic_owner_marker":marker,
                                "__qa_replay_v4831":{"test_only":"hidden"}})
            nova._db_execute(
                "INSERT INTO latest_report (singleton_id,user_id,generated_at_utc,"
                "generated_at_local,app_version,payload_json) VALUES (?,?,?,?,?,?)",
                (owner,owner,"2026-11-03T09:00:00Z",
                 "2026-11-03T10:00:00+01:00","INC106 staging",payload))
        alpha=nova.load_latest_report(owner_user_id="inc106-alpha")
        beta=nova.load_latest_report(owner_user_id="inc106-beta")
        self.assertEqual(alpha["data"],{"synthetic_owner_marker":"A"})
        self.assertEqual(beta["data"],{"synthetic_owner_marker":"B"})
        self.assertNotIn("__qa_replay_v4831",alpha["data"])
        self.assertNotIn("__qa_replay_v4831",beta["data"])
        self.assertIsNone(nova.load_latest_report(owner_user_id="inc106-unknown"))
        only_meta=nova.load_latest_report(include_payload=False,
                                          owner_user_id="inc106-alpha")
        self.assertNotIn("data",only_meta)
        self.assertNotIn("qa_replay",only_meta)
        with_replay=nova.load_latest_report(include_qa_replay=True,
                                            owner_user_id="inc106-alpha")
        self.assertTrue(with_replay.get("qa_replay_available"))
        self.assertEqual(with_replay["qa_replay"]["test_only"],"hidden")
        # Private QA route authorization is separately tested by INC105.


class Inc106NumericFuelOracle(unittest.TestCase):
    def test_predeclared_gph_targets_under_tolerance(self):
        cases=(
            # kind, environment, profile, min, tolerance, expected (low, high).
            ("VO2","OUTDOOR","VO2",90,70,(30,60)),
            ("VO2","INDOOR","VO2",90,70,(20,40)),
            ("RECOVERY","OUTDOOR","RECOVERY",45,70,(0,20)),
            ("ENDURANCE","OUTDOOR","ENDURANCE",210,70,(40,60)),
            ("THRESHOLD","OUTDOOR","THRESHOLD",90,35,(30,35)),
            ("VO2","OUTDOOR","VO2",90,None,(30,30)),
        )
        for kind,env,profile,minutes,established,expected in cases:
            with self.subTest(kind=kind,environment=env,minutes=minutes,
                              established=established):
                fi=({"established_gph":established} if established is not None
                    else {"next_practice_gph":30})
                result=nova._intra_fueling_strategy(
                    kind,env,profile,minutes,metabolic_context={
                        "fueling_intelligence":fi,"glycogen_pressure":"LOW"})
                self.assertEqual((result["low_gph"],result["high_gph"]),expected)
                self.assertIn("g",result["display"])
                self.assertTrue(result.get("duration_driver"))

    def test_no_unverified_race_hourly_target(self):
        ctx={"fueling_intelligence":{"observed_recorded_gph":90}}
        result=nova._intra_fueling_strategy("RACE","OUTDOOR","RACE",120,
                                           metabolic_context=ctx,
                                           session_item={"environment":"OUTDOOR",
                                                         "duration_min":120})
        self.assertIsNone(result["high_gph"])
        self.assertEqual(result["display"],"Race target still learning")

    def test_real_plan_intra_matches_approved_hourly_boundary(self):
        context={"glycogen_pressure":"LOW","fueling_intelligence":
                 {"established_gph":70}}
        session={"title":"Synthetic VO2","session_kind":"VO2",
                 "planned_demand":"VO2","intensity":"HARD",
                 "environment":"OUTDOOR","duration_min":90,
                 "date":"2026-11-04","start_minute":1080}
        rows=nova.build_nutrition_plan([session],context)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["kind"],"VO2")
        self.assertEqual(rows[0]["intra_cho"],"30–60 g CHO/h")
        self.assertEqual(rows[0]["duration_min"],90)
        self.assertIn("CHO",rows[0]["intra_total"])
        self.assertNotEqual(rows[0]["post_cho"],None)


if __name__=="__main__":
    unittest.main(verbosity=2)
