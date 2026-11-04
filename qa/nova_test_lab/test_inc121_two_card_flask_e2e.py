"""INC121: black-box synthetic Card 3 placement through real Flask/Jinja.
No real athlete data, secrets, DB reads, issuer bypass, or mock final HTML.
Two user acceptance scenarios: (A) quality in Card 3, (B) quality already in
Card 1/2 -> Card 3 neutral/grey. The real INC120 presentation code runs.
"""
import copy
import os
import re
import unittest
from unittest.mock import patch

for name in ("DATABASE_URL", "THE_LAB_OWNER_DATABASE_URL", "ICU_API_KEY",
             "ICU_ATHLETE_ID", "GARMIN_EMAIL", "GARMIN_PASSWORD",
             "ANTHROPIC_API_KEY", "THE_LAB_STANDARD_AI_API_KEY",
             "THE_LAB_PLATFORM_AI_API_KEY"):
    os.environ[name] = ""
os.environ["PRODUCT_SECURITY_STRICT"] = "0"
os.environ["SESSION_COOKIE_SECURE"] = "0"
os.environ["THE_LAB_TEST_LAB_MODE"] = "1"
import the_lab_app as nova

R140 = nova._v4891_prepare_snapshot_for_ui
GOAL = "POWER_5"
DIM = "DURABILITY"
BAD_ID = "P5X_2X420_R300"
COL3 = re.compile(r'<article class="v4-card v4-session[^"]*v23-col-3[^"]*"[^>]*>(.*?)</article>', re.S)

def easy(title, day):
    return dict(title=title, date=day, slot="Synthetic slot",
        intensity="EASY", intensity_class="recovery",
        session_kind="RECOVERY", duration="45 min", duration_min=45,
        main_set="Synthetic easy aerobic work only.", why="Recovery.",
        environment="INDOOR", source="CALENDAR", is_planned_training=False,
        hard_spacing_relevant=False, provisional_quality=False,
        quality_relevance="NONE", restriction="NONE", nova_workout_id=None)

def synthesize(input_data, position=None):
    # Let the true previous adapters process the actual Flask preview data,
    # then substitute two synthetic chronological sessions + new R140 inputs.
    pre = R140(input_data)
    d = dict(pre)
    first = easy("Synthetic easy one", "2026-11-05")
    second = easy("Synthetic easy two", "2026-11-06")
    chronological = [first, second]
    if position is not None:
        chronological[position] = dict(chronological[position],
            title="Synthetic VALID calendar quality in card "+str(position+1),
            source="CALENDAR", date="2026-11-06",
            intensity="HARD", intensity_class="vo2",
            session_kind="VO2", quality_relevance="MEANINGFUL",
            hard_spacing_relevant=True, is_planned_training=True,
            nova_workout_id=None, main_set="Validated calendar quality (synthetic).",
            why="Genuine explicitly scheduled athlete quality.")
    d.update(nova_decision=dict(goal_key=GOAL, dimension=DIM, action="TRAIN"),
             adaptive_roadmap=dict(goal_key=GOAL,scientific_progression=dict(dimension=DIM)),
             evidence_ledger={}, training_definitions={},
             next_sessions=chronological,
             nova_inc110_chronological_cards=copy.deepcopy(chronological),
             nova_inc110_chronological_audit=dict(retained_identical_hard_workout_ids=[]),
             nutrition_plan=nova.build_nutrition_plan(chronological, {}),
             nova_prescription=dict(status="EASY_ONLY",workout_id=None),
             nova_card3_workout_view=dict(state="NOT_PRESCRIBED",
                goal_key=GOAL,dimension=DIM,title="Development goal",
                verified_offer=False,verified_future_plan=False,
                offer_structure_only=False, planned_quality=False),
             future_quality_plan=None,next_quality_offer=None,
             quality_offer_integrity=dict(state="FAIL"),
             quality_direction_fuel=None)
    # Invoke the ACTUAL R140 placement code over explicit synthetic inputs;
    # do not replace it with a faked final Card-3 view.
    with patch.object(nova, "_INC120_BEFORE_UI", return_value=d):
        out = R140(input_data)
    return out

class Inc121FlaskCardAcceptance(unittest.TestCase):
    def render(self, position):
        original=R140
        verdicts=[]
        def project(input_data):
            out=synthesize(input_data,position=position)
            verdicts.append(dict(
                placement=out.get("inc120_quality_placement"),
                duplicate=out.get("inc120_quality_duplicate_card"),
                quality=(out.get("nova_card3_workout_view") or {}).get("workout_id"),
                planned=(out.get("nova_card3_workout_view") or {}).get("planned_quality"),
                structure=(out.get("nova_card3_workout_view") or {}).get("structure")))
            return out
        with patch.object(nova,"_v4891_prepare_snapshot_for_ui",side_effect=project):
            response=nova.app.test_client().get("/preview")
        self.assertEqual(response.status_code,200)
        self.assertTrue(verdicts)
        return response.get_data(as_text=True),verdicts[-1]

    def test_A_no_hard_in_first_two_quality_visible_in_card3(self):
        html, meta=self.render(None)
        card3=COL3.findall(html)
        self.assertEqual(len(card3),1,"Card3 HTML card must exist")
        self.assertTrue(meta["planned"],"Card3 must contain concrete quality")
        self.assertTrue(meta["quality"],"Canonical quality ID is required")
        self.assertTrue(meta["structure"],"Canonical workout structure required")
        self.assertIn("CARD3_PLANNED_UNCLEARED",str(meta["placement"]))
        self.assertIn("FUTURE WORKOUT STRUCTURE",card3[0])
        self.assertIn("NOT CLEARED",card3[0])
        self.assertIn(meta["structure"],card3[0])
        self.assertNotIn(BAD_ID,card3[0])
        self.assertNotIn("Verified personal power:",card3[0])

    def test_B_quality_already_in_card1_or_2_card3_grey_and_not_duplicate(self):
        for location in (0,1):
            with self.subTest(card=location+1):
                html,meta=self.render(location)
                self.assertEqual(meta["duplicate"],location+1)
                self.assertEqual(meta["placement"],"CARD12_OWNS_QUALITY_CARD3_GREY")
                self.assertIn("Synthetic VALID calendar quality in card "+str(location+1),html)
                self.assertEqual(len(COL3.findall(html)),1,
                    "Card3 grey placeholder should be visible, not silently absent")
                card3=COL3.findall(html)[0]
                self.assertIn("ALREADY IN YOUR PLAN",card3)
                self.assertNotIn("FUTURE WORKOUT STRUCTURE",card3)
                self.assertNotIn(BAD_ID,card3)

if __name__=="__main__":
    unittest.main(verbosity=2)
