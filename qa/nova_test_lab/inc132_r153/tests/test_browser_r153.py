#!/usr/bin/env python3
"""True headless Chromium for the actual complete Jinja template, DEMO ONLY.

No live login, database, Intervals API or private fixtures. Expand the responsive
Performance panel before asserting mobile FTP visibility.
"""
import json
import os
from pathlib import Path
from shutil import which
from playwright.sync_api import sync_playwright
from qa_stub_import import load

HERE=Path(__file__).resolve().parent
CANDIDATE=Path(os.environ.get('INC132_CANDIDATE',HERE/'r153_candidate_test_only.py'))
EVIDENCE=Path(os.environ.get('INC132_EVIDENCE_DIR',HERE/'evidence'))
EVIDENCE.mkdir(parents=True,exist_ok=True)
mod=load(CANDIDATE)
data=mod._v4891_prepare_snapshot_for_ui(mod.build_preview_data())
mod.request.endpoint='preview'
kwargs=dict(days=mod.DAYS_BACK,season_days=mod.SEASON_DAYS_BACK,data=data,error=None,
 css=mod.BASE_CSS,logo=mod.LOGO_B64,brand_wordmark=mod.BRAND_WORDMARK_B64,favicon=mod.FAVICON_B64,
 notes=[],chat_answer=None,chat_error=None,feelings=[],latest_feeling=None,
 app_version=mod.APP_VERSION,clock_preview=mod.get_clock_preview(),
 is_preview=True,report_mode=False,report_meta=None,download_mode=False,
 latest_report_meta=None,chat_context_meta=None)
kwargs.update(mod.inject_v10_memory_context())
html=mod.app.jinja_env.from_string(mod.HOME_PAGE).render(**kwargs)
assert 'inc132-ftp-panel' in html and 'nova-card3-grey-placeholder' not in html
(EVIDENCE/'rendered_DEMO_full_template.html').write_text(html,encoding='utf-8')
results=[]
with sync_playwright() as pw:
 kwargs={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
 if which('chromium'):
  kwargs['executable_path']=which('chromium')
 elif which('google-chrome'):
  kwargs['executable_path']=which('google-chrome')
 browser=pw.chromium.launch(**kwargs)
 for width in (320,390,1280):
  page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1)
  page.set_content(html,wait_until='load')
  if width<761:
   page.locator('[data-v4865-macro="performance"] > .v4865-macro-head').click()
   # Card 3 lives in the Training macro, collapsed by default on mobile.
   page.locator('[data-v4865-macro="training"] > .v4865-macro-head').click()
  panel=page.locator('article.inc132-ftp-panel')
  rect=panel.bounding_box()
  text=panel.inner_text()
  row={'viewport_px':width,'ftp_panel_count':panel.count(),'ftp_panel_visible':panel.is_visible(),
       'ftp_panel_inside_viewport':bool(rect and rect['x']>=-1 and rect['x']+rect['width']<=width+1),
       'no_old_error_copy':all(k not in text for k in ('FTP_EXPLORATORY','RETEST DUE','NO VALIDATED ANCHOR')),
       # Distinguish visible Card 3 from an authorized canonical workout.
       'card3_count':page.locator('.v1962-quality-card').count(),
       'card3_visible':page.locator('.v1962-quality-card').is_visible(),
       'card3_structure_present':'3×10 min' in page.locator('.v1962-quality-card').inner_text(),
       'card3_state_incomplete':'INCOMPLETE' in page.locator('.v1962-quality-card').inner_text(),
       'canonical_quality_container_count':page.locator('.r1969104-single-workout').count(),
       'old_card3_placeholder_count':page.locator('.nova-card3-grey-placeholder').count(),
       'document_horizontal_overflow_px':page.evaluate('document.documentElement.scrollWidth-window.innerWidth')}
  page.screenshot(path=str(EVIDENCE/f'browser_DEMO_{width}px.png'),full_page=False)
  results.append(row)
  page.close()
 browser.close()
print('CARD3 PRESENT in DEMO; canonical verified workout absent. Q01 full-dose and authenticated E2E NOT VERIFIED')
(EVIDENCE/'browser_results_DEMO.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
print(json.dumps(results,indent=2))
assert all(r['ftp_panel_count']==1 and r['ftp_panel_visible'] and r['ftp_panel_inside_viewport']
 and r['no_old_error_copy']
 and r['card3_count']==1 and r['card3_visible'] and r['card3_structure_present']
 and r['old_card3_placeholder_count']==0 and r['document_horizontal_overflow_px']==0
 for r in results)
