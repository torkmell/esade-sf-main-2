"""Detailed inspection: list contents of every company folder in the archive."""
import zipfile, sys, os
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")

ZIP_PATH = r"C:\Users\ionva\Desktop\sustainable finance supporting files\SusFin_Archive.zip"
SKIP_PREFIXES = ("__MACOSX/", "SusFin_Archive/.DS_Store", "SusFin_Archive/~$")

with zipfile.ZipFile(ZIP_PATH, "r") as z:
    names = [n for n in z.namelist()
             if not any(n.startswith(p) for p in SKIP_PREFIXES)
             and not n.endswith(".DS_Store")]

# Group by company folder (the depth-1 entry under SusFin_Archive/)
by_folder = defaultdict(list)
for n in names:
    parts = n.split("/")
    if len(parts) < 3 or not parts[2]:
        continue
    company = parts[1]
    rel_inside = "/".join(parts[2:])
    if rel_inside and not rel_inside.startswith("._"):
        by_folder[company].append(rel_inside)

print(f"Companies with files: {len(by_folder)}")
print()

# Print everything
for company in sorted(by_folder.keys()):
    files = sorted(set(by_folder[company]))
    print(f"=== {company} ({len(files)} files) ===")
    for f in files:
        print(f"  {f}")
    print()
