"""Scientific scaffolding tests: INC132 TEST branch, no app runtime used."""
import unittest
from datetime import date
from inc132_candidate_gate import GOALS,TEMPO,Z2_STUDY_FORMATS,study

DAY=date(2026,11,6)
OWNER="inc132_synthetic_owner"
def tempo(**patch):
    obj=dict(owner_id=OWNER,source_verified=True,valid_through="2026-11-15",
             ftp_status="VALID",ftp_watts=300,hard_load_reviewed=True)
    obj.update(patch)
    return obj
def aerobic(**patch):
    obj=dict(owner_id=OWNER,source_verified=True,valid_through="2026-11-15",
             z2_lower_watts=145,lt1_ceiling_watts=188,lt1_verified=True)
    obj.update(patch)
    return obj

class INC132ScaffoldTests(unittest.TestCase):
    def test_coverage(self):
        self.assertEqual(set(GOALS),set(TEMPO))
        self.assertEqual(len(set(x[0] for x in TEMPO.values())),7)
    def test_tempo_seven_goal_research_is_never_executable(self):
        for goal in GOALS:
            with self.subTest(goal=goal):
                out=study(goal,"TEMPO_Z3",tempo(),OWNER,DAY)
                self.assertEqual(out["intensity"],"HARD")
                self.assertFalse(out["executable"])
                self.assertFalse(out["scheduled"])
                self.assertIsNone(out["recommended_priority"])
                self.assertIsNone(out["fueling"])
                self.assertFalse(out["ledger_write"])
    def test_three_missing_goals_fail_closed(self):
        for goal in ("POWER_1","SPRINTER","ENDURANCE_BASE"):
            out=study(goal,"TEMPO_Z3",tempo(),OWNER,DAY)
            self.assertIn("UNVALIDATED_GOAL_DOSE",out["blockers"])
            self.assertIsNone(out["potential_power_watts"])
    def test_four_existing_mechanics_are_not_executable(self):
        for goal in ("POWER_5","VO2MAX","POWER_20","TIME_TRIAL"):
            out=study(goal,"TEMPO_Z3",tempo(),OWNER,DAY)
            self.assertTrue(out["study_screened"])
            self.assertEqual(out["potential_power_watts"],(240,264))
            self.assertFalse(out["executable"])
    def test_all_z2_modes_easy_below_personal_lt1(self):
        for goal in GOALS:
            for mode in Z2_STUDY_FORMATS:
                with self.subTest(goal=goal,mode=mode):
                    out=study(goal,"Z2",aerobic(),OWNER,DAY,mode)
                    self.assertEqual(out["intensity"],"EASY")
                    self.assertTrue(out["study_screened"])
                    self.assertEqual(out["potential_power_watts"],(145,187))
                    self.assertLess(out["potential_power_watts"][1],188)
                    self.assertFalse(out["executable"])
    def test_decimal_lt1_upper_is_strictly_below_real_threshold(self):
        ev=aerobic(z2_lower_watts=145.2,lt1_ceiling_watts=188.2)
        out=study("POWER_5","Z2",ev,OWNER,DAY)
        self.assertEqual(out["potential_power_watts"],(146,188))
        self.assertLess(out["potential_power_watts"][1],188.2)
    def test_narrow_lt1_range_not_round_up_to_threshold(self):
        ev=aerobic(z2_lower_watts=187.7,lt1_ceiling_watts=188.0)
        out=study("POWER_5","Z2",ev,OWNER,DAY)
        self.assertIn("LT1_RANGE_NOT_ATTESTED",out["blockers"])
        self.assertIsNone(out["potential_power_watts"])
    def test_missing_lt1_rejects_ftp_substitution(self):
        out=study("POWER_5","Z2",aerobic(lt1_ceiling_watts=None,ftp_watts=300),OWNER,DAY)
        self.assertIn("LT1_RANGE_NOT_ATTESTED",out["blockers"])
        self.assertIsNone(out["potential_power_watts"])
    def test_cross_owner_and_stale_rejected(self):
        for ev in (tempo(owner_id="stranger"),tempo(valid_through="2025-01-01"),
                   tempo(source_verified=False),tempo(ftp_watts=float("nan")),
                   tempo(hard_load_reviewed=False)):
            out=study("POWER_5","TEMPO_Z3",ev,OWNER,DAY)
            self.assertFalse(out["study_screened"])
            self.assertIsNone(out["potential_power_watts"])
    def test_injury_and_health_cannot_improvise_priority(self):
        for kind,ev in (("Z2",aerobic()),("TEMPO_Z3",tempo())):
            for injured in ("NO_TRAINING","NO_INTENSITY"):
                out=study("POWER_20",kind,{**ev,"injury":injured},OWNER,DAY)
                self.assertIn("INJURY_RESTRICTION",out["blockers"])
                self.assertFalse(out["executable"])
            low=study("POWER_20",kind,{**ev,"health_percentile":5},OWNER,DAY)
            high=study("POWER_20",kind,{**ev,"health_percentile":95},OWNER,DAY)
            self.assertEqual(low["blockers"],high["blockers"])
            self.assertIsNone(low["recommended_priority"])
    def test_invalid_inputs_rejected(self):
        for args in (("unknown","Z2","STEADY"),("POWER_5","Z4","STEADY"),("POWER_5","Z2","OVER_UNDER")):
            with self.assertRaises(ValueError):
                study(args[0],args[1],tempo(),OWNER,DAY,args[2])
    def test_no_tempo_confused_with_easy(self):
        self.assertTrue(all("Z3" not in repr(phases) for phases in Z2_STUDY_FORMATS.values()))

if __name__=="__main__": unittest.main()
