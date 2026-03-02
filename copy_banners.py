# -*- coding: utf-8 -*-
"""One-time script: copy 3 banner images from Cursor assets to core/static/onboarding/"""
import os
import shutil

ASSETS = os.path.expandvars(r"%USERPROFILE%\.cursor\projects\c-Users-User-Desktop-Almau-a-mark-1-CharityAlmauWeb\assets")
DST = os.path.join(os.path.dirname(__file__), "core", "static", "onboarding")

# Find files by unique suffix in filename
SUFFIXES = {
    "70ca0cc4-2501-4931-a602-3895d1e859d3": "banner_platform.png",  # O platforme
    "6b04ed1d-2c88-40bf-988c-fa1701674b78": "banner_about.png",      # O nas
    "2c13ce64-3930-431c-a6db-a0bf6dc2505c": "banner_almauni.png",   # AlmaUni
}

os.makedirs(DST, exist_ok=True)
for suffix, dest_name in SUFFIXES.items():
    dest_path = os.path.join(DST, dest_name)
    for root, dirs, files in os.walk(ASSETS):
        for f in files:
            if suffix in f and f.lower().endswith(".png"):
                src_path = os.path.join(root, f)
                shutil.copy2(src_path, dest_path)
                print("OK:", dest_name, "<-", f)
                break
        else:
            continue
        break
    else:
        print("NOT FOUND:", dest_name, "(suffix", suffix + ")")
print("Done.")
