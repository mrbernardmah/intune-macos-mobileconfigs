#!/usr/bin/env python3
"""Lint every .mobileconfig under macOS-26-27/: parses, required keys, unique identifiers/UUIDs."""
import plistlib
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
UUID_RE = re.compile(r"^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$")
TOP = ["PayloadType", "PayloadVersion", "PayloadIdentifier", "PayloadUUID",
       "PayloadDisplayName", "PayloadContent", "PayloadScope"]
INNER = ["PayloadType", "PayloadVersion", "PayloadIdentifier", "PayloadUUID"]

errors, seen_ids, seen_uuids, count = [], {}, {}, 0
for f in sorted(root.rglob("*.mobileconfig")):
    count += 1
    try:
        p = plistlib.loads(f.read_bytes())
    except Exception as e:
        errors.append(f"{f.name}: not a valid plist ({e})")
        continue
    for k in TOP:
        if k not in p:
            errors.append(f"{f.name}: missing top-level {k}")
    if p.get("PayloadType") != "Configuration":
        errors.append(f"{f.name}: PayloadType must be Configuration")
    if p.get("PayloadScope") not in ("System", "User"):
        errors.append(f"{f.name}: bad PayloadScope")
    items = [p] + list(p.get("PayloadContent", []))
    for item in items:
        for k in INNER:
            if k not in item:
                errors.append(f"{f.name}: payload missing {k}")
        u, i = item.get("PayloadUUID", ""), item.get("PayloadIdentifier", "")
        if not UUID_RE.match(u):
            errors.append(f"{f.name}: bad UUID {u}")
        if u in seen_uuids:
            errors.append(f"{f.name}: duplicate UUID also in {seen_uuids[u]}")
        if i in seen_ids:
            errors.append(f"{f.name}: duplicate identifier also in {seen_ids[i]}")
        seen_uuids[u], seen_ids[i] = f.name, f.name
    # referenced certificate UUIDs must exist in the same profile
    inner_uuids = {i.get("PayloadUUID") for i in p.get("PayloadContent", [])}
    for item in p.get("PayloadContent", []):
        ref = item.get("PayloadCertificateUUID")
        if ref and ref not in inner_uuids:
            errors.append(f"{f.name}: PayloadCertificateUUID {ref} not in profile")

print(f"Checked {count} profiles")
if errors:
    print("\n".join(errors))
    sys.exit(1)
print("All OK")
