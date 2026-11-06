"""INC132 Z3 research precompiler acceptance; synthetic by definition."""
import unittest
from pathlib import Path
from datetime import date
from inc132_tempo_blocks import precompile_tempo_from_test_catalog as precompile
from inc132_catalog_inventory import catalog

SOURCE=Path(__file__).resolve().parents[2]/"the_lab_app.py"
OWNER="synthetic-tempo-owner"
DAY=date(2026,11,6)

def athlete(**patch):
    d=dict(owner_id=OWNER,source_verified=True,valid_through="2026-11-30",
           hard_load_reviewed=True,tempo_zone_verified=True,
           tempo_z3_lower_watts=235,tempo_z3_upper_watts=257,
           easy_recovery_lower_watts=105,easy_recovery_upper_watts=130)
    d.update(patch)
    return d
def run(goal="POWER_5",workout_id="P5_TEMPO_2X12",ev=None):
    return precompile(SOURCE,goal,workout_id,athlete() if ev is None else ev,OWNER,DAY)

class Inc132TempoBlocks(unittest.TestCase):
    def test_every_existing_tempo_template_preserves_work_rest(self):
        for row in catalog(SOURCE)["rows"]:
            with self.subTest(workout_id=row["workout_id"]):
                x=run(row["goal"],row["workout_id"])
                self.assertEqual(x["status"],"STRUCTURE_SCREENED_ONLY")
                self.assertEqual(x["work_seconds"],row["total_work_seconds"])
                self.assertEqual(len(x["blocks"]),row["reps"]*2-1)
                self.assertFalse(x["can_execute"])
                self.assertFalse(x["can_schedule"])
                self.assertFalse(x["can_sign"])
    def test_no_card_or_issuer_priority_or_fueling(self):
        x=run()
        self.assertIsNone(x["card_id"])
        self.assertIsNone(x["recommended_priority"])
        self.assertIsNone(x["issuer_signature"])
        self.assertIsNone(x["fuel"])
        self.assertFalse(x["ledger_write"])
    def test_personal_tempo_watts_are_stable_only_in_tempo_phases(self):
        x=run()
        for block in x["blocks"]:
            self.assertEqual(block["watts_low"],235 if block["domain"]=="TEMPO_Z3_HARD" else 105)
            self.assertEqual(block["watts_high"],257 if block["domain"]=="TEMPO_Z3_HARD" else 130)
    def test_missing_individual_z3_band_is_blocked_not_ftp_backfill(self):
        x=run(ev=athlete(tempo_z3_lower_watts=None,ftp_watts=300))
        self.assertIn("INDIVIDUAL_Z3_BAND_UNVERIFIED",x["blockers"])
        self.assertEqual(x["blocks"],[])
    def test_unsupported_three_goals_not_issued(self):
        for goal in ("POWER_1","SPRINTER","ENDURANCE_BASE"):
            x=run(goal,"INC132_STUDY_ONLY")
            self.assertIn("GOAL_TEMPO_DOSE_RESEARCH_ONLY",x["blockers"])
            self.assertEqual(x["status"],"BLOCKED")
    def test_cross_goal_template_blocked(self):
        self.assertIn("CANONICAL_TEMPO_TEMPLATE_NOT_FOUND",run("TIME_TRIAL","P5_TEMPO_2X12")["blockers"])
    def test_owner_and_source_blocked(self):
        for ev in (athlete(owner_id="other"),athlete(source_verified=False),
                   athlete(valid_through="2026-01-01")):
            self.assertEqual(run(ev=ev)["status"],"BLOCKED")
    def test_unreviewed_hard_exposure_blocked(self):
        self.assertIn("HARD_EXPOSURE_NOT_REVIEWED",
                      run(ev=athlete(hard_load_reviewed=False))["blockers"])
    def test_injury_hard_override(self):
        for injury in ("NO_TRAINING","NO_INTENSITY"):
            self.assertIn("INJURY_RESTRICTION",run(ev=athlete(injury=injury))["blockers"])
    def test_bad_or_overlapping_recovery_band(self):
        for ev in (athlete(easy_recovery_upper_watts=236),
                   athlete(easy_recovery_lower_watts=None),
                   athlete(easy_recovery_lower_watts=float("nan"))):
            self.assertIn("PERSONAL_RECOVERY_BAND_UNVERIFIED",run(ev=ev)["blockers"])
    def test_mechanics_not_dose_validation(self):
        x=run()
        self.assertEqual(x["scientific_status"],"DOSE_NOT_VALIDATED_FOR_ATHLETE")
    def test_no_training_under_bogus_user_data(self):
        x=run(ev={"owner_id":OWNER})
        self.assertEqual(x["blocks"],[])
        self.assertFalse(x["can_execute"])
if __name__=="__main__":unittest.main()
