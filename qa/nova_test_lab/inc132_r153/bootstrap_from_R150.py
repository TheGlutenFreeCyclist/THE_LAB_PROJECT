#!/usr/bin/env python3
"""Materialize QA-only source from the exact R150 GitHub root. NO DEPLOY."""
from pathlib import Path
import hashlib,subprocess,tempfile
R150='6db176875fdc6b60b9ce437aae2046774bca9495f2864005f4c45d61f355ca73'
FTP='6e7e70e033d1a9e53105cfe0d3660c3f3366f91d8ed9ce09423dc1ae9a8fede9'
DUAL='d37840512624592eaf867730e93156ca50eb99e864bdf171f6379823d93291c1'
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]/'the_lab_app.py'

def check(data,expected,label):
 observed=hashlib.sha256(data).hexdigest()
 if observed!=expected:raise RuntimeError(f'{label}_SHA_DRIFT got={observed} expected={expected}')
 print(f'PASS {label} {observed}')

def main():
 root=ROOT.read_bytes();check(root,R150,'REMOTE_TEST_ROOT_R150')
 base=HERE/'tests/R150_BASELINE/the_lab_app.py'
 base.parent.mkdir(parents=True,exist_ok=True);base.write_bytes(root)
 with tempfile.TemporaryDirectory(prefix='nova_r153_') as tmp:
  app=Path(tmp)/'the_lab_app.py';app.write_bytes(root)
  for patch,dest,expected,label in [
    (HERE/'patches/R150_to_FTP.patch', HERE/'source/the_lab_app_R153_GO_WORK.py', FTP,'FTP_STABILIZED_R153'),
    (HERE/'patches/FTP_to_DUAL.patch', HERE/'implementation/the_lab_app_R153_DUAL_QA.py', DUAL,'R153_DUAL')]:
   subprocess.run(['git','apply','--check',str(patch)],cwd=tmp,check=True)
   subprocess.run(['git','apply',str(patch)],cwd=tmp,check=True)
   data=app.read_bytes();check(data,expected,label)
   dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 print('THIN_QA_BOOTSTRAP_PASS NO DEPLOY')
if __name__=='__main__':main()
