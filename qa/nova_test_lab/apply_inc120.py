"""INC120 deterministic R139->R140 assembly; no data, no secrets, no new branches."""
from pathlib import Path
import ast, base64, hashlib, zlib

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "the_lab_app.py"
FRAGMENT = Path(__file__).with_name("inc120_quality_placement.zlib.b64")
BEFORE = "20b3164c075b658ec7814988db5d28b7c48409294a18935caa5cbc22a5d669a4"
FRAG_HASH = "cf27f5043ed822602942b96ada62884aa0ae60c5db14f9182bc733b87ba23069"
AFTER = "b16d99be3181d6423457c0b0a1f681315f279b1b0b99eb62f8913c747dd67871"

def digest(data):
    return hashlib.sha256(data).hexdigest()

original = SRC.read_bytes()
if digest(original) == AFTER:
    print("INC120: exact candidate already assembled", AFTER)
else:
    if digest(original) != BEFORE:
        raise SystemExit("INC120: unrecognized base source, refusing to patch")
    packed = base64.b64decode("".join(FRAGMENT.read_text().split()), validate=True)
    patch = zlib.decompress(packed)
    if digest(patch) != FRAG_HASH:
        raise SystemExit("INC120: fragment checksum mismatch")
    anchor = b'\n\nif __name__ == "__main__":\n'
    if original.count(anchor) != 1:
        raise SystemExit("INC120: insertion anchor drift")
    updated = original.replace(anchor, patch + anchor, 1)
    if digest(updated) != AFTER:
        raise SystemExit("INC120: final R140 checksum mismatch")
    ast.parse(updated.decode("utf-8"), filename=str(SRC))
    SRC.write_bytes(updated)
    print("INC120: exact R140 assembled", AFTER)
