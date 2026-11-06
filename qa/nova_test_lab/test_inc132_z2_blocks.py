"""INC132 Card1 Z2 block research gates. Never authorizes execution."""
import unittest
from datetime import date
from inc132_z2_blocks import compile_study_z2

OWNER="only-synthetic-owner"
DAY=date(2026,11,6)
def athlete(**edits):
    x=dict(owner_id=OWNER,source_verified=True,valid_through="2026-11-30",
           z2_lower_watts=145,lt1_ceiling_watts=188,lt1_verified=True,
           recovery_lower_watts=90,recovery_upper_watts=115,
           habitual_cadence_rpm=85,cadence_source_verified=True)
    x.update(edits)
    return x
def get(mode,ev=None,goal="POWER_5"):
    return compile_study_z2(goal,ev or athlete(),OWNER,DAY,mode)

class Inc132Z2Blocks(unittest.TestCase):
    def test_four_varieties_generate_real_phase_arrays(self):
        for mode in ("STEADY","INTERVAL","PROGRESSIVE","CADENCE_VARIATION"):
            with self.subTest(mode=mode):
                x=get(mode)
                self.assertEqual(x["status"],"STRUCTURE_SCREENED_ONLY")
                self.assertTrue(x["blocks"])
                self.assertFalse(x["can_execute"])
                self.assertFalse(x["can_schedule"])
                self.assertIsNone(x["canonical_workout_id"])
                self.assertIsNone(x["fueling"])
    def test_every_z2_phase_below_measured_lt1(self):
        for mode in ("STEADY","INTERVAL","PROGRESSIVE","CADENCE_VARIATION"):
            for b in get(mode)["blocks"]:
                self.assertLess(b["watts_high"],188)
                self.assertGreaterEqual(b["watts_low"],40)
                self.assertLessEqual(b["watts_low"],b["watts_high"])
                self.assertEqual(b["domain"],"EASY_BELOW_LT1")
    def test_interval_needs_individual_recovery_watts(self):
        x=get("INTERVAL",athlete(recovery_lower_watts=None))
        self.assertEqual(x["status"],"BLOCKED")
        self.assertIn("BELOW_Z2_RECOVERY_NOT_ATTESTED",x["blockers"])
    def test_intervals_require_recovery_below_z2(self):
        for ev in (athlete(recovery_upper_watts=145),
                   athlete(recovery_lower_watts=147,recovery_upper_watts=148),
                   athlete(recovery_lower_watts=float("nan"))):
            x=get("INTERVAL",ev)
            self.assertEqual(x["status"],"BLOCKED")
    def test_progressive_has_increasing_nonoverlapping_bands(self):
        rows=get("PROGRESSIVE")["blocks"]
        self.assertEqual(len(rows),3)
        self.assertLess(rows[0]["watts_high"],rows[1]["watts_low"])
        self.assertLess(rows[1]["watts_high"],rows[2]["watts_low"])
    def test_narrow_zone_blocked_for_progressive_only(self):
        ev=athlete(z2_lower_watts=181.1,lt1_ceiling_watts=184)
        self.assertEqual(get("PROGRESSIVE",ev)["status"],"BLOCKED")
    def test_cadence_cues_around_habitual_not_forced_torque(self):
        x=get("CADENCE_VARIATION")
        self.assertEqual([b["cadence_cue_rpm"] for b in x["blocks"]],[85,90,85,80,85])
        self.assertTrue(all(65<=b["cadence_cue_rpm"]<=110 for b in x["blocks"]))
        self.assertIn("no low-cadence strength claim",x["cadence_note"])
    def test_cadence_unverified_fails_closed(self):
        for ev in (athlete(cadence_source_verified=False),athlete(habitual_cadence_rpm=40)):
            self.assertIn("HABITUAL_CADENCE_NOT_ATTESTED",
                          get("CADENCE_VARIATION",ev)["blockers"])
    def test_owner_stale_lt1_injury_blocked(self):
        for ev in (athlete(owner_id="foreign"),athlete(valid_through="2023-01-01"),
                   athlete(lt1_verified=False),athlete(injury="NO_INTENSITY")):
            self.assertEqual(get("STEADY",ev)["status"],"BLOCKED")
    def test_all_seven_goals_screened_only_not_prescribed(self):
        for goal in ("POWER_5","VO2MAX","POWER_1","SPRINTER","POWER_20","TIME_TRIAL","ENDURANCE_BASE"):
            x=get("STEADY",goal=goal)
            self.assertFalse(x["can_execute"])
            self.assertEqual(x["goal"],goal)
    def test_invalid_mode_is_error_not_fallback(self):
        with self.assertRaises(ValueError):get("Z4_TEMPO")
    def test_no_unwitnessed_priorities(self):
        self.assertIsNone(get("STEADY")["recommended_priority"])

if __name__=="__main__":unittest.main()
