"""Generate an ephemeral R151 TEST candidate from exact R150 + proven C07 adapter.

NEVER writes to the repository or to production unless explicitly invoked with
an output path. GitHub Actions uses an isolated checkout and read-only token.
"""
import hashlib
import json
from pathlib import Path

ORIGINAL_SHA256 = '6db176875fdc6b60b9ce437aae2046774bca9495f2864005f4c45d61f355ca73'
DTM_SHA256 = '7ebd387abee2ef1479e26000c0244928c9bdfb1689882cb77ff567c6fabc3a27'
END = '\n\nif __name__ == "__main__":\n'


def build(source: Path, adapter: Path, output: Path):
    original = source.read_bytes()
    if hashlib.sha256(original).hexdigest() != ORIGINAL_SHA256:
        raise ValueError('UNVERIFIED_R150_SOURCE')
    base = original.decode('utf-8')
    if base.count(END) != 1:
        raise ValueError('R150_ENTRYPOINT_CHANGED')
    helper = adapter.read_text(encoding='utf-8')
    if helper.count('def apply_card3_mirror(') != 1:
        raise ValueError('MIRROR_ADAPTER_CHANGED')
    addition = ( '\n\n# INC132 / R196.9.151 — BH-001 C07 VIEW RESTORATION (TEST CANDIDATE).\n'
        '# Verified canonical Card 3 data remains visible even if C1/2 contain\n'
        '# an equivalent plan or unrelated calendar HARD. No new issuer, dose,\n'
        '# Calendar/ledger writes, date, execution authority or user identity.\n'
        + helper
        + '\nHOME_PAGE = apply_card3_mirror(HOME_PAGE, _INC121_GREY_CARD)\n'
        + 'app.jinja_env.parse(HOME_PAGE)\n'
        + "APP_VERSION = ('THE LAB · R196.9.151 · INC132 BH001 C07 CANONICAL VIEW '"
          "'· R150 SCIENCE UNCHANGED · LAB ONLY · NO AUTO-DEPLOY')\n")
    new = base.replace(END, addition + END, 1).encode('utf-8')
    if output.resolve() == source.resolve():
        raise ValueError('NO_IN_PLACE_SOURCE_WRITE_ALLOWED')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(new)
    gitsha = hashlib.sha1(b'blob ' + str(len(new)).encode() + b'\0' + new).hexdigest()
    print(json.dumps({'suite':'INC132_R151_EPHEMERAL_SOURCE_BUILD',
        'status':'SOURCE_CANDIDATE_ONLY', 'source_sha256':ORIGINAL_SHA256,
        'candidate_sha256':hashlib.sha256(new).hexdigest(),
        'candidate_git_blob':gitsha, 'dtm_sha256':DTM_SHA256,
        'source_changed_in_repo':False, 'product_release':'NO_GO'}, sort_keys=True))

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 4:
        raise SystemExit('Usage: build_inc132_c07_candidate.py SOURCE ADAPTER OUTPUT')
    build(*(Path(x) for x in sys.argv[1:]))
