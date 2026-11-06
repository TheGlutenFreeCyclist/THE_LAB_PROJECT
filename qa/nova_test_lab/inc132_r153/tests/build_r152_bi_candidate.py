#!/usr/bin/env python3
"""INC132 / BI FTP producer test-only patch, R150 immutable. Not a release."""
import hashlib, json
from pathlib import Path

R150_SHA256 = '6db176875fdc6b60b9ce437aae2046774bca9495f2864005f4c45d61f355ca73'
DTM_SHA256 = 'eda8ab935d66ef27c1b8fbf1fb298d1d78d3bafc9e32c0c6044128cd2d119304'

PATCHES = [
    # BI-002: age changes confidence, not continued existence; test horizons are not input lifetime.
    ("if watts is not None and 0 <= age <= 365:\n            candidates.append((day, label, int(round(watts)), age))",
     "if watts is not None and age >= 0:\n            candidates.append((day, label, int(round(watts)), age))"),
    ("'age_days':age,'stale':age>56,'needs_check':age>56 or",
     "'age_days':age,'stale':age>FTP_ANCHOR_VALID_DAYS,'needs_check':age>FTP_ANCHOR_VALID_DAYS or"),
    # BI-003/005: template selector must use the same dated FTP reference as the band.
    ("tempo_ftp_valid=(ftp.get('available') is True\n        and str(ftp.get('status') or '').upper() in {'VALID','TEST SUPPORTED'}\n        and _v1943_finite(ftp.get('prescription_watts'),80,600) is not None)",
     "tempo_ftp_valid=(_nova_power_coaching_reference(ftp,(slot or {}).get('date')) is not None)"),
    ("# A Tempo session without trusted FTP is not an issuable candidate.",
     "# A Tempo session without an eligible dated owner-scoped FTP reference is not a candidate."),
    ("# Same facts required downstream by the canonical Tempo power band.",
     "# The canonical Tempo band also checks the dated Intervals reference."),
    # BI-003: remove only the FTP formal-test requirement from the existing Tempo band.
    ("        # Only real library identities and the SAME active scientific\n        # dimension are eligible. A stale/model FTP must fail closed.\n        indexed=next((x for x in _NOVA_WORKOUT_LIBRARY if x.get('id')==t.get('id')),{})\n        ftp=ftp_anchor if isinstance(ftp_anchor,dict) else {}\n        watts=_v1943_finite(ftp.get('prescription_watts'),80,600)\n        trusted=(ftp.get('available') is True and\n                 str(ftp.get('status') or '').upper() in {'VALID','TEST SUPPORTED'} and\n                 watts is not None)",
     "        # Exact library identity, matching science dimension, and other dose gates persist.\n        # An eligible Intervals reference is not a completed-work or HARD-clearance proof.\n        indexed=next((x for x in _NOVA_WORKOUT_LIBRARY if x.get('id')==t.get('id')),{})\n        ftp=ftp_anchor if isinstance(ftp_anchor,dict) else {}\n        ref=_nova_power_coaching_reference(ftp,as_of_date)\n        watts=_v1943_finite(ref.get('watts'),80,600) if ref else None\n        trusted=bool(ref and watts is not None)"),
    ("'reason':'TEMPO_REQUIRES_VALID_FTP_AND_CANONICAL_MECHANICS',",
     "'reason':'TEMPO_REQUIRES_DATED_FTP_REFERENCE_AND_CANONICAL_MECHANICS',"),
    ("'source':'VALID_FTP_TEMPO_STARTER_POLICY_NOT_REPEATABILITY',",
     "'source':'DATED_FTP_TEMPO_STARTER_NOT_REPEATABILITY',"),
    ("            'work_domain':'TEMPO_Z3','observed_repeated_work_is_direct_evidence':False,\n            'not_a_pb_or_formal_validation':True,",
     "            'work_domain':'TEMPO_Z3','observed_repeated_work_is_direct_evidence':False,\n            'not_a_pb_or_formal_validation':True,\n            'reference_date':ref['date'],'reference_origin':ref['origin'],\n            'reference_age_days':ref['age_days'],'reference_is_stale':ref['stale'],\n            'test_recommended_nonblocking':ref['needs_check'],\n            'workout_specific_proof': 'NOT_IMPLIED_BY_FTP',\n            'execution_clearance': 'SEPARATE_DOWNSTREAM',"),
    ("'rule':'Cycling Z3 Tempo starter range; current validated FTP required; exact interval mechanics and downstream safety gates unchanged.'",
     "'rule':'Cycling Z3 Tempo starter range from dated FTP reference; exact mechanics, workout-specific evidence and downstream safety gates remain separate.'"),
    # The last downstream attester checks same watt bounds and mechanics; add source to allowed attestation, not arbitrary watts.
    ("band.get('source')=='VALID_FTP_TEMPO_STARTER_POLICY_NOT_REPEATABILITY'",
     "band.get('source')=='DATED_FTP_TEMPO_STARTER_NOT_REPEATABILITY'"),
]

def build(source: Path, output: Path):
    if output.resolve()==source.resolve():
        raise ValueError('NEVER_OVERWRITE_R150')
    raw=source.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=R150_SHA256:
        raise ValueError('R150_SHA256_MISMATCH')
    result=raw.decode('utf-8')
    for old,new in PATCHES:
        count=result.count(old)
        if count!=1:raise ValueError(f'PATCH_DRIFT: {old[:75]!r} count={count}')
        result=result.replace(old,new,1)
    compile(result,str(output),'exec')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(result,encoding='utf-8')
    print(json.dumps({'source_sha256':R150_SHA256,
                      'candidate_sha256':hashlib.sha256(result.encode()).hexdigest(),
                      'dtm_sha256':DTM_SHA256,'patch_count':len(PATCHES),
                      'scope':'QA_OFFLINE_SOURCE_ONLY','production':'NO_GO'},indent=2))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();build(a.source,a.output)
