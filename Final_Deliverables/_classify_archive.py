"""Build the routing manifest for SusFin_Archive files.

For every file in C:\\stg-archive\\SusFin_Archive\\NN_Company_Name\\:
  1. Map NN_Company_Name → existing project folder TICKER_Company_Name
     (matched by normalised company-name suffix)
  2. Classify file as 'company_report' or 'external_evidence' by filename pattern
  3. Build target path: data/rag/reports/TICKER_Company_Name/{company_reports|external_evidence}/<file>

Output: Final_Deliverables/_archive_routing_manifest.csv
"""
import os, sys, re, csv
sys.stdout.reconfigure(encoding="utf-8")

PROJECT      = r"C:\Users\ionva\Desktop\Sustainable Finance Project"
STAGING_ROOT = r"C:\stg-archive\SusFin_Archive"
RAG_DIR      = os.path.join(PROJECT, "data", "rag", "reports")
MANIFEST     = os.path.join(PROJECT, "Final_Deliverables", "_archive_routing_manifest.csv")

# ── 1. Load existing folder map: normalised name → folder path ────────────────
def normalise(name: str) -> str:
    """Strip leading prefix token + optional class letter, then drop legal-form suffixes.

    Pattern is always PREFIX_COMPANY_NAME, with optional PREFIX_B_COMPANY_NAME for
    Swedish class-B shares (ADDT_B, SWEC_B, TEL2_B). We only strip 1–2 leading tokens,
    never more — otherwise short company-name acronyms (AIB, ABB, EON, UCB) get eaten.
    """
    parts = name.split("_")
    if not parts: return ""
    parts = parts[1:]   # always strip the very first token (numeric or ticker)
    # Optionally strip a single-letter class indicator like "B"
    if parts and parts[0].isalpha() and len(parts[0]) == 1:
        parts = parts[1:]
    n = " ".join(parts).lower()
    n = re.sub(r"[_\-]+", " ", n)
    n = re.sub(r"\bclass\s+[a-z]\b", "", n)
    n = re.sub(r"\b(plc|llc|ltd|ag|sa|nv|se|sas|sl|spa|oyj|abp|holding|holdings|group|the|international|inc|company)\b", "", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n

existing_folders = sorted(os.listdir(RAG_DIR))
existing_map = {}
for folder in existing_folders:
    if not os.path.isdir(os.path.join(RAG_DIR, folder)):
        continue
    key = normalise(folder)
    existing_map[key] = folder

# manual aliases for tricky names (archive name normalised → project folder)
ALIAS = {
    "industria de diseno textil": "ITX_Inditex_SA",
    "lloyds banking":              "LLOY_Lloyds_Banking_Group_PLC",
    "natwest":                     "NWG_NatWest_Group_PLC",
    "raiffeisen bank international":"RBI_Raiffeisen_Bank_International_AG",
    "loreal":                      "OR_LOreal_SA",
    "schneider electric":          "SU_Schneider_Electric_SE",
    "klepierre":                   "LI_Klepierre_SA",
    "merlin properties socimi":    "MRL_MERLIN_Properties_SOCIMI_SA",
    "tele2 b":                      "TEL2_B_Tele2_AB_Class_B",
    "sweco b":                      "SWEC_B_Sweco_AB_Class_B",
}

def find_project_folder(archive_folder: str):
    """Map archive folder name to existing project folder, returning (folder_name, status)."""
    arch_key = normalise(archive_folder)
    if arch_key in ALIAS:
        return ALIAS[arch_key], "ALIAS"
    if arch_key in existing_map:
        return existing_map[arch_key], "EXACT"
    # try partial: substring containment
    candidates = [v for k, v in existing_map.items() if arch_key and (arch_key in k or k in arch_key)]
    if len(candidates) == 1:
        return candidates[0], "PARTIAL"
    if len(candidates) > 1:
        return candidates[0], f"AMBIG ({len(candidates)})"
    return None, "NO_MATCH"

# ── 2. Classification rules ──────────────────────────────────────────────────
EXTERNAL_PATTERNS = [
    r"\bspo\b",
    r"second[\s\-]party",
    r"indep(endent)?[\s_\-]*auditor",
    r"limit(ed)?[\s_\-]*assur",
    r"third[\s_\-]?party",
    r"ngo[\s_\-]",
    r"clientearth",
    r"reclaim[\s_\-]?finance",
    r"sbti[\s_\-]?report",
    r"transition[\s_\-]?pathway",
    r"carbon[\s_\-]?tracker",
    r"ghani",            # AIXTRON case — Ghani Solar Power Project is third-party
    r"mscI[\s_\-]?rating",
    r"sustainalytics[\s_\-]?rating",
    r"iss[\s_\-]?rating",
]

def classify(filename: str) -> str:
    n = filename.lower()
    for pat in EXTERNAL_PATTERNS:
        if re.search(pat, n):
            return "external_evidence"
    return "company_reports"

# ── 3. Walk staging and build manifest ───────────────────────────────────────
rows = []
unmapped_summary = {}

for folder in sorted(os.listdir(STAGING_ROOT)):
    folder_path = os.path.join(STAGING_ROOT, folder)
    if not os.path.isdir(folder_path):
        continue
    project_folder, status = find_project_folder(folder)
    files = [f for f in sorted(os.listdir(folder_path))
             if os.path.isfile(os.path.join(folder_path, f))
             and not f.startswith(".")
             and not f.startswith("~$")]
    if status == "NO_MATCH":
        unmapped_summary[folder] = len(files)
        # still create row entries for review
    for f in files:
        target_folder  = project_folder if project_folder else f"_UNMAPPED/{folder}"
        classification = classify(f)
        rel_target     = f"data/rag/reports/{target_folder}/{classification}/{f}"
        src_full       = os.path.join(folder_path, f)
        size_mb        = os.path.getsize(src_full) / (1024*1024)
        rows.append({
            "archive_folder":   folder,
            "project_folder":   target_folder,
            "match_status":     status,
            "filename":         f,
            "classification":   classification,
            "target_path":       rel_target,
            "size_mb":          round(size_mb, 2),
        })

# ── 4. Write manifest ────────────────────────────────────────────────────────
with open(MANIFEST, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["archive_folder","project_folder","match_status",
                                      "filename","classification","target_path","size_mb"])
    w.writeheader()
    w.writerows(rows)

# ── 5. Summary printout ──────────────────────────────────────────────────────
print(f"Manifest written: {MANIFEST}")
print(f"Total rows: {len(rows)}\n")

# Mapping status breakdown
from collections import Counter
status_counts = Counter(r["match_status"] for r in rows)
print("Folder-match status (per file):")
for k, v in status_counts.most_common():
    print(f"  {k:10s}  {v}")
print()

# Classification breakdown
class_counts = Counter(r["classification"] for r in rows)
print("Classification (per file):")
for k, v in class_counts.most_common():
    print(f"  {k:18s}  {v}")
print()

# Show every EXTERNAL file (small set, worth reviewing)
externals = [r for r in rows if r["classification"] == "external_evidence"]
print(f"=== EXTERNAL_EVIDENCE files ({len(externals)}) ===")
for r in externals:
    print(f"  [{r['archive_folder']}] → [{r['project_folder']}]  ::  {r['filename']}")
print()

# Show unmapped folders (need user decision)
if unmapped_summary:
    print("=== UNMAPPED archive folders (no matching project folder) ===")
    for folder, n in unmapped_summary.items():
        print(f"  {folder}  ({n} files)")
    print()
else:
    print("All 40 archive folders mapped successfully.")

# Show summary per company: folder → file count + mapped name
print("\nPer-folder summary:")
by_folder = {}
for r in rows:
    by_folder.setdefault(r["archive_folder"], []).append(r)
for folder in sorted(by_folder.keys()):
    items = by_folder[folder]
    proj   = items[0]["project_folder"]
    status = items[0]["match_status"]
    n_ext  = sum(1 for x in items if x["classification"]=="external_evidence")
    n_com  = len(items) - n_ext
    flag = "  " if status in ("EXACT","PARTIAL","ALIAS") else "⚠ "
    print(f"  {flag}{folder:48s}  →  {proj:48s}  [{status:7s}]  com:{n_com:2d}  ext:{n_ext}")
