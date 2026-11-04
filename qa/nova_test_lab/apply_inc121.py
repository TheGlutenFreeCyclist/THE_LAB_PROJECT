"""INC121 deterministic R140 -> R141 append-only UI correction.
Keeps R140 scientific producer byte-identical. No secrets or data touched.
"""
from pathlib import Path
import ast
import hashlib
import runpy

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "the_lab_app.py"
R139 = "20b3164c075b658ec7814988db5d28b7c48409294a18935caa5cbc22a5d669a4"
R140 = "b16d99be3181d6423457c0b0a1f681315f279b1b0b99eb62f8913c747dd67871"
R141 = "27ff5e828b848d2341c556b0357f496943e6c54a9c2b196eceb2c52f73a2e42c"
FRAGMENT_SHA = "d7c21285fce09c1c9cc00051b08b352d22b4d7ee66dcf721c6e77bd2c9841ef5"

def digest(b):
    return hashlib.sha256(b).hexdigest()

src = SRC.read_bytes()
if digest(src) == R141:
    print("INC121: exact R141 already assembled", R141)
else:
    if digest(src) == R139:
        runpy.run_path(str(Path(__file__).with_name("apply_inc120.py")))
        src = SRC.read_bytes()
    if digest(src) != R140:
        raise SystemExit("INC121: expected R140 source; refuse unexpected baseline")
    patch = Path(__file__).with_name("inc121_grey_placeholder.pyfrag").read_bytes()
    if digest(patch) != FRAGMENT_SHA:
        raise SystemExit("INC121: fragment hash mismatch")
    anchor = b'\n\nif __name__ == "__main__":\n'
    if src.count(anchor) != 1:
        raise SystemExit("INC121: insertion anchor drift")
    candidate = src.replace(anchor, patch + anchor, 1)
    if digest(candidate) != R141:
        raise SystemExit("INC121: candidate digest mismatch")
    ast.parse(candidate.decode("utf-8"), filename=str(SRC))
    SRC.write_bytes(candidate)
    print("INC121: exact R141 assembled", R141)
