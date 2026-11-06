"""Synthetic acceptance tests. Never substitute for issuer/Flask/auth E2E."""
import copy
import unittest
from inc132_render_contract import project

def row(role,wid,plan,domain=None):
    return dict(role=role,goal="POWER_5",workout_id=wid,plan_id=plan,
        owner_id="synthetic-owner",snapshot_id="snapshot-A",as_of="2026-11-06",decision_digest="digest-A",
        compiled=True,issuer_verified=True,dose_attested=True,fueling_attested=True,
        intensity_class="HARD",blocks=[dict(seconds=720,domain=domain or "SPECIFIC")],
        **({"domain":domain} if domain else {}))

def fixture():
    return dict(owner_id="synthetic-owner",snapshot_id="snapshot-A",decision_digest="digest-A",as_of="2026-11-06",producer_version="R146_TEST_MOCK",
        issuer_signature_verified=True,goal="POWER_5",injury=None,day_decision="HOLD",
        card1=dict(role="CARD1",owner_id="synthetic-owner",snapshot_id="snapshot-A",intensity_class="EASY"),
        card2=row("CARD2","P5_TEMPO_2X12","tempo-plan","TEMPO_Z3"),
        card3=row("CARD3","P5_SPECIFIC_4X4","specific-plan"),
        recommended_priority="CARD3",priority_reason_code="WITNESSED_SPECIFIC_FIRST",
        priority_evidence_ids=["synthetic-witness"])

def screen(a=None,owner="synthetic-owner",sid="snapshot-A",digest="digest-A",
           day="2026-11-06",goal="POWER_5",c2_id="P5_TEMPO_2X12",c3_id="P5_SPECIFIC_4X4"):
    if isinstance(a,dict) and a.get("card2") is None: c2_id=None
    return project(a if a is not None else fixture(),owner,sid,digest,
        live_as_of=day,live_goal=goal,live_card2_workout_id=c2_id,
        live_card3_workout_id=c3_id)

class Inc132RenderBoundary(unittest.TestCase):
    def test_current_snapshot_one_priority(self):
        self.assertTrue(screen()["valid"])
        self.assertEqual(screen()["highlight"],"CARD3")
        self.assertFalse(screen()["can_execute"])
    def test_alternate_priority_keeps_both_offers(self):
        a=fixture();a["recommended_priority"]="CARD2"
        result=screen(a)
        self.assertTrue(result["valid"]);self.assertEqual(result["highlight"],"CARD2")
        self.assertIsNotNone(result["card3"])
    def test_historical_has_no_border(self):
        result=screen(sid="old")
        self.assertTrue(result["valid"]);self.assertIsNone(result["highlight"])
    def test_different_digest_has_no_border(self):
        self.assertIsNone(screen(digest="wrong")["highlight"])
    def test_foreign_owner_blocked(self):
        r=screen(owner="someone-else")
        self.assertIn("OWNER_SCOPE_FAIL",r["errors"]);self.assertIsNone(r["card3"])
    def test_incomplete_specific_blocked(self):
        a=fixture();a["card3"]=None
        self.assertIn("CARD3_MISSING",screen(a)["errors"])
    def test_unverified_issuer_blocked(self):
        a=fixture();a["issuer_signature_verified"]=False
        self.assertIn("ISSUER_MISSING",screen(a)["errors"])
    def test_unvalidated_goal_dose_blocked(self):
        a=fixture();a["goal"]="SPRINTER";a["card2"]["goal"]="SPRINTER";a["card3"]["goal"]="SPRINTER"
        self.assertIn("CARD2_DOSE_UNVALIDATED",screen(a)["errors"])
    def test_cross_goal_template_blocked(self):
        a=fixture();a["goal"]="VO2MAX";a["card2"]["goal"]="VO2MAX";a["card3"]["goal"]="VO2MAX"
        self.assertIn("CARD2_DOSE_UNVALIDATED",screen(a)["errors"])
    def test_no_inferred_scheduling(self):
        a=fixture();a["recommended_priority"]="CARD2"
        self.assertFalse(screen(a)["can_schedule"])
    def test_card2_missing_explicit_reason_uses_card3(self):
        a=fixture();a["card2"]=None;a["card2_blocked_reason"]="GOAL_DOSE_UNVALIDATED"
        r=screen(a);self.assertTrue(r["valid"]);self.assertEqual(r["highlight"],"CARD3")
    def test_not_silent_when_card2_missing(self):
        a=fixture();a["card2"]=None
        self.assertIn("C2_REASON_MISSING",screen(a)["errors"])
    def test_duplicate_offer_plan_blocked(self):
        a=fixture();a["card2"]["plan_id"]="specific-plan"
        self.assertIn("DUPLICATE_ID",screen(a)["errors"])
    def test_foreign_card_owner_blocked(self):
        a=fixture();a["card2"]["owner_id"]="foreign"
        self.assertIn("CARD2_IDENTITY_MISMATCH",screen(a)["errors"])
    def test_unverified_fueling_blocked(self):
        a=fixture();a["card2"]["fueling_attested"]=False
        self.assertIn("CARD2_BAD",screen(a)["errors"])
    def test_z4_not_tempo(self):
        a=fixture();a["card2"]["domain"]="Z4"
        self.assertIn("CARD2_BAD",screen(a)["errors"])
    def test_tempo_injury_blocked(self):
        a=fixture();a["injury"]="NO_INTENSITY"
        self.assertIn("INJURY_HARD_BLOCK",screen(a)["errors"])
    def test_no_veto_from_health_marker(self):
        a=fixture();a["health_percentile"]=1
        b=copy.deepcopy(a);b["health_percentile"]=99
        self.assertEqual(screen(a)["highlight"],screen(b)["highlight"])
    def test_invalid_seconds_fail_without_exceptions(self):
        for bad in ("720",None,float("nan"),-3,False):
            a=fixture();a["card3"]["blocks"][0]["seconds"]=bad
            self.assertIn("CARD3_MISSING",screen(a)["errors"])

    def test_report_day_changed_no_active_highlight(self):
        result=screen(day="2026-11-07")
        self.assertTrue(result["valid"]);self.assertIsNone(result["highlight"])
    def test_goal_changed_no_sticky_border(self):
        self.assertIsNone(screen(goal="VO2MAX")["highlight"])
    def test_live_c2_id_changed_no_sticky_border(self):
        self.assertIsNone(screen(c2_id="P5_TEMPO_2X15")["highlight"])
    def test_live_c3_id_changed_no_sticky_border(self):
        self.assertIsNone(screen(c3_id="different")["highlight"])
    def test_missing_trusted_live_context_never_highlights(self):
        a=fixture()
        self.assertIsNone(project(a,"synthetic-owner","snapshot-A","digest-A")["highlight"])
    def test_missing_report_day_fails(self):
        a=fixture();a["as_of"]=None
        self.assertIn("DATE_MISSING_OR_INVALID",screen(a)["errors"])
    def test_malformed_calendar_day_fails(self):
        a=fixture();a["as_of"]="2026-02-29"
        self.assertIn("DATE_MISSING_OR_INVALID",screen(a)["errors"])
    def test_missing_producer_version_fails(self):
        a=fixture();a.pop("producer_version")
        self.assertIn("PRODUCER_VERSION_MISSING",screen(a)["errors"])
    def test_offer_attestation_digest_must_match(self):
        a=fixture();a["card2"]["decision_digest"]="different"
        self.assertIn("CARD2_ATTESTATION_MISMATCH",screen(a)["errors"])
    def test_specific_offer_as_of_must_match(self):
        a=fixture();a["card3"]["as_of"]="2026-11-05"
        self.assertIn("CARD3_ATTESTATION_MISMATCH",screen(a)["errors"])
    def test_malformed_payload_is_not_exception(self):
        self.assertIn("PAYLOAD_INVALID",screen(False)["errors"])
    def test_blank_phase_domain_fails(self):
        a=fixture();a["card2"]["blocks"][0]["domain"]="  "
        self.assertIn("CARD2_BAD",screen(a)["errors"])
    def test_priority_witness_must_be_a_list(self):
        a=fixture();a["priority_evidence_ids"]="unverified"
        self.assertIn("WITNESS_MISSING",screen(a)["errors"])
    def test_card3_easy_is_not_a_specific_quality(self):
        a=fixture();a["card3"]["intensity_class"]="EASY"
        self.assertIn("CARD3_MISSING",screen(a)["errors"])

if __name__ == "__main__":unittest.main()
