"""Execute the merge per the approved manifest.

Strategy:
  - ADD       : copy file from download → local
  - REPLACE   : copy file from download → local (overwrite)
  - IDENTICAL : no action
  - KEEP_LOCAL: no action (local session work)
  - LOCAL_ONLY: no action (kept)
  - CLAUDE.md : SPECIAL — smart merge: take download as base, re-apply 2 session edits

Also takes a backup of every file being REPLACED into Final_Deliverables/_merge_backup/.
"""
import os, sys, csv, shutil, time, re
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT  = Path(r"C:\Users\ionva\Desktop\Sustainable Finance Project")
DOWNLOAD = Path(r"C:\stg-susfin\SusFin-main")
MANIFEST = PROJECT / "Final_Deliverables" / "_merge_manifest.csv"
BACKUP   = PROJECT / "Final_Deliverables" / "_merge_backup"
LOG_PATH = PROJECT / "Final_Deliverables" / "_merge_execution_log.txt"

BACKUP.mkdir(parents=True, exist_ok=True)

log_lines = []
def log(msg):
    print(msg)
    log_lines.append(msg)

# ── Smart-merge CLAUDE.md ─────────────────────────────────────────────────────
def smart_merge_claudemd():
    """Take download's CLAUDE.md as base, re-apply our 2 session edits."""
    local_md    = PROJECT / "CLAUDE.md"
    download_md = DOWNLOAD / "CLAUDE.md"
    if not download_md.exists():
        log("  CLAUDE.md: download version missing — keeping local untouched")
        return False

    # backup local first
    (BACKUP / "CLAUDE.md").write_text(local_md.read_text(encoding="utf-8"), encoding="utf-8")

    download_text = download_md.read_text(encoding="utf-8")

    # Edit 1: insert the 04b row after the 04 row in the notebooks table
    nb04b_row = (
        "| `notebooks/04b_fundamental_quality.ipynb` | Agent 10b — Fundamental Quality (Screen B) | "
        "6-metric framework (M-01 ROIC–WACC, M-02 FCF Conversion, M-03 FCCR + Net Debt/EBITDA, M-04 Sloan, "
        "M-05 EBITDA CV, M-06 DSI) + Layer-1 dividend-cut pre-screen. See `docs/financial_filtering_framework/` |\n"
    )
    # Re-apply Edit 1: only if the row isn't already there AND the 04 row exists
    if "04b_fundamental_quality.ipynb" not in download_text:
        # find the line for notebooks/04_financial_analysis.ipynb and insert after
        pattern = re.compile(r"(\|\s*`notebooks/04_financial_analysis\.ipynb`[^\n]*\n)")
        m = pattern.search(download_text)
        if m:
            insert_at = m.end()
            download_text = download_text[:insert_at] + nb04b_row + download_text[insert_at:]
            log("  CLAUDE.md edit 1 (04b row): re-applied")
        else:
            log("  CLAUDE.md edit 1 (04b row): SKIPPED — anchor row not found in download version")

    # Edit 2: ensure the Reference documents section exists. If not, append it.
    ref_block = (
        "\n**Reference documents:**\n"
        "- `docs/financial_filtering_framework/` — source documents for the 6-metric Screen B "
        "(Version 2 HTML + design rationale PDFs)\n"
        "- `Final_Deliverables/` — generated docx reports + builder scripts "
        "(data-driven; re-run `build_final_report.py` to refresh)\n"
    )
    if "docs/financial_filtering_framework/" not in download_text:
        # try to append after the existing "Output files land in:" section
        anchor = "**Output files land in:**"
        if anchor in download_text:
            # find end of that bulleted block
            idx = download_text.index(anchor)
            # next blank line or heading marks end of block
            tail = download_text[idx:]
            m = re.search(r"\n\n(?=##|\Z)", tail)
            insert_at = idx + (m.start() if m else len(tail))
            download_text = download_text[:insert_at] + ref_block + download_text[insert_at:]
            log("  CLAUDE.md edit 2 (reference docs): re-applied (appended after Output files)")
        else:
            download_text += ref_block
            log("  CLAUDE.md edit 2 (reference docs): re-applied (appended at end)")

    # Also normalise the "Normal usage" run order if it's missing 04b
    download_text = re.sub(
        r"(run notebooks in order \(01\s*→\s*02\s*→\s*03\s*→\s*04)\s*→\s*05",
        r"\1 → 04b → 05",
        download_text
    )

    local_md.write_text(download_text, encoding="utf-8")
    log("  CLAUDE.md: smart-merged and written")
    return True

# ── Read manifest and execute ─────────────────────────────────────────────────
with open(MANIFEST, "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

stats = {"ADD":0, "REPLACE":0, "IDENTICAL":0, "KEEP_LOCAL":0, "LOCAL_ONLY":0, "SKIP":0, "ERROR":0}
t0 = time.time()

for row in rows:
    rel = row["rel_path"].replace("\\", "/")
    action = row["action"]
    local_path = PROJECT / rel
    dl_path    = DOWNLOAD / rel

    if rel == "CLAUDE.md":
        # handled separately below
        stats["SKIP"] += 1
        continue

    if action in ("KEEP_LOCAL", "LOCAL_ONLY", "IDENTICAL"):
        stats[action] += 1
        continue

    try:
        if action == "ADD":
            local_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dl_path, local_path)
            stats["ADD"] += 1
        elif action == "REPLACE":
            # back up the file we're about to overwrite
            backup_target = BACKUP / rel
            backup_target.parent.mkdir(parents=True, exist_ok=True)
            if local_path.exists():
                shutil.copy2(local_path, backup_target)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dl_path, local_path)
            stats["REPLACE"] += 1
        else:
            stats["SKIP"] += 1
    except Exception as e:
        stats["ERROR"] += 1
        log(f"  ERROR on {rel}: {e}")

# Smart merge CLAUDE.md
log("\nSmart-merging CLAUDE.md...")
smart_merge_claudemd()

elapsed = time.time() - t0
log("")
log("="*70)
log("MERGE EXECUTION COMPLETE")
log("="*70)
for k in ("ADD","REPLACE","IDENTICAL","KEEP_LOCAL","LOCAL_ONLY","SKIP","ERROR"):
    log(f"  {k:12s}  {stats[k]}")
log(f"\nElapsed: {elapsed:.1f}s")
log(f"Backups of replaced files: {BACKUP}")

LOG_PATH.write_text("\n".join(log_lines), encoding="utf-8")
print(f"\nLog: {LOG_PATH}")
