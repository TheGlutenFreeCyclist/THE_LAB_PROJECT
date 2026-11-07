#!/usr/bin/env python3
"""Materialize deterministic QA from R150 or already-integrated R153 TEST root.

This script never edits repo root, does no network and does no deploy.
"""
from pathlib import Path
import hashlib, subprocess, tempfile
R150='6db176875fdc6b60b9ce437aae2046774bca9495f2864005f4c45d61f355ca73'
FTP='6e7e70e033d1a9e53105cfe0d3660c3f3366f91d8ed9ce09423dc1ae9a8fede9'
DUAL='d37840512624592eaf867730e93156ca50eb99e864bdf171f6379823d93291c1'
FIRST_DOSE='b697f775163222869eafb4bdcec4ab2a25a306b892ac52552817c8d0aaa6a790'
INTEGRATED='020117a90b531defa0eba8d94bef665fd64b43d4dc62d883ee2fcee995a38b71'
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]/'the_lab_app.py'

def digest(data):return hashlib.sha256(data).hexdigest()
def check(data,expected,label):
 observed=digest(data)
 if observed!=expected:raise RuntimeError(f'{label}_SHA_DRIFT observed={observed} expected={expected}')
 print(f'PASS {label} {observed}')

def apply(patch,tmp,reverse=False):
 cmd=['git','apply']
 if reverse:cmd.append('-R')
 subprocess.run(cmd+['--check',str(patch)],cwd=tmp,check=True)
 subprocess.run(cmd+[str(patch)],cwd=tmp,check=True)

def main():
 root=ROOT.read_bytes();root_sha=digest(root)
 if root_sha not in (R150,DUAL,FIRST_DOSE,INTEGRATED):
  raise RuntimeError(f'WRONG_TEST_ROOT_SHA {root_sha}: unexpected runtime, no overwrite')
 with tempfile.TemporaryDirectory(prefix='nova_r153_') as tmp:
  app=Path(tmp)/'the_lab_app.py';app.write_bytes(root)
  patch_base=HERE/'patches/R150_to_FTP.patch'
  patch_dual=HERE/'patches/FTP_to_DUAL.patch'
  if root_sha==INTEGRATED:
   apply(HERE/'patches/quality-fix-on-TEST.patch',tmp,reverse=True)
   check(app.read_bytes(),FIRST_DOSE,'REVERSED_QUALITY')
  if root_sha in (FIRST_DOSE,INTEGRATED):
   apply(HERE/'patches/R153_to_R153_CARD2_FIRST_DOSE.patch',tmp,reverse=True)
   check(app.read_bytes(),DUAL,'REVERSED_FIRST_DOSE')
  if root_sha!=R150:
   # Reverse only on scratch copy to recover exact R150 immutable QA baseline.
   apply(patch_dual,tmp,reverse=True);check(app.read_bytes(),FTP,'REVERSED_FTP')
   apply(patch_base,tmp,reverse=True);check(app.read_bytes(),R150,'REVERSED_R150')
  else:check(root,R150,'REMOTE_TEST_ROOT_R150')
  (HERE/'tests/R150_BASELINE').mkdir(parents=True,exist_ok=True)
  (HERE/'tests/R150_BASELINE/the_lab_app.py').write_bytes(app.read_bytes())
  for patch,dest,expected,label in [
      (patch_base,HERE/'source/the_lab_app_R153_GO_WORK.py',FTP,'FTP_STABILIZED_R153'),
      (patch_dual,HERE/'implementation/the_lab_app_R153_DUAL_QA.py',DUAL,'R153_DUAL')]:
   apply(patch,tmp)
   data=app.read_bytes();check(data,expected,label)
   dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
  if root_sha==DUAL and app.read_bytes()!=root:
   raise RuntimeError('RUNTIME_QA_RECONSTRUCTION_MISMATCH')
 print('THIN_QA_BOOTSTRAP_PASS ROOT_='+('R153' if root_sha!=R150 else 'R150')+' NO DEPLOY')
if __name__=='__main__':main()
