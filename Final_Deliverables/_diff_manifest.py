"""Compare the extracted SusFin-main folder against the local project.

Outputs a CSV manifest with recommended actions per file:
    KEEP_LOCAL  — file is a local-only session artefact we created (don't touch)
    ADD         — file exists in downloaded but not local (will be added)
    REPLACE     — file exists in both but content differs (download wins by default)
    IDENTICAL   — same content, no action
    LOCAL_ONLY  — file exists in local but not in download (will be kept untouched)
"""
import os, sys, hashlib, csv
sys.stdout.reconfigure(encoding="utf-8")

PROJECT     = r"C:\Users\ionva\Desktop\Sustainable Finance Project"
DOWNLOAD    = r"C:\stg-susfin\SusFin-main"
OUTPUT_CSV  = os.path.join(PROJECT, "Final_Deliverables", "_merge_manifest.csv")
OUTPUT_TXT  = os.path.join(PROJECT, "Final_Deliverables", "_merge_manifest_summary.txt")

# Files / folders we created this session that must NOT be overwritten
KEEP_LOCAL = {
    "notebooks/04b_fundamental_quality.ipynb",
    "outputs/scores/fundamental_quality_2026-05-20.csv",
}
KEEP_LOCAL_PREFIXES = (
    "Final_Deliverables/",
    "docs/financial_filtering_framework/",
    "data/market/fundamentals_cache/",
)
# Folders we ignore entirely in both directions (junk, env, generated)
IGNORE_PREFIXES = (
    "venv/", ".venv/", "__pycache__/", ".git/", ".ipynb_checkpoints/",
    "node_modules/", ".pytest_cache/", ".mypy_cache/", ".claude/",
)

def norm(p: str) -> str:
    return p.replace("\\", "/")

def is_ignored(rel: str) -> bool:
    r = norm(rel)
    return any(r.startswith(p) for p in IGNORE_PREFIXES)

def is_keep_local(rel: str) -> bool:
    r = norm(rel)
    if r in KEEP_LOCAL: return True
    return any(r.startswith(p) for p in KEEP_LOCAL_PREFIXES)

def walk_files(root: str):
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        # prune ignored dirs in-place for speed
        dirnames[:] = [d for d in dirnames if not is_ignored(
            norm(os.path.relpath(os.path.join(dirpath, d), root)) + "/"
        )]
        for f in filenames:
            full = os.path.join(dirpath, f)
            rel = norm(os.path.relpath(full, root))
            if is_ignored(rel): continue
            try:
                size = os.path.getsize(full)
                mtime = os.path.getmtime(full)
            except OSError:
                continue
            out[rel] = {"path": full, "size": size, "mtime": mtime}
    return out

def quick_hash(path: str, max_bytes: int = 2_000_000) -> str:
    """Hash first 2MB for fast equality check on most files."""
    h = hashlib.sha1()
    try:
        with open(path, "rb") as f:
            h.update(f.read(max_bytes))
    except OSError:
        return ""
    return h.hexdigest()

print(f"Scanning local:    {PROJECT}")
local = walk_files(PROJECT)
print(f"  {len(local)} files")

print(f"Scanning download: {DOWNLOAD}")
dl = walk_files(DOWNLOAD)
print(f"  {len(dl)} files")

manifest = []
all_keys = sorted(set(local.keys()) | set(dl.keys()))

for rel in all_keys:
    in_local = rel in local
    in_dl    = rel in dl
    action   = "UNKNOWN"
    detail   = ""

    if is_keep_local(rel):
        # Local session work — preserve unconditionally
        if in_dl and in_local:
            action = "KEEP_LOCAL"
            detail = "Local session artefact; ignoring download version."
        elif in_dl and not in_local:
            action = "KEEP_LOCAL"
            detail = "Reserved namespace for local session work; not pulling download."
        else:
            action = "LOCAL_ONLY"
            detail = "Local session artefact."
    elif in_local and not in_dl:
        action = "LOCAL_ONLY"
        detail = "Exists only locally; will be left untouched."
    elif in_dl and not in_local:
        action = "ADD"
        detail = "New file from download."
    else:  # in both
        size_l, size_d = local[rel]["size"], dl[rel]["size"]
        if size_l != size_d:
            action = "REPLACE"
            detail = f"Sizes differ ({size_l} vs {size_d})."
        else:
            # Same size — compare hash of first 2MB
            hl = quick_hash(local[rel]["path"])
            hd = quick_hash(dl[rel]["path"])
            if hl and hd and hl == hd:
                action = "IDENTICAL"
                detail = "Same size + content hash."
            else:
                action = "REPLACE"
                detail = "Same size but content hash differs."

    manifest.append({
        "rel_path":  rel,
        "action":    action,
        "size_local": local[rel]["size"] if in_local else "",
        "size_dl":    dl[rel]["size"]    if in_dl else "",
        "detail":     detail,
    })

# Write CSV manifest
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["rel_path","action","size_local","size_dl","detail"])
    w.writeheader()
    for row in manifest:
        w.writerow(row)

# Summary stats
counts = {}
for row in manifest:
    counts[row["action"]] = counts.get(row["action"], 0) + 1

# Top-level breakdown for ADD + REPLACE
top_level_changes = {}
for row in manifest:
    if row["action"] in ("ADD", "REPLACE"):
        top = row["rel_path"].split("/", 1)[0]
        top_level_changes.setdefault(top, {"ADD": 0, "REPLACE": 0})[row["action"]] += 1

with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
    def w(s=""):
        print(s); f.write(s + "\n")
    w("="*70)
    w("MERGE MANIFEST — SUMMARY")
    w("="*70)
    w(f"Local files scanned:      {len(local)}")
    w(f"Download files scanned:   {len(dl)}")
    w(f"Total manifest entries:   {len(manifest)}")
    w("")
    w("Action breakdown:")
    for k in ("ADD","REPLACE","IDENTICAL","KEEP_LOCAL","LOCAL_ONLY","UNKNOWN"):
        if counts.get(k):
            w(f"  {k:12s}  {counts[k]:5d}")
    w("")
    w("Top-level folder changes (ADD + REPLACE only):")
    for k in sorted(top_level_changes.keys()):
        v = top_level_changes[k]
        w(f"  {k:30s}  add: {v['ADD']:4d}   replace: {v['REPLACE']:4d}")
    w("")
    w(f"Full manifest: {OUTPUT_CSV}")
