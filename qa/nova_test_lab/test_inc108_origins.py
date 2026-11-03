"""INC108 fully synthetic repetition-ledger replay through native R136 watt model.

The fabricated DEVICE_LAPS label here is *not* a verified device receipt and
must never be treated as owner-authenticated or executable issuer authority.
It tests original-science numerical provenance *mechanics* only.
"""
import copy
import os
import unittest
from datetime import date

for k in ("DATABASE_URL","THE_LAB_OWNER_DATABASE_URL","ICU_API_KEY",
          "ICU_ATHLETE_ID","GARMIN_EMAIL","GARMIN_PASSWORD",
          "ANTHROPIC_API_KEY","THE_LAB_STANDARD_AI_API_KEY",
          "THE_LAB_PLATFORM_AI_API_KEY"):
    os.environ[k]=""
os.environ["PRODUCT_SECURITY_STRICT"]="0"
import the_lab_app as nova

DAY=date(2026,11,3)
WID="P5_5X3_EASYREC"
DIM="SPECIFIC_DOSE"


def original_repetition_fixture():
    event={
        "activity_id":"INC108_SYNTHETIC_EVENT_NOT_FROM_DEVICE",
        "date":"2026-11-02","strong":True,
        "activity_truth_source":"DEVICE_LAPS",
        "source":"DEVICE_LAPS",
        "avg_watts":340.0,"cv_pct":1.4,
        "interval_secs":180,"reps":5,
        "recovery_secs":300,
        "recovery_observation_complete":True,
        "recovery_pair_count":4,
        "recovery_pair_expected":4
    }
    ledger={"repeatability":{"events":[event]}}
    return ledger,event


def replay(ledger, dimension=DIM, work_overrides=None):
    tpl=nova._R19696_LIBRARY_INDEX[WID]
    band=nova._v1943_band(tpl,evidence_ledger=ledger,
        ftp_anchor=None,as_of_date=DAY.isoformat(),dimension=dimension)
    work={"nova_workout_id":WID,
          "nova_prescription_dimension":dimension,
          "power_prescription":band}
    work.update(work_overrides or {})
    road={"scientific_progression":{"dimension":dimension}}
    proof=nova._nova_inc083_science_replay(
        work,ledger,None,road,today=DAY)
    return band,proof


class Inc108OriginalRepetitionProof(unittest.TestCase):
    def test_synthetic_native_model_replays_equal_comparable_repeats(self):
        ledger,_=original_repetition_fixture()
        band,proof=replay(ledger)
        self.assertEqual(band.get("source"),"COMPARABLE_VERIFIED_REPEATED_WORK")
        self.assertEqual(band.get("state"),"PRESCRIBED")
        self.assertEqual(band.get("repeatability_state"),"VERIFIED_COMPARABLE_REPEATS")
        self.assertTrue(proof.get("accepted"),proof.get("reason"))
        self.assertEqual(proof.get("state"),"PASS")
        self.assertNotIn("execution_authorized",proof)

    def test_synthetic_invalid_origin_and_recovery_fail_closed(self):
        ledger,event=original_repetition_fixture()
        for kind in ("duplicate_activity","wrong_truth_source","longer_recovery",
                     "stale_event","altered_observed_watts","missing_repeats"):
            with self.subTest(kind=kind):
                bad=copy.deepcopy(ledger)
                row=bad["repeatability"]["events"][0]
                if kind=="duplicate_activity":bad["repeatability"]["events"].append(copy.deepcopy(row))
                if kind=="wrong_truth_source":row["activity_truth_source"]="UNVERIFIED_TEXT"
                if kind=="longer_recovery":row["recovery_secs"]=420
                if kind=="stale_event":row["date"]="2026-08-01"
                if kind=="altered_observed_watts":row["avg_watts"]=7000
                if kind=="missing_repeats":row["reps"]=1
                _,proof=replay(bad)
                self.assertFalse(proof.get("accepted"),
                                 "Invalid fabricated evidence was accepted: "+kind)

    def test_model_and_replay_reject_mismatched_issued_band(self):
        ledger,_=original_repetition_fixture()
        tpl=nova._R19696_LIBRARY_INDEX[WID]
        band=nova._v1943_band(tpl,evidence_ledger=ledger,ftp_anchor=None,
                              as_of_date=DAY.isoformat(),dimension=DIM)
        self.assertEqual(band.get("state"),"PRESCRIBED")
        wrong=dict(band,high_watts=band["high_watts"]+15)
        work={"nova_workout_id":WID,"nova_prescription_dimension":DIM,
              "power_prescription":wrong}
        proof=nova._nova_inc083_science_replay(
            work,ledger,None,{"scientific_progression":{"dimension":DIM}},today=DAY)
        self.assertFalse(proof.get("accepted"))


if __name__=="__main__":
    unittest.main(verbosity=2)
