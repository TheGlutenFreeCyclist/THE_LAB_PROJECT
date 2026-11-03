"""INC107 synthetic-only owner editorial review pack.

Render the actual R136 Flask Preview in Chromium, collect safe metrics and
screenshots for explicit human approval. Aesthetics/text usefulness are NEVER
certified just because the renderer has no overflow.
"""
import argparse
import collections
import json
import os
from pathlib import Path
import sys
for k in ("DATABASE_URL","THE_LAB_OWNER_DATABASE_URL","ICU_API_KEY",
          "ICU_ATHLETE_ID","GARMIN_EMAIL","GARMIN_PASSWORD",
          "ANTHROPIC_API_KEY","THE_LAB_STANDARD_AI_API_KEY",
          "THE_LAB_PLATFORM_AI_API_KEY"):
    os.environ[k]=""
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from run_ui_browser import render_real_flask,SAFE_BROWSER_ORIGIN
from playwright.sync_api import sync_playwright


def run(outdir):
    dest=Path(outdir)
    dest.mkdir(parents=True,exist_ok=True)
    html, _ = render_real_flask("preview",None)
    metrics=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=[
            "--no-sandbox","--disable-dev-shm-usage"])
        try:
            for width in (320,390,768,1280):
                ctx=browser.new_context(
                    viewport={"width":width,"height":850},
                    reduced_motion="reduce",device_scale_factor=1,
                    is_mobile=width<=390,has_touch=width<=390)
                page=ctx.new_page()
                page.route("**/*",lambda route: route.fulfill(
                    status=200,body=html,content_type="text/html; charset=utf-8")
                    if route.request.url==SAFE_BROWSER_ORIGIN else route.abort())
                page.goto(SAFE_BROWSER_ORIGIN,wait_until="domcontentloaded")
                page.wait_for_timeout(250)
                # Expand accordion panels; all screenshots remain synthetic.
                if width==390:
                    for name in ("fuel","physiology","performance","science"):
                        panel=page.locator('[data-v4865-macro="'+name+'"]')
                        if panel.count() and panel.get_attribute("data-open")!="true":
                            panel.locator(".v4865-macro-head").first.click()
                browser_state=page.evaluate("""() => {
                  const targets=[...document.querySelectorAll(
                    '.v1962-quality-card,.v23-recovery-card,.v4865-macro-copy,.v23-session-card')];
                  const p=[...document.querySelectorAll('p')];
                  const fam={};
                  for(const el of [...document.querySelectorAll('h1,h2,h3,p')].slice(0,400)){
                    const css=getComputedStyle(el), font=css.fontFamily;
                    fam[font]=(fam[font]||0)+1;
                  }
                  const wordCount=e=>(e.innerText||'').trim().split(/\\s+/).filter(Boolean).length;
                  return {
                    horizontal_overflow:document.documentElement.scrollWidth>innerWidth+8,
                    clipped_count:targets.filter(e=>e.scrollWidth>e.clientWidth+7).length,
                    paragraph_count:p.length,
                    longest_paragraph_words:Math.max(0,...p.map(wordCount)),
                    typography_families:fam,
                    quality_card_count:document.querySelectorAll('.v1962-quality-card').length,
                    recovery_card_count:document.querySelectorAll('.v23-recovery-card').length
                  }
                }""")
                page.screenshot(path=str(dest/f"inc107_preview_{width}.png"),
                                animations="disabled",full_page=False)
                card=page.locator(".v1962-quality-card")
                if card.count()==1 and card.is_visible():
                    card.screenshot(path=str(dest/f"inc107_card3_{width}.png"),
                                    animations="disabled",timeout=20000)
                metrics.append({"width":width,**browser_state})
                ctx.close()
        finally:
            browser.close()
    (dest/"review_metrics.json").write_text(json.dumps({
        "schema":"INC107_VISUAL_REVIEW_V1",
        "content_source":"R136_REAL_FLASK_SYNTHETIC_PREVIEW_ONLY",
        "owner_review_status":"NOT_VERIFIED",
        "aesthetic_harmony":"NOT_VERIFIED",
        "text_usefulness":"NOT_VERIFIED",
        "comparison_reference_approved":False,
        "mechanical_observations":metrics},indent=2),encoding="utf-8")
    if any(x["horizontal_overflow"] for x in metrics):
        print(json.dumps({"suite":"INC107_EDITORIAL","mechanical_status":"FAIL",
                          "human_status":"NOT_VERIFIED","reason":"horizontal_overflow"}))
        return 1
    print(json.dumps({"suite":"INC107_EDITORIAL","mechanical_status":"PASS",
                      "human_status":"NOT_VERIFIED",
                      "screenshots":"synthetic_only","viewports":len(metrics)}))
    return 0


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",default="inc107-ui-review")
    args=parser.parse_args()
    raise SystemExit(run(args.out))
