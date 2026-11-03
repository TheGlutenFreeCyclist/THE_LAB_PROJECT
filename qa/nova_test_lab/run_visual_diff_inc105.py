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


def capture_synthetic_preview(width):
    """Real R136 Flask HTML -> isolated Chromium screenshot; synthetic only."""
    from run_ui_browser import render_real_flask, SAFE_BROWSER_ORIGIN
    from playwright.sync_api import sync_playwright
    html, _ = render_real_flask("preview", None)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            context = browser.new_context(
                viewport={"width":width,"height":850},device_scale_factor=1,
                is_mobile=width<=390,has_touch=width<=390,reduced_motion="reduce")
            page = context.new_page()
            def route_handler(route):
                if route.request.url == SAFE_BROWSER_ORIGIN:
                    route.fulfill(status=200,body=html,
                                  content_type="text/html; charset=utf-8")
                else:
                    route.abort()
            page.route("**/*",route_handler)
            page.goto(SAFE_BROWSER_ORIGIN,wait_until="domcontentloaded",timeout=30000)
            page.wait_for_timeout(250)
            return page.screenshot(full_page=True,animations="disabled")
        finally:
            browser.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy",default=str(Path(__file__).with_name("editorial_criteria_inc105.json")))
    parser.add_argument("--mode",choices=["preview"],default="preview")
    parser.add_argument("--width",type=int,default=390)
    args = parser.parse_args()
    policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))
    gate = baseline_decision(policy,mode=args.mode,width=args.width)
    if gate["status"] == "NOT_VERIFIED" and policy.get("status") != "APPROVED":
        print(json.dumps({"contract":"INC105_VISUAL",
                          "status":"NOT_VERIFIED","reason":gate["reason"]},
                         sort_keys=True))
        return 0
    if gate["status"] == "BLOCKED":
        print(json.dumps({"contract":"INC105_VISUAL",**gate},sort_keys=True))
        return 2
    try:
        actual = capture_synthetic_preview(args.width)
    except Exception as exc:
        print(json.dumps({"contract":"INC105_VISUAL","status":"BLOCKED",
                          "error_class":type(exc).__name__},sort_keys=True))
        return 2
    outcome = baseline_decision(policy,mode=args.mode,width=args.width,
                                screenshot_bytes=actual)
    print(json.dumps({"contract":"INC105_VISUAL",**outcome},sort_keys=True))
    return 0 if outcome["status"]=="PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
