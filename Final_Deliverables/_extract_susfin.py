"""Extract project content from SusFin-main (1).7z, skipping venv / cache / git."""
import os, sys, time
import py7zr

sys.stdout.reconfigure(encoding="utf-8")

ARCHIVE = (
    r"C:\Users\ionva\AppData\Local\Packages\5319275A.WhatsAppDesktop_cv1g1gvanyjgm"
    r"\LocalState\sessions\BD6CFC4552C27B5B3FAAD9D8A3AC6B1B19836776\transfers\2026-21"
    r"\SusFin-main (1).7z"
)
# Short destination path to avoid Windows 260-char limit during extraction
DEST = r"C:\stg-susfin"

# Folders that bloat the archive but aren't project content
SKIP_PATTERNS = [
    "/venv/", "\\venv\\",
    "/.venv/", "\\.venv\\",
    "/__pycache__/", "\\__pycache__\\",
    "/.git/", "\\.git\\",
    "/.ipynb_checkpoints/", "\\.ipynb_checkpoints\\",
    "/node_modules/", "\\node_modules\\",
    "/.pytest_cache/", "\\.pytest_cache\\",
    "/.mypy_cache/", "\\.mypy_cache\\",
]

def should_skip(name: str) -> bool:
    n = name.replace("\\", "/")
    return any(p.replace("\\", "/") in n for p in SKIP_PATTERNS)

os.makedirs(DEST, exist_ok=True)

print(f"Archive: {ARCHIVE}")
print(f"Dest:    {DEST}")

t0 = time.time()
with py7zr.SevenZipFile(ARCHIVE, mode="r") as z:
    all_names = z.getnames()
    keep = [n for n in all_names if not should_skip(n)]
    skip = [n for n in all_names if should_skip(n)]
    print(f"Total entries:  {len(all_names)}")
    print(f"Keeping:        {len(keep)}")
    print(f"Skipping:       {len(skip)}")
    print("\nSample of kept entries (first 20):")
    for n in keep[:20]:
        print(f"  {n}")

# Re-open and extract only the keep set (py7zr requires a fresh handle for targets)
with py7zr.SevenZipFile(ARCHIVE, mode="r") as z:
    print("\nExtracting filtered set...")
    z.extract(path=DEST, targets=keep)
print(f"Extracted in {time.time()-t0:.1f}s")

# verify
total = 0
size_bytes = 0
for root, dirs, files in os.walk(DEST):
    for f in files:
        try:
            size_bytes += os.path.getsize(os.path.join(root, f))
            total += 1
        except OSError:
            pass
print(f"Files on disk in {DEST}: {total}  ({size_bytes/(1024*1024):.1f} MB)")
