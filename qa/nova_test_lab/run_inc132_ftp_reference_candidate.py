#!/usr/bin/env python3
"""Isolated regression for R151 FTP reference presentation, never a release gate."""
import json
import sys
from pathlib import Path
from datetime import timedelta
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import the_lab_app as nova


def assert_true(value, label):
    if not value:
        raise AssertionError(label)


def run():
    assert_true("R196.9.151" in nova.APP_VERSION, "WRONG_TEST_CANDIDATE")
    today = nova.get_rome_now().date()
    ftp = {"current_rolling_ftp": 274,
           "current_rolling_date": (today - timedelta(days=9)).isoformat(),
           "available": False, "anchor_watts": None,
           "status": "NO TEST-BACKED FTP", "prescription_watts": None}
    original = dict(ftp)
    ref = nova._inc132_ftp_public_reference(ftp, today)
    assert_true(ref["state"] == "AVAILABLE" and ref["watts"] == 274,
                "INTERVALS_DATED_REFERENCE_WAS_LOST")
    assert_true(ref["source"] == "INTERVALS_ICU", "WRONG_REFERENCE_SOURCE")
    assert_true(ref["requires_maximal_ftp_retest"] is False,
                "AUTOMATIC_FTP_RETEST_REINTRODUCED")
    assert_true(ftp == original, "INPUT_FTP_MUTATED")
    message = nova.ftp_anchor_text(ftp)
    assert_true("274 W" in message and "INTERVALS" in message,
                "INTERVALS_NOT_ACKNOWLEDGED_TO_COACH")
    assert_true("NO TEST-BACKED FTP" not in message,
                "LEGACY_FTP_ERROR_LEAKED_TO_COACH")

    older = {"current_rolling_ftp": 272,
             "current_rolling_date": (today - timedelta(days=100)).isoformat()}
    older_ref = nova._inc132_ftp_public_reference(older, today)
    assert_true(older_ref["state"] == "AVAILABLE" and older_ref["older_reference"],
                "OLDER_INTERVALS_REFERENCE_WAS_SUPPRESSED")
    missing = nova._inc132_ftp_public_reference({}, today)
    assert_true(missing["state"] == "NOT_AVAILABLE" and missing["watts"] is None,
                "MISSING_FTP_VALUE_FABRICATED")

    # Real Jinja template segment, not a mock of the card HTML.
    page = nova.HOME_PAGE
    anchor = "{% if data.ftp_anchor %}"
    start = page.index(anchor)
    stop = page.index("</article>", start) + len("</article>")
    renderer = nova.app.jinja_env.from_string(page[start:stop] + "{% endif %}")
    display = renderer.render(data={"ftp_anchor": ftp,
                                    "nova_inc132_ftp_reference": ref})
    assert_true("274 W" in display and "COACHING REFERENCE" in display,
                "UI_FAILED_TO_DISPLAY_INTERVALS_FTP")
    for outdated in ("NO VALIDATED ANCHOR", "REFRESH DUE.", "NO TEST-BACKED FTP",
                     "FTP_EXPLORATORY", "TEMPO_REQUIRES_VALID_FTP"):
        assert_true(outdated not in display, "LEGACY_FTP_ERROR_IN_ATHLETE_UI")
    absent_display = renderer.render(data={"ftp_anchor": {"available": False},
                                           "nova_inc132_ftp_reference": missing})
    assert_true("NO DATED REFERENCE" in absent_display and "274 W" not in absent_display,
                "MISSING_FTP_UI_INVENTED_VALUE")

    # The original scientific issuer proof must reject FTP-only estimates.
    template = next((t for t in nova._NOVA_WORKOUT_LIBRARY
                     if t.get("pattern") == "STANDARD" and
                     t.get("goal") == "POWER_5"), None)
    assert_true(isinstance(template, dict), "CANONICAL_TEMPLATE_UNAVAILABLE")
    dimension = next(iter(template["dimensions"]))
    attempted = {"nova_workout_id": template["id"],
                 "nova_prescription_dimension": dimension,
                 "power_prescription": {
                     "state": "PRESCRIBED",
                     "source": "INTERVALS_DATED_FTP_EXPLORATORY",
                     "low_watts": 280, "high_watts": 300}}
    science = nova._nova_inc083_science_replay(
        attempted, {}, None, {"scientific_progression": {"dimension": dimension}})
    assert_true(science.get("accepted") is False,
                "FTP_ESTIMATE_BYPASSED_ORIGINAL_SCIENCE")
    assert_true(science.get("reason") == "CURRENT_NUMERIC_SOURCE_NOT_REPEATED_WORK_PROVEN",
                "INC111_ORIGINAL_REASON_SEMANTICS_CHANGED")

    with nova.app.test_client() as client:
        response = client.get("/healthz")
        assert_true(response.status_code == 204, "INERT_HEALTHZ_FAILED")

    print(json.dumps({
        "suite": "INC132_R151_INTERVALS_FTP_REFERENCE_CANDIDATE",
        "status": "PASS_TEST_CANDIDATE_ONLY",
        "intervals_reference_accepted_for_coaching": True,
        "ftp_errors_removed_from_tested_athlete_card": True,
        "missing_ftp_not_fabricated": True,
        "science_replay_rejects_unproven_ftp_only_dose": True,
        "new_owner_authenticated_snapshot": "NOT_VERIFIED",
        "raw_fit_provenance": "NOT_VERIFIED",
        "card2_card3_release": "RED",
        "production": "NO_GO",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
