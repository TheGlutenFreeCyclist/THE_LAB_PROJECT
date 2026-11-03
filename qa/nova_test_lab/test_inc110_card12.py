"""INC110 R137: read-only chronological issuer gate, synthetic contract tests."""
import copy
import unittest
from unittest.mock import patch
import the_lab_app as nova
from test_real_app import scenario

def sample():
    d,valid,rejected=scenario()
    d["next_sessions"]=[d["next_sessions"][0],rejected,d["next_sessions"][1]]
    return d,valid,rejected

class Inc110ChronologyTests(unittest.TestCase):
    def authorize(self,d,valid=True):
        return (
            patch.object(nova,"_nova_inc051_verified_owner_id",return_value="synthetic-owner"),
            patch.object(nova,"_nova_inc091_eligible",return_value=valid),
        )

    def test_r136_card2_red_r137_card2_suppressed(self):
        d,canonical,rejected=sample()
        before=copy.deepcopy(d)
        a,b=self.authorize(d)
        with a,b:
            rows,audit=nova._nova_inc110_chronological_projection(d)
        self.assertIsNone(rows[1])
        self.assertEqual(rows[0]["intensity"],"EASY")
        self.assertEqual(audit["authority_workout_id"],canonical["nova_workout_id"])
        self.assertEqual(audit["suppressed_chronological_hard"][0]["workout_id"],
                         rejected["nova_workout_id"])
        self.assertEqual(d,before)

    def test_equal_complete_c07_quality_kept(self):
        d,canonical,_=sample()
        d["next_sessions"][1]=copy.deepcopy(canonical)
        a,b=self.authorize(d)
        with a,b:
            rows,audit=nova._nova_inc110_chronological_projection(d)
        self.assertEqual(rows[1]["nova_workout_id"],canonical["nova_workout_id"])
        self.assertEqual(audit["suppressed_chronological_hard"],[])

    def test_same_id_altered_dose_is_not_duplicate(self):
        d,canonical,_=sample()
        wrong=copy.deepcopy(canonical)
        wrong["power_prescription"]["high_watts"]+=25
        d["next_sessions"][1]=wrong
        a,b=self.authorize(d)
        with a,b:
            rows,_=nova._nova_inc110_chronological_projection(d)
        self.assertIsNone(rows[1])

    def test_unverified_owner_plan_fails_closed(self):
        d,canonical,_=sample()
        d["next_sessions"][1]=copy.deepcopy(canonical)
        a,b=self.authorize(d,False)
        with a,b:
            rows,_=nova._nova_inc110_chronological_projection(d)
        self.assertIsNone(rows[1])

    def test_independent_race_not_suppressed(self):
        d,_,_=sample()
        d["next_sessions"][1]["is_race"]=True
        a,b=self.authorize(d)
        with a,b:
            rows,_=nova._nova_inc110_chronological_projection(d)
        self.assertTrue(rows[1]["is_race"])

    def test_main_set_drift_rejected(self):
        d,canonical,_=sample()
        wrong=copy.deepcopy(canonical)
        wrong["main_set"]="Changed without authority"
        d["next_sessions"][1]=wrong
        a,b=self.authorize(d)
        with a,b:
            rows,_=nova._nova_inc110_chronological_projection(d)
        self.assertIsNone(rows[1])

    def test_card12_selector_uses_only_projection(self):
        self.assertEqual(nova.HOME_PAGE.count("data.nova_inc110_chronological_cards[si]"),1)
        self.assertEqual(nova.HOME_PAGE.count("{% set upcoming.rows=upcoming.rows+[(si,data.next_sessions[si])] %}"),0)

if __name__=="__main__":
    unittest.main(verbosity=2)
