#!/usr/bin/env python3
"""INC132 R153 TEST-only candidate from R150 exact (BI, BH C07 and human FTP copy).

No production deploy, no database reads/writes, no network. Build is fail-closed
on baseline and integration-anchor drift. Baseline and DTM remain immutable.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

R150_SHA256='6db176875fdc6b60b9ce437aae2046774bca9495f2864005f4c45d61f355ca73'
DTM_SHA256='eda8ab935d66ef27c1b8fbf1fb298d1d78d3bafc9e32c0c6044128cd2d119304'
FILENAME='the_lab_app.py'
END_MARKER='\n\nif __name__ == "__main__":\n'

POSTLUDE=r"""
# INC132 / R196.9.153 TEST CANDIDATE -- single reference, no issuer bypass.
# BI-001..009: Athlete-facing FTP is an owner-scoped, dated Intervals reference;
# an invitation to recheck it is not a numeric-workout issue credential.
INC132_R153_SCHEMA='NOVA-R196.9.153-FTP-REFERENCE-OWNER-SCOPE-1'
_INC132_R153_CONTEXT_BEFORE=build_ftp_anchor_context

def _inc132_r153_scope_token(owner_id):
    if not owner_id:
        return None
    return hmac.new(str(SECRET_KEY).encode('utf-8'),
        ('INC132_FTP_OWNER_V1|'+str(owner_id)).encode('utf-8'), hashlib.sha256).hexdigest()

def build_ftp_anchor_context(history_activities, now=None, user_id=None):
    # Genuine pipeline passes the authenticated owner id and the original
    # context's reads are already constrained to that owner in SQL.
    result=_INC132_R153_CONTEXT_BEFORE(history_activities,now=now,user_id=user_id)
    if not isinstance(result,dict):return result
    out=dict(result)
    out['nova_inc132_owner_token']=_inc132_r153_scope_token(_data_owner_user_id(user_id))
    return out

def _inc132_r153_owner_ok(f, expected_owner_id=None):
    if not isinstance(f,dict):return False
    token=str(f.get('nova_inc132_owner_token') or '')
    if not token:
        # Legacy snapshots are still owner-scoped by the authenticated
        # report loader; never claim an additional R153 owner attestation.
        return expected_owner_id is None
    owner=expected_owner_id
    if owner is None and has_request_context():
        try:owner=_data_owner_user_id()
        except (RuntimeError,PermissionError,AttributeError):return False
    if owner is None:return False
    expected=_inc132_r153_scope_token(owner)
    return bool(expected and hmac.compare_digest(token,expected))

_INC132_R153_OLD_REF=_nova_power_coaching_reference

def _nova_power_coaching_reference(ftp_anchor, as_of_date=None):
    f=ftp_anchor if isinstance(ftp_anchor,dict) else {}
    # A stamped reading from another owner is never a source for a new dose,
    # even if a caller inserts plausible watts and a recent date.
    if f.get('nova_inc132_owner_token') and not _inc132_r153_owner_ok(f):
        return None
    return _INC132_R153_OLD_REF(ftp_anchor,as_of_date)

def _inc132_r153_public_ftp(f,as_of_date=None,expected_owner_id=None):
    if not isinstance(f,dict):f={}
    if f.get('nova_inc132_owner_token') and not _inc132_r153_owner_ok(f,expected_owner_id):
        ref=None
    else:
        ref=_nova_power_coaching_reference(f,as_of_date)
    if not isinstance(ref,dict):
        return {'schema':INC132_R153_SCHEMA,'state':'NOT_AVAILABLE','watts':None,
            'date':None,'source':None,'verification_suggested':False,
            'owner_attested':False,'execution_clearance':'SEPARATE'}
    origin=str(ref.get('origin') or '')
    return {'schema':INC132_R153_SCHEMA,'state':'AVAILABLE',
        'watts':int(ref['watts']),'date':ref['date'],
        'source':('INTERVALS.ICU' if origin.startswith('INTERVALS_')
                  else 'RECORDED 20-MINUTE CALIBRATION'),
        'verification_suggested':bool(ref.get('needs_check')),
        'older_reference':bool(ref.get('stale')),
        'owner_attested':bool(f.get('nova_inc132_owner_token')),
        'execution_clearance':'SEPARATE','not_workout_specific_proof':True}

_INC132_R153_OLD_FTP_TEXT=ftp_anchor_text

def ftp_anchor_text(context):
    ref=_inc132_r153_public_ftp(context)
    if ref['state']=='NOT_AVAILABLE':
        return ('FTP reference: no eligible dated personal value available. '
                'Do not invent watts. Workout-specific science and current '
                'training safety remain independent.')
    check=('You may consider checking this estimate when practical. '
        if ref['verification_suggested'] else '')
    return ('Intervals FTP reference: %d W, dated %s. %s'
            'This is a coaching estimate, not proof of repeatable interval '
            'performance or an authorization for a hard workout.'
            %(ref['watts'],ref['date'],check))

_INC132_R153_OLD_UI=_v4891_prepare_snapshot_for_ui

def _v4891_prepare_snapshot_for_ui(data):
    out=_INC132_R153_OLD_UI(data)
    if not isinstance(out,dict):return out
    result=dict(out)
    # Recompute deterministically from the saved input, never from browser or
    # LLM fields. As-of date comes from the snapshot if available.
    snapshot_day=(str(result.get('snapshot_generated_at_local') or
        result.get('generated_at_local') or
        ((result.get('coach_clock') or {}).get('date') if isinstance(result.get('coach_clock'),dict) else '')
        or '')[:10] or None)
    f=result.get('ftp_anchor')
    result['nova_inc132_ftp_reference']=_inc132_r153_public_ftp(f,snapshot_day)
    return result

# No template re-renders the old TEST/FTP_UP status as the athlete's FTP.
_INC132_R153_FTP_OPEN='{% if data.ftp_anchor %}\n{% set fa = data.ftp_anchor %}'
_INC132_R153_FTP_END='{% if data.aerobic_metabolic_range and data.aerobic_metabolic_range.available %}'
assert HOME_PAGE.count(_INC132_R153_FTP_OPEN)==1,'R153_FTP_PANEL_START_DRIFT'
start=HOME_PAGE.index(_INC132_R153_FTP_OPEN)
finish=HOME_PAGE.find(_INC132_R153_FTP_END,start)
assert start < finish and finish-start<5500,'R153_FTP_PANEL_END_DRIFT'
_INC132_R153_FTP_PANEL='''{% set fr = data.nova_inc132_ftp_reference or {} %}
<article class="v4825-ftp-anchor inc132-ftp-panel" aria-label="Personal Intervals FTP reference">
<div class="v4825-ftp-anchor-head"><div><span>📌 INTERVALS FTP REFERENCE</span><strong>{% if fr.state == 'AVAILABLE' %}{{ fr.watts }} W{% else %}NO DATED PERSONAL REFERENCE{% endif %}</strong></div><b>COACHING ESTIMATE</b></div>
<div class="v4825-ftp-anchor-grid"><div><span>REFERENCE DATE</span><strong>{{ fr.date or '—' }}</strong><small>{{ fr.source or 'PERSONAL SOURCE UNAVAILABLE' }}</small></div></div>
<p>{% if fr.state == 'AVAILABLE' %}This dated FTP remains a reference for pacing. {% if fr.verification_suggested %}You can check or update it when convenient; this does not remove your existing reference. {% endif %}{% else %}Nova does not invent a missing FTP. {% endif %}Evidence for the proposed workout and clearance to do hard training today are assessed separately.</p>
</article>
'''
HOME_PAGE=HOME_PAGE[:start]+_INC132_R153_FTP_PANEL+HOME_PAGE[finish:]
# Mirror a genuinely identical Card3 plan without a duplicate issuer/ledger.
# The C07 adapter is inserted below by the deterministic builder.
HOME_PAGE=apply_card3_mirror(HOME_PAGE,_INC121_GREY_CARD)
# Unit tests check the public template and producer/issuer separately; this
# parse also fails closed if an existing Jinja contract was accidentally cut.
app.jinja_env.parse(HOME_PAGE)
APP_VERSION=('THE LAB · R196.9.153 · INC132 BI FTP REFERENCE AND BH001 C07 VIEW '
             '· ORIGINAL INC083/INC111 ISSUER AND SCIENCE GATES PRESERVED '
             '· TEST ONLY · NO DEPLOY')
"""

def build(source:Path,dtm:Path,adapter:Path,r152_builder:Path,output:Path):
    if source.resolve()==output.resolve():raise ValueError('NEVER_OVERWRITE_R150')
    if hashlib.sha256(source.read_bytes()).hexdigest()!=R150_SHA256:raise ValueError('R150_SOURCE_SHA_MISMATCH')
    # A public QA commit may carry only the verified DTM digest; the full
    # governance document stays private in the user's handover. Digest-only
    # CI is NOT evidence that the private DTM bytes were re-read there.
    dtm_is_digest_only = dtm.suffix == '.sha256'
    observed = (dtm.read_text(encoding='ascii').strip() if dtm_is_digest_only
        else hashlib.sha256(dtm.read_bytes()).hexdigest())
    if observed != DTM_SHA256:raise ValueError('DTM_SHA_MISMATCH')
    spec=importlib.util.spec_from_file_location('r152_builder',r152_builder)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    result=source.read_text(encoding='utf-8')
    for old,new in mod.PATCHES:
        if result.count(old)!=1:raise ValueError('R152_PATCH_DRIFT '+repr(old[:70]))
        result=result.replace(old,new,1)
    # Fix rolling FTP being needlessly flagged for recheck even if dated today:
    # never interpret a missing formal 20-min test as automatic staleness.
    old=("'age_days':age,'stale':age>FTP_ANCHOR_VALID_DAYS,'needs_check':age>FTP_ANCHOR_VALID_DAYS or\n"
         "            origin not in {'INTERVALS_TEST_ESTIMATE','NOVA_COMPLETED_20MIN_TEST'} or not f.get('prescription_watts'),")
    new=("'age_days':age,'stale':age>FTP_ANCHOR_VALID_DAYS,\n"
         "            'needs_check':age>FTP_ANCHOR_VALID_DAYS,")
    if result.count(old)!=1:raise ValueError('R153_CHECK_CADENCE_DRIFT')
    result=result.replace(old,new,1)
    helper=adapter.read_text(encoding='utf-8')
    if helper.count('def apply_card3_mirror(')!=1:raise ValueError('C07_ADAPTER_DRIFT')
    if result.count(END_MARKER)!=1:raise ValueError('R150_MAIN_SENTINEL_DRIFT')
    addition='\n# INC132 R153 C07 template adapter imported unchanged from QA.\n'+helper+'\n'+POSTLUDE
    result=result.replace(END_MARKER,'\n'+addition+END_MARKER,1)
    compile(result,str(output),'exec')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(result,encoding='utf-8')
    report={'baseline_sha256':R150_SHA256,'dtm_sha256':DTM_SHA256,
            'candidate_sha256':hashlib.sha256(result.encode()).hexdigest(),
            'baseline_patch_count':len(mod.PATCHES)+1,
            'dtm_content_verified':not dtm_is_digest_only,
            'source_version':'R196.9.153','product_release':'NO_GO',
            'git_commit':False,'db_access':False,'production_changes':False}
    print(json.dumps(report,indent=2))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('source','dtm','adapter','r152_builder','output'):p.add_argument(name,type=Path)
    args=p.parse_args()
    build(**vars(args))
