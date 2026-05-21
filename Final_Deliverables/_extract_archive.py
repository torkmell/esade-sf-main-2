"""Extract SusFin_Archive.zip to staging folder (skip Mac metadata + lock files)."""
import zipfile, os, sys, time
sys.stdout.reconfigure(encoding="utf-8")

ZIP_PATH = r"C:\Users\ionva\Desktop\sustainable finance supporting files\SusFin_Archive.zip"
DEST     = r"C:\stg-archive"

SKIP_SUBSTR = ("__MACOSX/", "/.DS_Store", "/._", "/~$")

os.makedirs(DEST, exist_ok=True)

with zipfile.ZipFile(ZIP_PATH, "r") as z:
    all_names = z.namelist()
    keep = [n for n in all_names if not any(s in n for s in SKIP_SUBSTR) and not n.startswith("._")]
    skip = [n for n in all_names if n not in set(keep)]
    print(f"Total entries:  {len(all_names)}")
    print(f"Keeping:        {len(keep)}")
    print(f"Skipping (Mac): {len(skip)}")
    print()
    t0 = time.time()
    for i, n in enumerate(keep):
        if n.endswith("/"):
            os.makedirs(os.path.join(DEST, n), exist_ok=True)
            continue
        try:
            z.extract(n, DEST)
            if (i + 1) % 20 == 0:
                print(f"  [{i+1}/{len(keep)}] extracted")
        except Exception as e:
            print(f"  ERROR extracting {n}: {e}")
    print(f"\nElapsed: {time.time()-t0:.1f}s")

# Final size check
total = 0; total_bytes = 0
for root, dirs, files in os.walk(DEST):
    for f in files:
        try:
            total_bytes += os.path.getsize(os.path.join(root, f))
            total += 1
        except OSError: pass
print(f"\nFiles on disk: {total}  ({total_bytes/(1024*1024):.0f} MB)")
print(f"Staging path:  {DEST}")
