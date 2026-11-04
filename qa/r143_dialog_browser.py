"""Chromium proof for R143 native modal; actual committed Flask/Jinja UI strings.

Synthetic identity and no real HTTP or database credentials; no production access.
"""
from pathlib import Path
import sys
import json
import os
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import the_lab_app as n
from playwright.sync_api import sync_playwright

assert 'R196.9.143' in n.APP_VERSION
TEMPLATE=n.app.jinja_env.from_string(n._R143_PANEL)
DATA={'nova_r142_plan_ui':{'workout_id':'P5_5X3_EASYREC','card':3,
                           'required_minutes':73,'learned_minutes':60.5}}
STATE={'active':True,'workout_id':'P5_5X3_EASYREC','token':'a'*64,
       'feedback':None,'latest_intent':None,'usual_limit':None}
HTML=TEMPLATE.render(data=DATA,is_preview=False,qa_mode=False,download_mode=False,
                     nova_r142_state=STATE,today_iso='2026-11-04',
                     csrf_token=lambda:'safe-test-csrf',
                     url_for=lambda endpoint:'/quality/intent')
PAGE='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'''+n._R143_STYLE+'''<style>body{font-family:Arial,sans-serif;background:#061522;color:#dce8ef;margin:10px}.nova-preview-card{width:360px;max-width:100%;box-sizing:border-box;border:1px solid #24506b;padding:13px;border-radius:14px}.nova-preview-card h2{font-size:19px}</style></head><body><div class="nova-preview-card"><p>FUTURE QUALITY · CONDITIONAL PLAN</p><h2>5-min power · 5×3 min</h2><p>NEEDS A SUITABLE WINDOW · NOT CLEARED</p>'''+HTML+'''</div>'''+n._R143_SCRIPT+'''</body></html>'''

shots=Path('r143-browser-evidence'); shots.mkdir(exist_ok=True)
results=[]
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,**({'executable_path':os.environ['NOVA_LOCAL_CHROMIUM'],'args':['--no-sandbox']} if os.environ.get('NOVA_LOCAL_CHROMIUM') else {}))
    for width,height in [(1280,800),(390,844),(320,650)]:
        page=browser.new_page(viewport={'width':width,'height':height},locale='en-GB')
        console_errors=[]
        page.on('pageerror',lambda error:console_errors.append(str(error)))
        page.set_content(PAGE,wait_until='load')
        trigger=page.locator('[data-r143-open]')
        assert trigger.count()==1
        assert page.locator('#r143-quality-dialog').count()==1
        assert not page.locator('dialog').is_visible()
        entry_height=page.locator('.r143-quality-entry').bounding_box()['height']
        assert entry_height<111,('compact entry failed',width,entry_height)
        assert page.locator('body').evaluate('(e)=>e.scrollWidth<=window.innerWidth'),('horizontal scroll',width)
        page.screenshot(path=str(shots/f'r143-closed-{width}.png'),full_page=True)
        trigger.click()
        dialog=page.locator('dialog')
        assert dialog.is_visible()
        assert dialog.evaluate('(e)=>e.matches(":modal")')
        assert page.locator('[data-r143-section="PLAN"]').is_visible()
        assert not page.locator('[data-r143-section="TOO_LONG"]').is_visible()
        assert page.locator('[data-r143-section="PLAN"] input[name="local_date"]').input_value()=='2026-11-04'
        assert page.locator('[data-r143-section="PLAN"] select[name="daypart"]').input_value()=='EVENING'
        plan_form=page.locator('[data-r143-section="PLAN"] form')
        plan_payload=plan_form.evaluate('(f)=>Object.fromEntries(new FormData(f))')
        assert plan_payload['intent_kind']=='PLAN' and plan_payload['scope']=='ONCE'
        assert plan_payload['minutes']=='73' and plan_payload['csrf_token']=='safe-test-csrf'
        page.locator('input[name=r143_intent_mode][value=TOO_LONG]').check()
        assert page.locator('[data-r143-section="TOO_LONG"]').is_visible()
        assert page.locator('[data-r143-section="PLAN"]').is_hidden()
        assert page.locator('[data-r143-section="PLAN"] input[name="minutes"]').is_disabled()
        short_form=page.locator('[data-r143-section="TOO_LONG"] form')
        short_payload=short_form.evaluate('(f)=>Object.fromEntries(new FormData(f))')
        assert short_payload['intent_kind']=='TOO_LONG' and short_payload['scope']=='ONCE'
        page.locator('[data-r143-short-scope]').select_option('USUAL')
        assert page.locator('[data-r143-once-fields]').is_hidden()
        assert page.locator('[data-r143-once-fields] input[name="local_date"]').is_disabled()
        short_payload=short_form.evaluate('(f)=>Object.fromEntries(new FormData(f))')
        assert short_payload['scope']=='USUAL' and 'local_date' not in short_payload and 'daypart' not in short_payload
        page.locator('[data-r143-short-scope]').select_option('ONCE')
        assert page.locator('[data-r143-once-fields]').is_visible()
        page.screenshot(path=str(shots/f'r143-modal-too-long-{width}.png'),full_page=True)
        page.locator('input[name=r143_intent_mode][value=PLAN]').check()
        assert page.locator('[data-r143-section="PLAN"]').is_visible()
        page.screenshot(path=str(shots/f'r143-modal-plan-{width}.png'),full_page=True)
        page.keyboard.press('Escape')
        assert not dialog.is_visible()
        assert page.evaluate('document.activeElement.classList.contains("r143-open-dialog")')
        trigger.click()
        page.locator('[data-r143-close]').click()
        assert not dialog.is_visible()
        assert not console_errors,console_errors
        results.append({'viewport':width,'entry_height':round(entry_height,2),'dialog_open_close':'PASS',
                        'plan_post':'PASS','short_post':'PASS','scope_switch':'PASS',
                        'console_errors':len(console_errors)})
        page.close()
    browser.close()
print('R143_CHROMIUM_VERDICT',json.dumps({'tested':len(results),'results':results},sort_keys=True))
