#!/usr/bin/env python3
"""INC132 R151 candidate: display Intervals FTP as a dated coaching reference.

Builds ONLY an ephemeral TEST artifact from exact R150. Scientific source,
provenance, selectors, HMAC, activity identities and release gates stay intact.
"""
import argparse
import hashlib
from pathlib import Path

R150_SHA = "6db176875fdc6b60b9ce437aae2046774bca9495f2864005f4c45d61f355ca73"
END_MARKER = '\nif __name__ == "__main__":\n    app.run('

POSTLUDE = r'''
# INC132 R151 TEST candidate — public FTP interpretation, no science changes.
# A dated, plausible Intervals FTP is coaching context, NEVER a proof of
# completed comparable work. Keep all internal audit and reason/source codes.
INC132_FTP_REFERENCE_SCHEMA = "INC132-R151-INTERVALS-REFERENCE-COPY-1"

def _inc132_ftp_public_reference(context, as_of_date=None):
    f = context if isinstance(context, dict) else {}
    ref = _nova_power_coaching_reference(f, as_of_date=as_of_date)
    if not isinstance(ref, dict):
        return {"state": "NOT_AVAILABLE", "watts": None, "date": None,
                "source": "INTERVALS_OR_MEASURED_CALIBRATION",
                "quality_clearance": "SEPARATE_FROM_FTP_REFERENCE",
                "requires_maximal_ftp_retest": False}
    origin = str(ref.get("origin") or "")
    return {"state": "AVAILABLE", "watts": ref.get("watts"),
            "date": ref.get("date"),
            "source": ("INTERVALS_ICU" if origin.startswith("INTERVALS_")
                       else "MEASURED_COMPLETED_CALIBRATION"),
            "older_reference": bool(ref.get("stale")),
            "quality_clearance": "SEPARATE_FROM_FTP_REFERENCE",
            "requires_maximal_ftp_retest": False}

_INC132_FTP_TEXT_BEFORE = ftp_anchor_text

def ftp_anchor_text(context):
    """AI explanation-only; never conflate absent FTP test with bad FTP data."""
    ref = _inc132_ftp_public_reference(context)
    if ref["state"] != "AVAILABLE":
        return ("FTP REFERENCE: no eligible dated Intervals estimate is available "
                "in this analysis. Do not invent a value or request an automatic "
                "maximal FTP test. Assess workout-specific repeatability and "
                "current safety independently.")
    status = "older, use as broad context" if ref["older_reference"] else "dated reference"
    return ("FTP REFERENCE: %s W, %s, %s (%s); Intervals/recorded "
            "calibration is a coaching estimate, not a repeated-work test. "
            "Do not require another FTP test merely to discuss a quality. "
            "Workout-specific watts and execution clearance still require "
            "their own original science and safety checks."
            % (ref["watts"], ref["source"], ref["date"], status))

_INC132_UI_BEFORE = _v4891_prepare_snapshot_for_ui

def _v4891_prepare_snapshot_for_ui(data):
    original = _INC132_UI_BEFORE(data)
    if not isinstance(original, dict):
        return original
    out = dict(original)
    out["nova_inc132_ftp_reference"] = _inc132_ftp_public_reference(
        original.get("ftp_anchor"))
    return out

_INC132_FTP_BLOCK_CLASS = '<article class="v4825-ftp-anchor {{ fa.status_class or \'grey\' }}">'
assert HOME_PAGE.count(_INC132_FTP_BLOCK_CLASS) == 1, "INC132_FTP_CARD_CLASS_DRIFT"
HOME_PAGE = HOME_PAGE.replace(_INC132_FTP_BLOCK_CLASS,
    '<article class="v4825-ftp-anchor grey">\n'
    '{% set fr = data.get("nova_inc132_ftp_reference") or {} %}', 1)

_INC132_FTP_HEAD_OLD = '<div class="v4825-ftp-anchor-head"><div><span>📌 CURRENT FTP ANCHOR</span><strong>{% if fa.anchor_watts %}{{ fa.anchor_watts }} W{% else %}NO VALIDATED ANCHOR{% endif %}</strong></div><b>{{ fa.status }}</b></div>'
_INC132_FTP_HEAD_NEW = '<div class="v4825-ftp-anchor-head"><div><span>📌 FTP REFERENCE · INTERVALS</span><strong>{% if fr.get("state") == "AVAILABLE" %}{{ fr.get("watts") }} W{% else %}NO DATED REFERENCE{% endif %}</strong></div><b>{{ "COACHING REFERENCE" if fr.get("state") == "AVAILABLE" else "SOURCE UNAVAILABLE" }}</b></div>'
assert HOME_PAGE.count(_INC132_FTP_HEAD_OLD) == 1, "INC132_FTP_HEAD_DRIFT"
HOME_PAGE = HOME_PAGE.replace(_INC132_FTP_HEAD_OLD, _INC132_FTP_HEAD_NEW, 1)

_INC132_FTP_DATE_OLD = "<div><span>LAST VALIDATED</span><strong>{{ fa.anchor_date_display or '—' }}</strong><small>{% if fa.age_days is not none %}{{ fa.age_days }} days ago{% else %}No persisted FTP_UP yet{% endif %}</small></div>"
_INC132_FTP_DATE_NEW = '<div><span>REFERENCE DATE</span><strong>{{ fr.get("date") or "—" }}</strong><small>{{ "Earlier estimate: use as orientation" if fr.get("older_reference") else "Current recorded source context" }}</small></div>'
assert HOME_PAGE.count(_INC132_FTP_DATE_OLD) == 1, "INC132_FTP_DATE_DRIFT"
HOME_PAGE = HOME_PAGE.replace(_INC132_FTP_DATE_OLD, _INC132_FTP_DATE_NEW, 1)

_INC132_FTP_PARAGRAPH_OLD = "<p>{% if fa.retest_due %}<strong>REFRESH DUE.</strong> This threshold reference has become stale and should be refreshed before it is treated as a precise workout anchor.{% elif fa.status == 'AGING' %}This threshold reference is still useful, but its confidence is declining as it ages.{% else %}This is the threshold reference THE LAB currently trusts for workout context; it is not changed by a single weaker signal.{% endif %}</p>"
_INC132_FTP_PARAGRAPH_NEW = '<p>Nova uses the dated Intervals FTP for coaching context, not as a pass/fail exam. {% if fr.get("state") == "AVAILABLE" %}This reference informs a broad pacing range, not a guaranteed workout watt target.{% else %}No dated usable reading was available for this Snapshot; Nova does not invent one.{% endif %} Workout-specific repeatability and today\'s intensity clearance are independent. An FTP test is not automatically required.</p>'
assert HOME_PAGE.count(_INC132_FTP_PARAGRAPH_OLD) == 1, "INC132_FTP_PARAGRAPH_DRIFT"
HOME_PAGE = HOME_PAGE.replace(_INC132_FTP_PARAGRAPH_OLD, _INC132_FTP_PARAGRAPH_NEW, 1)

_INC132_FTP_GATE_OLD = '<p>A provisional FTP test is not proof of repeatable power. Nova can now offer controlled exploratory sustained work only when the documented 20–29-minute test remains eligible and the other gates pass.</p>'
_INC132_FTP_GATE_NEW = '<p>Intervals FTP is already considered as a dated pacing reference when available. No additional FTP test is required merely to show training direction. A specific hard-work dose needs independent completed work/recovery evidence, and the current safety and time gates remain in force.</p>'
assert HOME_PAGE.count(_INC132_FTP_GATE_OLD) == 1, "INC132_FTP_GATE_DRIFT"
HOME_PAGE = HOME_PAGE.replace(_INC132_FTP_GATE_OLD, _INC132_FTP_GATE_NEW, 1)

app.jinja_env.parse(HOME_PAGE)
APP_VERSION = ("THE LAB · R196.9.151 · INC132 INTERVALS FTP REFERENCE COPY "
               "· SCIENCE/ISSUER/PROVENANCE R150 UNMODIFIED · TEST ONLY NO-GO")
'''

def build(src: Path, dst: Path) -> None:
    raw = src.read_bytes()
    if hashlib.sha256(raw).hexdigest() != R150_SHA:
        raise ValueError("R150_SOURCE_SHA256_MISMATCH")
    text = raw.decode("utf-8")
    if text.count(END_MARKER) != 1:
        raise ValueError("R150_MAIN_SENTINEL_DRIFT")
    after = text.replace(END_MARKER, "\n" + POSTLUDE + END_MARKER, 1)
    compile(after, str(dst), "exec")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(after, encoding="utf-8")
    print("INC132_R151_CANDIDATE_SOURCE_BUILT / NO_DEPLOY / NO_DB")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    build(args.source, args.output)
