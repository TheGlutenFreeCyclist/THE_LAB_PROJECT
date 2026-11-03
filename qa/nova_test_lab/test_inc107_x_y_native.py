"""INC107 real native R154 X/Y decision vs separately authored synthetic oracle.

Explicit quality intent is a training preference, NOT permission to auto-book
a conditional Card 3 future plan. Personal availability has NOT been approved.
"""
import copy
import os
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

for k in ("DATABASE_URL","THE_LAB_OWNER_DATABASE_URL","ICU_API_KEY",
          "ICU_ATHLETE_ID","GARMIN_EMAIL","GARMIN_PASSWORD",
          "ANTHROPIC_API_KEY","THE_LAB_STANDARD_AI_API_KEY",
          "THE_LAB_PLATFORM_AI_API_KEY"):
    os.environ[k]=""
import the_lab_app as nova

ROME=ZoneInfo("Europe/Rome")
X="2026-11-04"
Y="2026-11-05"


def fixture(preferred=X, blocked_x=False, earliest="2026-11-04T07:00:00+01:00"):
    clock={
        "iso":"2026-11-03",
        "next_slots":[
            {"date":X,"start_minute":1110,"source":"RHYTHM",
             "restriction":"NO_INTENSITY" if blocked_x else "NONE",
             "is_race":False,"label":"X evening (synthetic)"},
            {"date":Y,"start_minute":1110,"source":"RHYTHM",
             "restriction":"NONE","is_race":False,"label":"Y evening (synthetic)"},
        ],
        "future_note_intent":{
            "active":True,"quality_preferred":True,"date":preferred,
            "preferred_dayparts":["ALL_DAY"],"session_profile":"QUALITY",
            "hard_blocked":False,"conditional":False
        }
    }
    road={"quality_window":{"state":"OPEN","earliest_iso":earliest,
           "preferred_iso":"2026-11-05T18:30:00+01:00"}}
    dec={"hard_session_allowed":True}
    return clock,road,dec


class Inc107ActualNativeDateDecision(unittest.TestCase):
    def decision(self, **overrides):
        clock,road,dec=fixture(**overrides)
        before=(copy.deepcopy(clock),copy.deepcopy(road),copy.deepcopy(dec))
        actual=nova._v154_explicit_quality_target(clock,road,dec)
        self.assertEqual((clock,road,dec),before,
                         "Read-only target resolver altered prescription/clock")
        return actual

    def test_explicit_x_beats_learned_y(self):
        target=self.decision(preferred=X)
        self.assertIsNotNone(target)
        self.assertTrue(target["target_iso"].startswith(X))
        self.assertEqual(target["index"],0)

    def test_explicit_y_when_x_unavailable(self):
        target=self.decision(preferred=Y,blocked_x=True)
        self.assertIsNotNone(target)
        self.assertTrue(target["target_iso"].startswith(Y))
        self.assertEqual(target["index"],1)

    def test_blocked_x_never_relabelled_eligible(self):
        self.assertIsNone(self.decision(preferred=X,blocked_x=True))

    def test_x_before_recovery_window_rejected(self):
        self.assertIsNone(self.decision(
            preferred=X,earliest="2026-11-05T08:00:00+01:00"))

    def test_preference_cannot_override_hard_science_veto(self):
        clock,road,dec=fixture(preferred=X)
        dec["hard_session_allowed"]=False
        self.assertIsNone(nova._v154_explicit_quality_target(clock,road,dec))

    def test_conditional_future_plan_is_not_a_booking(self):
        clock,road,dec=fixture()
        clock["future_note_intent"]["conditional"]=True
        self.assertIsNone(nova._v154_explicit_quality_target(clock,road,dec))
        self.assertNotIn("calendar_event",clock)


if __name__ == "__main__":
    unittest.main(verbosity=2)
