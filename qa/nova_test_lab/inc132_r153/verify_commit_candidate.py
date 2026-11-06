#!/usr/bin/env python3
"""Validate pinned, public-safe QA staging. Does not touch production."""
from pathlib import Path
import hashlib, sys
p=Path(__file__).resolve().parent
checks={
 'implementation/the_lab_app_R153_DUAL_QA.py':'d37840512624592eaf867730e93156ca50eb99e864bdf171f6379823d93291c1',
 'source/the_lab_app_R153_GO_WORK.py':'6e7e70e033d1a9e53105cfe0d3660c3f3366f91d8ed9ce09423dc1ae9a8fede9',
 'tests/R150_BASELINE/the_lab_app.py':'6db176875fdc6b60b9ce437aae2046774bca9495f2864005f4c45d61f355ca73',
}
for name,sha in checks.items():
 f=p/name
 actual=hashlib.sha256(f.read_bytes()).hexdigest()
 if actual!=sha:raise SystemExit(f'HASH DRIFT: {name}: {actual} != {sha}')
 print('PASS',name,actual)
dtm=(p/'tests/DTM/DTM_v1_0_75.sha256').read_text().strip()
assert dtm=='eda8ab935d66ef27c1b8fbf1fb298d1d78d3bafc9e32c0c6044128cd2d119304'
if (p/'tests/DTM/NOVA_DOCUMENTO_TECNICO_MECCANICO_v1.0.75.md').exists():
 raise SystemExit('PRIVATE_DTM_EXPOSED_IN_PUBLIC_STAGING')
for f in p.rglob('*'):
 if f.is_file() and (f.suffix in ('.db','.sqlite','.env','.pem','.key') or '__pycache__' in f.parts):
  raise SystemExit(f'UNSAFE_QA_PAYLOAD: {f.relative_to(p)}')
print('QA_STAGING_INTEGRITY=PASS; NO PRIVATE DTM PRESENT')
