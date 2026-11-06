from pathlib import Path
import hashlib,sys
BASE=Path(__file__).resolve().parents[1]/'source/the_lab_app_R153_GO_WORK.py'
PATCH=Path(__file__).with_name('inc132_dual_quality_extension.py')
OUTPUT=Path(__file__).with_name('the_lab_app_R153_DUAL_QA.py')
EXPECTED='6e7e70e033d1a9e53105cfe0d3660c3f3366f91d8ed9ce09423dc1ae9a8fede9'

def build():
 b=BASE.read_bytes()
 if hashlib.sha256(b).hexdigest()!=EXPECTED:raise ValueError('FTP_STABILIZED_R153_BASELINE_DRIFT')
 marker=b'\nif __name__ == "__main__":\n'
 if b.count(marker)!=1:raise ValueError('MAIN_GUARD_DRIFT')
 ext=PATCH.read_bytes()+b'\n'+PATCH.with_name('inc132_ui_patch.py.txt').read_bytes()
 out=b.replace(marker,b'\n\n'+ext+marker,1)
 compile(out.decode('utf-8'),str(OUTPUT),'exec')
 OUTPUT.write_bytes(out)
 print('baseline',hashlib.sha256(b).hexdigest())
 print('candidate',hashlib.sha256(out).hexdigest())
 print('bytes',len(out))
 return OUTPUT
if __name__=='__main__':build()
