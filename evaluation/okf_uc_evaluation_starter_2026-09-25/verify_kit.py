"""Check the delivered starter's file hashes and JSON syntax (standard library only)."""
from pathlib import Path
import hashlib
import json
import sys

root = Path(__file__).resolve().parent
manifest = json.loads((root / "checksums.json").read_text(encoding="utf-8"))
errors = []
for entry in manifest["files"]:
    path = root / entry["path"]
    if not path.is_file():
        errors.append(f"Missing: {entry['path']}")
        continue
    data = path.read_bytes()
    if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
        errors.append(f"Changed: {entry['path']}")
    try:
        if path.suffix == ".json":
            json.loads(data)
        elif path.suffix == ".jsonl":
            for line in data.decode("utf-8").splitlines():
                if line.strip():
                    json.loads(line)
    except (ValueError, UnicodeError) as exc:
        errors.append(f"Invalid JSON: {entry['path']}: {exc}")
if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)
print(f"Verified {len(manifest['files'])} files. This is an integrity check, not legal validation.")
