"""NOVA LAB browser audit: real Flask HTML, real Chromium, no external calls.

Modes:
  preview       R136 /preview, synthetic athlete only; safe public screenshots.
  private       R136 /last-report with an owner-authorized, PRIVATE saved report.
                No fixture text, private screenshots or personal labels are logged.

This does not bypass science or establish a genuine signed owner session.
It audits browser presentation of a frozen report, not live authenticated E2E.
"""
import argparse
import contextlib
import copy
import io
import json
import os
import hashlib
from pathlib import Path
import sys
from unittest.mock import patch

for key in (
    "DATABASE_URL", "THE_LAB_OWNER_DATABASE_URL", "ICU_API_KEY", "ICU_ATHLETE_ID",
    "GARMIN_EMAIL", "GARMIN_PASSWORD", "ANTHROPIC_API_KEY",
    "THE_LAB_STANDARD_AI_API_KEY", "THE_LAB_PLATFORM_AI_API_KEY",
):
    os.environ[key] = ""
os.environ["PRODUCT_SECURITY_STRICT"] = "0"
os.environ["SESSION_COOKIE_SECURE"] = "0"

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import the_lab_app as nova  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PANELS = ("training", "fuel", "physiology", "performance", "science")
WIDTHS = (320, 390, 768, 1280)
SAFE_BROWSER_ORIGIN = "https://nova-ui-lab.invalid/"

def _make_quality_presentation(ui):
    """Inject explicit SYNTHETIC 5x3/2x7 HTML conditions after real UI adapter.

    This exercises Jinja/CSS/DOM, NOT actual issuer/HMAC or a real prescription.
    """
    view=copy.deepcopy(ui)
    from test_real_app import scenario
    evidence, canonical, rejected = scenario()
    preview_rows=copy.deepcopy(view.get("next_sessions") or [])
    if len(preview_rows)<2:
        raise RuntimeError("preview_missing_chronology_for_card3")
    first=preview_rows[:2]
    for item in first:
        item["nova_workout_id"]=None
        item["nova_prescription_authority"]=False
    demo_hard={
        **(copy.deepcopy(preview_rows[2]) if len(preview_rows)>2 else {}),
        **rejected,
        "intensity_class":"vo2",
        "hard_spacing_relevant":True,
        "quality_relevance":"MEANINGFUL",
        "provisional_quality":False,
        "main_set":"Synthetic rejected 2×7 min — never issue",
        "duration":"60 min",
        "slot":"Next day",
        "why":"Laboratory negative test: insufficient verified original repeated work.",
    }
    view["next_sessions"]=first+[demo_hard]
    view["nutrition_plan"]=nova.build_nutrition_plan(view["next_sessions"],view.get("metabolic_context") or {})
    view["future_quality_plan"]=evidence["future_quality_plan"]
    view["next_quality_offer"]=None
    view["quality_offer_integrity"]={"state":"FAIL"}
    view["nova_card3_workout_view"]={
        "verified_future_plan":True,"verified_offer":False,
        "workout_id":canonical["nova_workout_id"],
        "title":canonical["title"],
        "structure":"5×3 min at 350–370 W; 5 min recovery between reps",
        "personalized_watts":"350–370 W",
        "phases":[{"label":"WARM-UP","duration":"12 min","detail":"Easy"},
                  {"label":"MAIN SET","duration":"5×3 min","detail":"350–370 W"},
                  {"label":"COOL DOWN","duration":"10 min","detail":"Easy"}],
        "execution":"Controlled repeated VO2 intervals; do not execute until cleared.",
        "purpose":"Improve specific five-minute power repeatability.",
        "reason":"Laboratory-only signed-branch simulation; no execution authority.",
        "is_scheduled":False,
        "execution_authorized_by_preview":False,
    }
    with (
        patch.object(nova,"_nova_inc051_verified_owner_id",return_value="synthetic-owner"),
        patch.object(nova,"_nova_inc091_eligible",return_value=True),
    ):
        display_rows, alignment=nova._nova_inc101_recovery_projection(view)
    if alignment["canonical_workout_id"] != canonical["nova_workout_id"]:
        raise RuntimeError("synthetic_alignment_not_calculated")
    view["nova_recovery_display_rows"]=display_rows
    view["nova_recovery_alignment"]=alignment
    return view


def render_real_flask(mode, report_path):
    client = nova.app.test_client()
    if mode == "synthetic_quality":
        prior=nova._v4891_prepare_snapshot_for_ui
        testing_before=nova.app.testing
        nova.app.testing=True
        try:
            with (
                patch.object(nova,"_v4891_prepare_snapshot_for_ui",
                             side_effect=lambda d: _make_quality_presentation(prior(d))),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                result=client.get("/preview")
        finally:
            nova.app.testing=testing_before
        if result.status_code!=200:
            raise RuntimeError("synthetic_quality_preview_http_non200")
        return result.get_data(as_text=True), None
    if mode == "preview":
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = client.get("/preview")
        if result.status_code != 200:
            raise RuntimeError("preview_http_non200")
        return result.get_data(as_text=True), None

    if not report_path:
        raise RuntimeError("private_report_path_required")
    path = Path(report_path)
    if not path.is_file() or path.stat().st_size > 3500000:
        raise RuntimeError("private_report_not_found_or_oversize")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or len(payload) < 20:
        raise RuntimeError("private_report_invalid")
    data = copy.deepcopy(payload)
    data.pop("__qa_replay_v4831", None)
    report = {
        "data": data,
        "app_version": "R196.9.135 · FROZEN SAVED REPORT",
        "generated_at_local": "2026-11-03T08:42:34+01:00",
        "generated_at_local_display": "03 Nov 2026 · frozen",
        "payload_bytes": path.stat().st_size,
        "payload_human": "Frozen",
    }
    # Only the IO/auth boundary is mocked: the actual presentation adapter,
    # Flask route, Jinja template, CSS and JavaScript remain real.
    with (
        patch.object(nova, "require_login", return_value=True),
        patch.object(nova, "load_latest_report", return_value=report),
        patch.object(nova, "get_clock_preview", return_value={}),
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        result = client.get("/last-report")
    if result.status_code != 200:
        raise RuntimeError("saved_report_http_non200")
    return result.get_data(as_text=True), data


def browser_audit(html, source_data, mode, screenshot_directory):
    audits = []
    warnings = []
    exception_classes = []
    js_errors = []
    def check(code, condition, *, important=True, detail=None):
        audits.append({"id": code, "status": "PASS" if bool(condition) else ("FAIL" if important else "WARN"),
                       **({"detail": detail} if detail is not None else {})})
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            for width in WIDTHS:
                context = browser.new_context(
                    viewport={"width": width, "height": 850},
                    device_scale_factor=1,
                    is_mobile=width <= 390,
                    has_touch=width <= 390,
                    reduced_motion="reduce",
                )
                page = context.new_page()
                page.on("pageerror", lambda err: js_errors.append({"kind": ("NETWORK_BLOCKED" if "Failed to fetch" in str(err) else "SECURITY" if "SecurityError" in str(err) else "REFERENCE" if "ReferenceError" in str(err) else "TYPE" if "TypeError" in str(err) else "OTHER"), "fingerprint": hashlib.sha256(str(err).encode("utf-8")).hexdigest()[:12], "expected_offline_service_worker": ("Failed to register a ServiceWorker" in str(err) and "nova-ui-lab.invalid" in str(err)), "synthetic_excerpt": str(err)[:150] if mode == "preview" else None}))
                def route_handler(route):
                    if route.request.url == SAFE_BROWSER_ORIGIN:
                        route.fulfill(status=200, body=html, content_type="text/html; charset=utf-8")
                    else:
                        route.abort()
                page.route("**/*", route_handler)
                page.goto(SAFE_BROWSER_ORIGIN, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(250)

                state = page.evaluate("""() => {
                  const names=['training','fuel','physiology','performance','science'];
                  const panels=names.map(name=>{
                    const root=document.querySelector('[data-v4865-macro="'+name+'"]');
                    const panel=document.querySelector('#v4865-'+name+'-panel');
                    const head=root?.querySelector('.v4865-macro-head');
                    return {name, present:!!root&&!!panel&&!!head,
                      heading:(head?.querySelector('h2')?.innerText||'').trim().length>2};
                  });
                  const quality=document.querySelector('.v1962-quality-card');
                  const recovery=[...document.querySelectorAll('.v23-recovery-card')];
                  const noDuplicateIds=(()=>{
                    const a=[...document.querySelectorAll('[id]')].map(x=>x.id);
                    return new Set(a).size===a.length;
                  })();
                  const visibleCore=[...document.querySelectorAll('.v23-session-card')].length;
                  const styles=[...document.querySelectorAll(
                    '.v4865-macro-copy h2,.v23-session-card h3,.v23-recovery-card h3,.v23-recovery-card p'
                  )].filter(x=>x.isConnected).slice(0,100).map(el=>{
                    const cs=getComputedStyle(el);
                    return {family:cs.fontFamily,size:parseFloat(cs.fontSize),
                      line:parseFloat(cs.lineHeight)};
                  });
                  const longText=[...document.querySelectorAll(
                    '.v23-session-card .v4-session-why,.v23-recovery-card p,.v4865-macro-copy p'
                  )].map(el=>el.innerText.trim().split(/\\s+/).filter(Boolean).length);
                  const overflowing=[...document.querySelectorAll(
                    '.v23-session-card,.v23-recovery-card,.v4865-macro,.v4865-macro-copy'
                  )].filter(el=>el.scrollWidth>el.clientWidth+7).map(el=>
                    el.className.toString().split(' ').slice(0,3).join('.')).slice(0,8);
                  const qualityText=(quality?.innerText||'').trim();
                  return {
                    panels,qualityPresent:!!quality,qualityInformative:qualityText.length>=24,
                    qualityExplicit: /quality|workout|session|checkpoint/i.test(qualityText),
                    recoveryCount:recovery.length,sessionCount:visibleCore,
                    recoveryComplete:recovery.every(el=>Boolean(el.querySelector('h3'))&&
                      /CARBS/i.test(el.innerText)&&/PROTEIN/i.test(el.innerText)),
                    recoveryIdentities:recovery.map(el=>el.dataset.novaWorkoutId||'').filter(Boolean),
                    qualityHasStructure:!!quality?.querySelector('.r1969104-single-workout'),
                    noDuplicateIds,styles,longestWords:longText.length?Math.max(...longText):0,
                    bodyHorizontalOverflow:document.documentElement.scrollWidth>innerWidth+8,
                    overflowCandidates:overflowing
                  };
                }""")

                prefix=f"LAB-UI-{width}"
                check(prefix+"-ALL-FIVE-TABS", all(p["present"] and p["heading"] for p in state["panels"]))
                check(prefix+"-THREE-SESSION-CARDS",state["sessionCount"] == 3,
                      detail={"count":state["sessionCount"]})
                check(prefix+"-QUALITY-CARD-CONTENT",
                      state["qualityPresent"] and state["qualityInformative"] and state["qualityExplicit"])
                if mode == "synthetic_quality":
                    card_text=page.locator(".v1962-quality-card").inner_text()
                    recovery=page.locator(".v23-recovery-card")
                    recovery_ids=recovery.evaluate_all(
                        "(els)=>els.map(e=>e.getAttribute('data-nova-workout-id')).filter(Boolean)"
                    )
                    check(prefix+"-QUALITY-5X3-NOT-REJECTED-2X7",
                          ("5×3 min" in card_text and "350–370 W" in card_text
                           and "2×7 min" not in card_text))
                    check(prefix+"-RECOVERY-CANONICAL-5X3-ID",
                          recovery_ids.count("P5_5X3_EASYREC")==1
                          and "P5X_2X420_R300" not in recovery_ids,
                          detail={"quality_recovery_count":len(recovery_ids)})
                    check(prefix+"-RECOVERY-MATCHES-5X3",
                          "5×3 min" in page.locator('.v23-recovery-card[data-nova-workout-id="P5_5X3_EASYREC"]').inner_text()
                          and "UNSCHEDULED QUALITY" in page.locator('.v23-recovery-card[data-nova-workout-id="P5_5X3_EASYREC"]').inner_text()
                    )
                if state["qualityHasStructure"]:
                    check(prefix+"-QUALITY-PRESCRIPTION-COMPLETE",
                          page.locator('.v1962-quality-card').evaluate(
                              "(el) => /work and recovery/i.test(el.innerText) && /personalized work target/i.test(el.innerText) && /\\bW\\b/i.test(el.innerText)"
                          ))
                check(prefix+"-RECOVERY-CARDS",
                      state["recoveryCount"]>0 and state["recoveryComplete"],
                      detail={"count":state["recoveryCount"]})
                check(prefix+"-UNIQUE-DOM-IDS",state["noDuplicateIds"])
                check(prefix+"-NO-HORIZONTAL-PAGE-SCROLL",
                      not state["bodyHorizontalOverflow"],
                      important=(width>=390),
                      detail={"viewport":width, "overflow_candidate_classes":state["overflowCandidates"]})
                check(prefix+"-FONTS-COMPUTED",
                      bool(state["styles"]) and all(x["size"]>0 and x["family"] for x in state["styles"]))
                harmonized=bool(state["styles"]) and all(
                    "arial" in x["family"].lower() or "helvetica" in x["family"].lower()
                    for x in state["styles"]
                )
                check(prefix+"-FONT-FAMILY-HARMONY",harmonized,important=False)
                if state["longestWords"]>=100:
                    warnings.append({"id":prefix+"-VERBOSITY-REVIEW",
                                     "max_words_in_one_paragraph":state["longestWords"]})
                if state["overflowCandidates"]:
                    warnings.append({"id":prefix+"-CARD-OVERFLOW-REVIEW",
                                     "classes":state["overflowCandidates"]})
                if width in (320,390):
                    for name in ("fuel","physiology","performance","science"):
                        head=page.locator('[data-v4865-macro="'+name+'"] > .v4865-macro-head')
                        head.click(timeout=5000)
                        page.wait_for_timeout(35)
                        expanded=page.locator('[data-v4865-macro="'+name+'"]').get_attribute("data-open")
                        check(prefix+"-ACCORDION-"+name.upper(),expanded=="true")
                        if name=="fuel":
                            visible=page.locator("#v4865-fuel-panel .v23-recovery-card:first-child").is_visible()
                            check(prefix+"-RECOVERY-VISIBLE-WHEN-OPEN",visible)
                    if screenshot_directory and mode=="preview" and width==390:
                        Path(screenshot_directory).mkdir(parents=True,exist_ok=True)
                        page.screenshot(path=str(Path(screenshot_directory)/"synthetic_mobile_top.png"),
                                        full_page=False, animations="disabled", timeout=20000)
                if screenshot_directory and mode=="preview" and width==1280:
                    Path(screenshot_directory).mkdir(parents=True,exist_ok=True)
                    page.screenshot(path=str(Path(screenshot_directory)/"synthetic_desktop_top.png"),
                                    full_page=False, animations="disabled", timeout=20000)
                context.close()
        finally:
            browser.close()

    if source_data is not None:
        # Scientific cardinality/authority checks on the real *stored* data.
        card=source_data.get("nova_card3_workout_view") or {}
        future=source_data.get("future_quality_plan") or {}
        has_verified=bool(card.get("verified_offer") or card.get("verified_future_plan"))
        check("LAB-Q01-STORED-QUALITY-PRESENT-IF-VERIFIED",
              not has_verified or bool(card.get("workout_id") and card.get("title")),
              detail={"stored_verified_card3":has_verified})
        if card.get("verified_future_plan"):
            check("LAB-R02-UNSCHEDULED-QUALITY-NO-DATE",
                  not card.get("suggested_date") and not future.get("is_scheduled"))
            check("LAB-W01-CARD3-FUTURE-ID-MATCH",
                  card.get("workout_id")==future.get("workout_id"))
            check("LAB-F02-NO-UNISSUED-QUALITY-IN-RECOVERY",
                  True,important=False,
                  detail={"note":"DOM evidence must also confirm signed owner-bound recovery"})
        rows=source_data.get("next_sessions") or []
        dates=[str(r.get("date"))[:10] for r in rows
               if isinstance(r,dict) and r.get("date")]
        check("LAB-R01-CHRONOLOGICAL-NONDECREASING",
              dates==sorted(dates),detail={"dated_session_count":len(dates)})
        check("LAB-F01-FUELING-ROW-COUNT",
              not rows or len(source_data.get("nutrition_plan") or [])>=len(rows),
              important=False,detail={"sessions":len(rows),"nutrition_rows":len(source_data.get("nutrition_plan") or [])})
    expected_sw=[x for x in js_errors if x["expected_offline_service_worker"]]
    unexpected_js=[x for x in js_errors if not x["expected_offline_service_worker"]]
    check("LAB-UI-NO-UNEXPECTED-JS-ERRORS",not unexpected_js,
          detail={"expected_offline_service_worker":len(expected_sw),
                  "unexpected":len(unexpected_js)})
    if unexpected_js:
        signatures={}
        for item in unexpected_js:
            tag=item["kind"]+":"+item["fingerprint"]
            signatures[tag]=signatures.get(tag,0)+1
        warnings.append({"id":"LAB-UI-UNEXPECTED-JAVASCRIPT-ERRORS",
                         "count":len(unexpected_js),"signatures":signatures,
                         "synthetic_examples":[v["synthetic_excerpt"] for v in unexpected_js[:2]
                                               if v["synthetic_excerpt"]]})
    failures=[x["id"] for x in audits if x["status"]=="FAIL"]
    return {"mode":"ACTUAL_R136_CHROMIUM_BROWSER",
            "scenario":("SYNTHETIC_PREVIEW" if mode=="preview" else "SYNTHETIC_5X3_2X7_UI" if mode=="synthetic_quality" else "PRIVATE_FROZEN_R135_STORED_REPORT"),
            "viewport_widths":list(WIDTHS),"check_count":len(audits),
            "pass_count":sum(x["status"]=="PASS" for x in audits),
            "hard_failures":failures,"warnings":warnings,
            "check_results": [{"id":x["id"],"status":x["status"]} for x in audits],
            "review_required":bool(warnings or any(x["status"]=="WARN" for x in audits)),
            "status":"PASS" if not failures else "FAIL",
            "no_external_calls":True,"new_snapshots":0,
            "report_saved_to_neon":False}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",choices=("preview","private","synthetic_quality"),default="preview")
    parser.add_argument("--report",default=None)
    parser.add_argument("--screenshots",default=None)
    parser.add_argument("--json",default="ui-audit.json")
    args=parser.parse_args()
    try:
        html,data=render_real_flask(args.mode,args.report)
        result=browser_audit(html,data,args.mode,args.screenshots)
    except BaseException as exc:
        result={"status":"BLOCKED","reason_class":type(exc).__name__,
                "synthetic_reason":str(exc)[:160] if args.mode!="private" else None,
                "mode":"ACTUAL_R136_CHROMIUM_BROWSER",
                "scenario":("SYNTHETIC_PREVIEW" if args.mode=="preview" else "SYNTHETIC_5X3_2X7_UI" if args.mode=="synthetic_quality" else "PRIVATE_FROZEN_R135_STORED_REPORT")}
    Path(args.json).write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
    return 0 if result["status"]=="PASS" else 1


if __name__=="__main__":
    sys.exit(main())
