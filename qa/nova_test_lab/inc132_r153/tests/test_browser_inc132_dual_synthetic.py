"""Visual-only Chromium acceptance for *synthetic* dual snapshot presentation.

This intentionally bypasses no production seal: it invokes Jinja with a fake
local data object solely for responsive/card layout assertions. An authenticated
Snapshot is required to establish the scientific/owner proof.
"""
import json,os
from pathlib import Path
from shutil import which
from playwright.sync_api import sync_playwright
from qa_stub_import import load
ROOT=Path(__file__).resolve().parent
mod=load(ROOT.parent/'implementation/the_lab_app_R153_DUAL_QA.py')
TARGET=ROOT.parent/'implementation'/'browser'/'dual_synthetic'
TARGET.mkdir(parents=True,exist_ok=True)
base=mod._v4891_prepare_snapshot_for_ui(mod.build_preview_data())
base['inc132_dual_quality']={
 'schema':'UI_SYNTHETIC_TEST_NOT_A_SIGNED_PLAN',
 'quality_specific':{'complete':True,'workout_id':'SYNTHETIC_SPECIFIC'},
 'quality_integrative':{'complete':True,'workout_id':'SYNTHETIC_TEMPO',
   'title':'Synthetic 2×12 Tempo · layout test',
   'duration_minutes':49,'structure':'2×12 min; 5 min easy between',
   'why':'Synthetic copy for layout; not an exercise prescription',
   'power_display':'200–210 W',
   'fueling':{'display':'Synthetic indoor fueling','outdoor_display':'Synthetic outdoor fueling'}},
 'recommended_priority':'CARD2','reason_code':'SYNTHETIC_TEST'}
mod.request.endpoint='preview'
args=dict(days=mod.DAYS_BACK,season_days=mod.SEASON_DAYS_BACK,data=base,
 error=None,css=mod.BASE_CSS,logo=mod.LOGO_B64,brand_wordmark=mod.BRAND_WORDMARK_B64,
 favicon=mod.FAVICON_B64,notes=[],chat_answer=None,chat_error=None,feelings=[],
 latest_feeling=None,app_version=mod.APP_VERSION,clock_preview=mod.get_clock_preview(),
 is_preview=True,report_mode=False,report_meta=None,download_mode=False,
 latest_report_meta=None,chat_context_meta=None)
args.update(mod.inject_v10_memory_context())
html=mod.app.jinja_env.from_string(mod.HOME_PAGE).render(**args)
(TARGET/'synthetic_dual.html').write_text(html)
results=[]
with sync_playwright() as pw:
 kw={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
 if which('chromium'):kw['executable_path']=which('chromium')
 elif which('google-chrome'):kw['executable_path']=which('google-chrome')
 browser=pw.chromium.launch(**kw)
 for width in (320,390,1280):
  page=browser.new_page(viewport={'width':width,'height':900})
  page.set_content(html,wait_until='load')
  if width<761:
   page.locator('[data-v4865-macro="training"] > .v4865-macro-head').click()
  tempo=page.locator('.inc132-dual-work')
  found=tempo.count()==1 and tempo.is_visible()
  txt=tempo.inner_text() if found else ''
  row={'width':width,'card2_tempo_visible':found,'synthetic_watt_range_present':'200–210 W' in txt,
      'selected_card_count':page.locator('.inc132-selected').count(),
      'horizontal_overflow_px':page.evaluate('document.documentElement.scrollWidth-window.innerWidth')}
  page.screenshot(path=str(TARGET/f'card2_synthetic_{width}.png'),full_page=False)
  results.append(row);page.close()
 browser.close()
(TARGET/'results.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
assert all(r['card2_tempo_visible'] and r['synthetic_watt_range_present']
 and r['selected_card_count']==1 and r['horizontal_overflow_px']==0 for r in results)
