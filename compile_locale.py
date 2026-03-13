#!/usr/bin/env python
"""Compile .po files to .mo (no gettext/msgfmt required). Run from project root."""
import os
from pathlib import Path

try:
    import polib
except ImportError:
    print("Install polib: pip install polib")
    raise SystemExit(1)

BASE = Path(__file__).resolve().parent
LOCALE = BASE / "locale"
if not LOCALE.exists():
    print("No locale/ folder found.")
    raise SystemExit(0)

for po_path in LOCALE.rglob("django.po"):
    mo_path = po_path.with_suffix(".mo")
    po = polib.pofile(str(po_path))
    po.save_as_mofile(str(mo_path))
    print("Compiled:", mo_path.relative_to(BASE))

print("Done.")
