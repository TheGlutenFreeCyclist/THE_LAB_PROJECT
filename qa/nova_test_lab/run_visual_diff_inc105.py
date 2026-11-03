"""INC105 owner-approved visual regression gate.

Prior to owner approval: NOT_VERIFIED (never PASS). Approved records include
exact Chromium-version, viewport, mode and SHA-256 of synthetic screenshot.
This deliberately uses an exact-hash gate: the baseline is version-pinned, and
a diff is surfaced for human review instead of inventing visual tolerances.
Private athlete report imagery is NEVER written to public CI.
"""
import argparse
import hashlib
import json
from pathlib import Path


def baseline_decision(policy, *, mode, width, screenshot_bytes=None):
    if policy.get("status") != "APPROVED":
        return {"status":"NOT_VERIFIED","reason":"owner_reference_not_approved"}
    approval = policy.get("approval") or {}
    if not approval.get("owner") or not approval.get("approved_at"):
        return {"status":"BLOCKED","reason":"approval_metadata_incomplete"}
    records = [x for x in policy.get("baseline_screenshots", [])
               if x.get("mode") == mode and x.get("width") == width]
    if len(records) != 1:
        return {"status":"BLOCKED","reason":"unique_reference_missing"}
    record = records[0]
    if record.get("playwright_version") != "1.56.0":
        return {"status":"BLOCKED","reason":"browser_version_mismatch"}
    expected = record.get("sha256") or ""
    if len(expected) != 64 or not all(ch in "0123456789abcdef" for ch in expected):
        return {"status":"BLOCKED","reason":"baseline_hash_invalid"}
    if screenshot_bytes is None:
        return {"status":"NOT_VERIFIED","reason":"no_screenshot_was_rendered"}
    actual = hashlib.sha256(screenshot_bytes).hexdigest()
    return {"status":"PASS" if actual == expected else "FAIL",
            "reason":"visual_exact_match" if actual == expected else "visual_diff_requires_review"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", default=str(Path(__file__).with_name("editorial_criteria_inc105.json")))
    parser.add_argument("--mode", choices=["preview"], default="preview")
    parser.add_argument("--width", type=int, default=390)
    args = parser.parse_args()
    policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))
    gate = baseline_decision(policy, mode=args.mode, width=args.width)
    if gate["status"] != "BLOCKED" and gate["status"] != "NOT_VERIFIED":
        raise AssertionError("unexpected_unrendered_baseline_state")
    if gate["status"] == "NOT_VERIFIED":
        print(json.dumps({"contract":"INC105_VISUAL","status":"NOT_VERIFIED",
                          "reason":"awaiting_approved_baseline"},sort_keys=True))
        return 0
    print(json.dumps({"contract":"INC105_VISUAL",**gate},sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
