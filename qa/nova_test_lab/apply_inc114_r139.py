"""Assemble the exact NOVA R196.9.139 candidate on the QA runner only.

Tracked production code in this repository remains unchanged on main.
The test checkout starts from the R136 blob and inserts the byte-for-byte
R137+R138+R139 delta retained in inc114_r139_insert.pyfrag.
"""
from pathlib import Path
import hashlib
import ast

root = Path(__file__).resolve().parents[2]
app = root / "the_lab_app.py"
frag_file = Path(__file__).with_name("inc114_r139_insert.pyfrag")
BASE = "00787299059932d65841fd5a73a15604fd02159720db1f0335bdfcf935e8442c"
FRAGMENT = "530117334a2bd1ffcae65c25fdd7bbbacd08fca73b76a078fa15e18cf02cdca6"
TARGET = "20b3164c075b658ec7814988db5d28b7c48409294a18935caa5cbc22a5d669a4"

def sha(b):
    return hashlib.sha256(b).hexdigest()

source = app.read_bytes()
if sha(source) == TARGET:
    print("INC114: exact R139 already assembled", TARGET)
else:
    if sha(source) != BASE:
        raise SystemExit(f"INC114: base mismatch ({sha(source)}), refuse to patch")
    fragment = frag_file.read_bytes()
    if sha(fragment) != FRAGMENT:
        raise SystemExit("INC114: fragment checksum mismatch")
    anchor = b'\n\nif __name__ == "__main__":\n'
    if source.count(anchor) != 1:
        raise SystemExit("INC114: insertion anchor mismatch")
    candidate = source.replace(anchor, fragment + anchor, 1)
    if sha(candidate) != TARGET:
        raise SystemExit(f"INC114: target mismatch ({sha(candidate)})")
    ast.parse(candidate.decode("utf-8"), filename=str(app))
    app.write_bytes(candidate)
    print("INC114: exact R139 assembled", TARGET)
