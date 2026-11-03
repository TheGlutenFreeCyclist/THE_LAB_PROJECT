"""INC105 regression: no aesthetic PASS without an approved reference."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from run_visual_diff_inc105 import baseline_decision

POLICY = Path(__file__).with_name("editorial_criteria_inc105.json")


class Inc105EditorialGovernance(unittest.TestCase):
    def test_pending_review_is_not_green(self):
        doc = json.loads(POLICY.read_text(encoding="utf-8"))
        self.assertEqual(doc["status"], "DRAFT_AWAITING_OWNER_APPROVAL")
        self.assertEqual(baseline_decision(doc,mode="preview",width=390)["status"],"NOT_VERIFIED")
        self.assertTrue(doc["editorial_criteria"])
        self.assertTrue(doc["typography_criteria"])

    def test_approved_baseline_flags_pixel_drift(self):
        doc = json.loads(POLICY.read_text(encoding="utf-8"))
        good = b"synthetic screenshot only"
        doc.update(status="APPROVED",approval={"owner":"test-reviewer",
                    "approved_at":"2026-11-03"})
        doc["baseline_screenshots"]=[{"mode":"preview","width":390,
                    "playwright_version":"1.56.0",
                    "sha256":hashlib.sha256(good).hexdigest()}]
        self.assertEqual(baseline_decision(doc,mode="preview",width=390,
                                           screenshot_bytes=good)["status"],"PASS")
        self.assertEqual(baseline_decision(doc,mode="preview",width=390,
                                           screenshot_bytes=b"changed")["status"],"FAIL")
        self.assertEqual(baseline_decision(doc,mode="preview",width=320)["status"],"BLOCKED")


if __name__ == "__main__":
    unittest.main()
