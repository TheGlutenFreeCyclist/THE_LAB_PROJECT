"""Prepare the byte-identical R137 candidate in the isolated Actions checkout only."""
from pathlib import Path
import base64, hashlib, zlib, ast

root = Path(__file__).resolve().parents[2]
source = root / "the_lab_app.py"
old = source.read_bytes()
old_hash = hashlib.sha256(old).hexdigest()
BASE = "00787299059932d65841fd5a73a15604fd02159720db1f0335bdfcf935e8442c"
TARGET = "f708c3bb25d5a0fbe9cd93432d49fe4a4d77caf22d8dd9f98b9beadfea0f81f3"
if old_hash == TARGET:
    print("INC110: already R137, SHA verified")
else:
    if old_hash != BASE:
        raise SystemExit("INC110 BASE SOURCE MISMATCH — do not patch")
    compressed = (Path(__file__).with_name("inc110_patch.z64")).read_text().strip()
    patch = zlib.decompress(base64.b64decode(compressed))
    marker = b'\n\nif __name__ == "__main__":\n'
    if old.count(marker) != 1:
        raise SystemExit("INC110 insertion anchor mismatch")
    new = old.replace(marker, patch + marker, 1)
    ast.parse(new.decode("utf-8"))
    if hashlib.sha256(new).hexdigest() != TARGET:
        raise SystemExit("INC110 target checksum mismatch")
    source.write_bytes(new)
    print("INC110 R137 LAB candidate assembled; source SHA256", TARGET)
