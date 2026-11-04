"""INC120 positive placement gates: a next quality, or a valid Card-1/2 owner."""
import copy
import unittest
from unittest.mock import patch
import the_lab_app as nova

SCHEMA = "NOVA-R196.9.140-CARD3-QUALITY-PLACEMENT-1"
WID = "P5_5X3_EASYREC"

def context():
    return {"nova_decision": {"goal_key": "POWER_5", "dimension": "DURABILITY", "action": "TRAIN"},
        "adaptive_roadmap": {"goal_key": "POWER_5",
                             "scientific_progression": {"dimension": "DURABILITY"}},
        "nova_prescription": {"status": "EASY_ONLY", "workout_id": None},
        "next_sessions": [{"intensity": "EASY", "date": "2026-11-03", "title": "Easy"},
                          {"intensity": "EASY", "date": "2026-11-04", "title": "Easy"}],
        "nova_inc110_chronological_cards": [
            {"intensity": "EASY"}, {"intensity": "EASY"}],
        "nova_card3_workout_view": {"state": "NOT_PRESCRIBED",
            "title": "Development goal", "goal_key": "POWER_5",
            "verified_offer": False, "verified_future_plan": False,
            "offer_structure_only": False, "planned_quality": False}}

class Inc120PlacementTests(unittest.TestCase):
    def test_original_canonical_selector_produces_deferred_identity_only(self):
        template = nova._R19696_LIBRARY_INDEX[WID]
        with patch.object(nova, "_v19699_select_workout_template",
                          return_value=(template, {"reason": "CANONICAL_SELECTOR"})):
            p = nova._nova_inc120_intent(
                {"goal_key": "POWER_5", "dimension": "DURABILITY"},
                {"scientific_progression": {"dimension": "DURABILITY"}}, {})
        self.assertEqual(p["workout_id"], WID)
        self.assertEqual(p["status"], "DEFERRED_NOT_CLEARED")
        self.assertFalse(p["execution_authorized"])
        self.assertIsNone(p["personalized_watts"])
        self.assertIsNone(p["fueling"])
        self.assertFalse(p["adds_calendar_event"])

    def test_rejected_original_science_cannot_be_planned_as_quality(self):
        with patch.object(nova, "_v19699_select_workout_template",
                          return_value=(nova._R19696_LIBRARY_INDEX[WID], {})):
            plan = nova._nova_inc120_intent(
                {"goal_key":"POWER_5","dimension":"DURABILITY"},
                {"scientific_progression":{"dimension":"DURABILITY"}},
                rejected=[{"workout_id":WID}])
        self.assertIsNone(plan)

    def test_replay_producer_still_withholds_hard_but_keeps_plan(self):
        fake = {"status": "EASY_ONLY", "workout_id": None, "raw_sessions": []}
        with patch.object(nova, "_INC120_BEFORE_PRODUCER", return_value=fake), \
             patch.object(nova, "_nova_inc120_intent",
                          return_value={"schema":SCHEMA,"workout_id":WID}):
            produced = nova.build_nova_prescription(
                {"goal_key":"POWER_5"}, {}, adaptive_roadmap={})
        self.assertEqual(produced["status"], "EASY_ONLY")
        self.assertIsNone(produced["workout_id"])
        self.assertEqual(produced["inc120_planned_quality"]["workout_id"], WID)

    def test_card3_gets_actual_structure_when_card12_are_easy(self):
        d=context()
        plan = {"schema":SCHEMA,"workout_id":WID,"title":"5-min power · 5×3 min",
            "structure":"5 × 3 min work; easy recovery", "purpose":"Five-minute power",
            "execution":"Repeat evenly", "reason":"Not cleared to execute."}
        with patch.object(nova, "_INC120_BEFORE_UI", return_value=copy.deepcopy(d)), \
             patch.object(nova, "_nova_inc120_intent", return_value=plan), \
             patch.object(nova, "_INC120_BEFORE_DUPLICATE", return_value=None):
            out = nova._v4891_prepare_snapshot_for_ui(d)
        card = out["nova_card3_workout_view"]
        self.assertEqual(card["workout_id"], WID)
        self.assertTrue(card["planned_quality"])
        self.assertEqual(out["inc120_quality_placement"], "CARD3_PLANNED_UNCLEARED")
        self.assertFalse(card["execution_authorized_by_preview"])
        self.assertIsNone(card["personalized_watts"])
        self.assertIsNone(out["quality_direction_fuel"])
        self.assertFalse(out["next_quality_direction"]["is_a_prescription"])

    def test_verified_quality_in_card1_greys_card3(self):
        d=context()
        row={"intensity":"HARD", "source":"CALENDAR", "date":"2026-11-05",
             "title":"Upcoming real quality", "is_planned_training":True}
        d["nova_inc110_chronological_cards"][0]=row
        d["next_sessions"][0]=row
        with patch.object(nova, "_INC120_BEFORE_UI", return_value=copy.deepcopy(d)), \
             patch.object(nova, "_INC120_BEFORE_DUPLICATE", return_value=None):
            out=nova._v4891_prepare_snapshot_for_ui(d)
        self.assertEqual(out["inc120_quality_duplicate_card"], 1)
        self.assertEqual(out["inc120_quality_placement"], "CARD12_OWNS_QUALITY_CARD3_GREY")

    def test_unissued_rejected_hard_does_not_grey_card3(self):
        d=context()
        row={"intensity":"HARD", "source":"RHYTHM", "date":"2026-11-05",
             "title":"Unissued", "nova_workout_id":"P5X_2X420_R300",
             "nova_prescription_authority":True}
        d["next_sessions"][1]=row
        d["nova_inc110_chronological_cards"][1]=None
        with patch.object(nova, "_INC120_BEFORE_DUPLICATE", return_value=None):
            self.assertIsNone(nova._nova_inc120_duplicate_index(d))

    def test_already_verified_card3_never_replaced(self):
        d=context()
        d["nova_card3_workout_view"].update(
            verified_offer=True, workout_id=WID, title="Original verified quality")
        with patch.object(nova, "_INC120_BEFORE_UI", return_value=copy.deepcopy(d)), \
             patch.object(nova, "_INC120_BEFORE_DUPLICATE", return_value=None):
            out=nova._v4891_prepare_snapshot_for_ui(d)
        self.assertEqual(out["nova_card3_workout_view"]["workout_id"], WID)
        self.assertEqual(out["inc120_quality_placement"], "EXISTING_VERIFIED_CARD3_QUALITY")
        
    def test_html_uses_real_planned_quality_branch(self):
        self.assertEqual(nova.HOME_PAGE.count("r1969104-planned-structure"), 1)
        self.assertIn("NEXT QUALITY · PROPOSED STRUCTURE · NOT CLEARED", nova.HOME_PAGE)

if __name__ == "__main__":
    unittest.main(verbosity=2)
