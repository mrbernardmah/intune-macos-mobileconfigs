#!/usr/bin/env python3
"""
Build a trusted root/intermediate certificate .mobileconfig from a PEM or DER file.

Usage:
  python3 make-root-cert-profile.py corp-root-ca.pem "Corp Root CA" > corp-root-ca.mobileconfig
"""
import plistlib
import ssl
import sys
import uuid

if len(sys.argv) != 3:
    sys.exit(__doc__)

path, name = sys.argv[1], sys.argv[2]
raw = open(path, "rb").read()
der = ssl.PEM_cert_to_DER_cert(raw.decode()) if b"BEGIN CERTIFICATE" in raw else raw

ns = uuid.UUID("6f1f3a62-9c0e-4d57-8a41-0b7d2f6e1c10")
slug = name.lower().replace(" ", "-")
prof = {
    "PayloadType": "Configuration", "PayloadVersion": 1, "PayloadScope": "System",
    "PayloadIdentifier": f"io.github.mrbernardmah.intune.cert.{slug}",
    "PayloadUUID": str(uuid.uuid5(ns, slug)).upper(),
    "PayloadDisplayName": f"Trusted Certificate - {name}",
    "PayloadOrganization": "Intune macOS Profiles (community)",
    "PayloadContent": [{
        "PayloadType": "com.apple.security.root", "PayloadVersion": 1,
        "PayloadIdentifier": f"io.github.mrbernardmah.intune.cert.{slug}.1",
        "PayloadUUID": str(uuid.uuid5(ns, slug + "/1")).upper(),
        "PayloadDisplayName": name, "PayloadContent": der,
    }],
}
sys.stdout.buffer.write(plistlib.dumps(prof, sort_keys=False))
