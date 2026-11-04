"""NOVA Test Lab: real R136 import, Flask HTTP and INC101 regression tests.

Pure synthetic data only. No athlete credentials, API calls, Neon or snapshots.
These tests are NOT a complete authenticated E2E or producer/issuer certification.
"""
import copy
import os
import unittest
from unittest.mock import patch

# Set this BEFORE importing the real application. Never inherit production DB URLs.
os.environ["DATABASE_URL"] = ""
os.environ["THE_LAB_OWNER_DATABASE_URL"] = ""
os.environ["PRODUCT_SECURITY_STRICT"] = "0"
os.environ["SESSION_COOKIE_SECURE"] = "0"
os.environ["ICU_API_KEY"] = ""
os.environ["GARMIN_EMAIL"] = ""
os.environ["GARMIN_PASSWORD"] = ""
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["THE_LAB_STANDARD_AI_API_KEY"] = ""
os.environ["THE_LAB_PLATFORM_AI_API_KEY"] = ""

import the_lab_app as nova  # noqa: E402 - import the ACTUAL deployed Python module


def scenario(issued=False):
    canonical = {
        "title": "5-min power · 5×3 min",
        "nova_workout_id": "P5_5X3_EASYREC",
        "nova_template_signature": "5x180r240",
        "intensity": "HARD",
        "session_kind": "VO2",
        "duration_min": 60,
        "date": None,
        "session_composition": {"total_seconds": 3600},
        "power_prescription": {"low_watts": 350, "high_watts": 370, "source": "DIRECT"},
    }
    rejected = {
        "title": "5-min power · 2×7 min",
        "nova_workout_id": "P5X_2X420_R300",
        "nova_template_signature": "2x420r300",
        "nova_prescription_authority": True,
        "intensity": "HARD",
        "session_kind": "VO2",
        "duration_min": 60,
        "date": "2026-11-04",
        "session_composition": {"total_seconds": 3600},
        "power_prescription": {"low_watts": 310, "high_watts": 340, "source": "TRANSFER"},
    }
    easy = [
        {"title": "Easy absorption", "intensity": "EASY", "session_kind": "RECOVERY", "duration_min": 45, "date": "2026-11-03"},
        {"title": "Easy endurance", "intensity": "EASY", "session_kind": "ENDURANCE", "duration_min": 60, "date": "2026-11-04"},
    ]
    # Real canonical nutrition calculations, not a stub.
    nutrition = nova.build_nutrition_plan(easy + [rejected], {"glycogen_pressure": "MODERATE"})
    data = {
        "next_sessions": easy + [rejected], "nutrition_plan": nutrition,
        "metabolic_context": {"glycogen_pressure": "MODERATE"},
        "future_quality_plan": {
            "workout": canonical, "workout_id": canonical["nova_workout_id"],
            "status": "COMPILED_UNSCHEDULED", "owner_scope": "synthetic-owner",
            "fueling": {"workout_id": canonical["nova_workout_id"], "display": "40 g/h"},
        },
        "next_quality_offer": None,
        "quality_offer_integrity": {"state": "FAIL"},
        "nova_card3_workout_view": {
            "workout_id": canonical["nova_workout_id"],
            "verified_future_plan": True, "verified_offer": False,
        },
    }
    if issued:
        data["next_quality_offer"] = {"workout_id": canonical["nova_workout_id"], "workout": canonical}
        data["quality_offer_integrity"] = {"state": "PASS"}
        data["nova_card3_workout_view"].update(verified_future_plan=False, verified_offer=True)
    return data, canonical, rejected


class RealFlaskAndScienceTests(unittest.TestCase):
    def test_exact_release_and_real_module_loaded(self):
        self.assertIn("R196.9.141", nova.APP_VERSION)
        self.assertTrue(callable(nova._v115_replay_nova_core))
        self.assertEqual(nova.R115_REPLAY_SCHEMA, "V4.8.91-R115-NOVA-REPLAY-1")
        self.assertTrue(callable(nova.build_nutrition_plan))

    def test_healthz_http_without_database(self):
        response = nova.app.test_client().get("/healthz")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.headers.get("X-Robots-Tag"), "noindex, nofollow")

    def test_anonymous_replay_http_denied_without_database(self):
        # A restricted QA route must not run on an unauthenticated request.
        with patch.object(nova, "require_login", return_value=False):
            with patch.object(nova, "load_latest_report", side_effect=AssertionError("DB read forbidden")):
                response = nova.app.test_client().post("/qa/nova-replay")
        self.assertIn(response.status_code, (302, 303, 401, 403))

    def test_canonical_recovery_real_fueling_and_html(self):
        data, canonical, rejected = scenario()
        before = copy.deepcopy(data)
        with patch.object(nova, "_nova_inc051_verified_owner_id", return_value="synthetic-owner"), \
             patch.object(nova, "_nova_inc091_eligible", return_value=True):
            rows, audit = nova._nova_inc101_recovery_projection(data)
        self.assertEqual(data, before, "Projection mutated persisted snapshot data")
        self.assertEqual(len(rows), 3)
        self.assertEqual(audit["canonical_workout_id"], canonical["nova_workout_id"])
        self.assertEqual(audit["suppressed_unissued_workout_ids"], [rejected["nova_workout_id"]])
        self.assertEqual(rows[-1]["workout_id"], canonical["nova_workout_id"])
        self.assertEqual(rows[-1]["source"], "SEALED_FUTURE_UNSCHEDULED")
        self.assertTrue(rows[-1]["conditional"])
        self.assertIsNone(rows[-1]["session"]["date"])
        self.assertTrue(rows[-1]["nutrition"]["post_cho"])
        self.assertIn("IF this exact quality is completed", rows[-1]["nutrition"]["guidance"])
        template = nova.HOME_PAGE[
            nova.HOME_PAGE.index('<div class="v23-recovery-grid">'):
            nova.HOME_PAGE.index('<div class="v8-science v23-science">')
        ]
        html = nova.app.jinja_env.from_string(template).render(data={"nova_recovery_display_rows": rows})
        self.assertIn('data-nova-workout-id="P5_5X3_EASYREC"', html)
        self.assertIn("5×3 min", html)
        self.assertNotIn("2×7 min", html)
        self.assertIn("UNSCHEDULED QUALITY", html)

    def test_unverified_future_fails_closed(self):
        data, canonical, rejected = scenario()
        with patch.object(nova, "_nova_inc051_verified_owner_id", return_value="synthetic-owner"), \
             patch.object(nova, "_nova_inc091_eligible", return_value=False):
            rows, audit = nova._nova_inc101_recovery_projection(data)
        self.assertEqual(len(rows), 2)
        self.assertEqual(audit["issuer_authority"], "NO_VERIFIED_QUALITY")
        self.assertNotIn(canonical["nova_workout_id"], [r["workout_id"] for r in rows])
        self.assertIn(rejected["nova_workout_id"], audit["suppressed_unissued_workout_ids"])

    def test_same_id_wrong_watts_never_equivalent(self):
        data, canonical, rejected = scenario()
        drifted = copy.deepcopy(canonical)
        drifted["power_prescription"]["high_watts"] += 15
        self.assertFalse(nova._nova_inc101_same_compiled_dose(drifted, canonical))
        self.assertTrue(nova._nova_inc101_same_compiled_dose(canonical, canonical))

    def test_issued_quality_not_duplicated(self):
        data, canonical, rejected = scenario(issued=True)
        data["next_sessions"][-1] = copy.deepcopy(canonical)
        data["nutrition_plan"][-1] = nova.build_nutrition_plan([canonical], {"glycogen_pressure": "MODERATE"})[0]
        with patch.object(nova, "_nova_inc051_verified_owner_id", return_value="synthetic-owner"), \
             patch.object(nova, "_nova_inc076_seal_ok", return_value=True):
            rows, audit = nova._nova_inc101_recovery_projection(data)
        self.assertEqual(len(rows), 3)
        self.assertEqual(sum(x["workout_id"] == canonical["nova_workout_id"] for x in rows), 1)
        self.assertFalse(rows[-1]["conditional"])
        self.assertFalse(audit["changed_persisted_prescription"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
