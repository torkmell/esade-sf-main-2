"""Execute the archive routing per _archive_routing_manifest.csv.

Copy every file from C:\\stg-archive\\SusFin_Archive\\... into
data/rag/reports/{COMPANY}/{company_reports|external_evidence}/<file>

PDFs are .gitignored by default — these stay local, not pushed to GitHub.
"""
import os, sys, csv, shutil, time
sys.stdout.reconfigure(encoding="utf-8")

PROJECT      = r"C:\Users\ionva\Desktop\Sustainable Finance Project"
STAGING_ROOT = r"C:\stg-archive\SusFin_Archive"
MANIFEST     = os.path.join(PROJECT, "Final_Deliverables", "_archive_routing_manifest.csv")
LOG_PATH     = os.path.join(PROJECT, "Final_Deliverables", "_archive_routing_log.txt")

log_lines = []
def log(msg):
    print(msg); log_lines.append(msg)

with open(MANIFEST, "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

log(f"Routing {len(rows)} files...")
t0 = time.time()
stats = {"copied": 0, "skipped": 0, "errors": 0}

for row in rows:
    archive_folder = row["archive_folder"]
    project_folder = row["project_folder"]
    filename       = row["filename"]
    classification = row["classification"]
    if project_folder.startswith("_UNMAPPED"):
        log(f"  SKIP (unmapped): {filename}")
        stats["skipped"] += 1
        continue
    src = os.path.join(STAGING_ROOT, archive_folder, filename)
    dst_folder = os.path.join(PROJECT, "data", "rag", "reports", project_folder, classification)
    dst = os.path.join(dst_folder, filename)
    if not os.path.exists(src):
        log(f"  ERROR (src missing): {src}")
        stats["errors"] += 1
        continue
    try:
        os.makedirs(dst_folder, exist_ok=True)
        shutil.copy2(src, dst)
        stats["copied"] += 1
        if stats["copied"] % 20 == 0:
            log(f"  [{stats['copied']}/{len(rows)}] copied")
    except Exception as e:
        log(f"  ERROR copying {filename}: {e}")
        stats["errors"] += 1

log("")
log("="*60)
log("ROUTING COMPLETE")
log("="*60)
log(f"  Copied:  {stats['copied']}")
log(f"  Skipped: {stats['skipped']}")
log(f"  Errors:  {stats['errors']}")
log(f"  Elapsed: {time.time()-t0:.1f}s")

# Final size summary per company
log("")
log("Files placed per company folder:")
from collections import Counter
per_company = Counter()
for row in rows:
    if row["project_folder"].startswith("_UNMAPPED"): continue
    per_company[row["project_folder"]] += 1
for pf, n in sorted(per_company.items()):
    log(f"  {pf:50s}  {n} file(s)")

with open(LOG_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines))
print(f"\nLog: {LOG_PATH}")
