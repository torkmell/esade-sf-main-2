#!/usr/bin/env python
"""Builds a page-marked evidence digest from each 8-Test work pack's
source_text.txt — surfaces candidate passages for the 8 greenwashing
dimensions so the assessment can quote real text with real page numbers.

Usage:  python scripts/_8test_digest.py <folderNN> <folderNN> ...
Output: outputs/rag/_evidence_digest.txt
"""
import glob, os, re, sys

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT)

DIM_KW = {
    "specificity":  r"net[\- ]?zero|carbon[\- ]?neutral|climate[\- ]?neutral|fossil[\- ]?free|decarbonis|carbon negative",
    "metric":       r"\d+(\.\d+)?\s?%|\d[\d,. ]*\s?(t|kt|mt)\s?co2|reduc\w* of \d|absolute (emiss|reduc)|emission intensity",
    "baseline":     r"baseline|base year|base-year|from (a )?20\d\d|versus 20\d\d|vs\.? ?20\d\d|compared (to|with) 20\d\d|20\d\d base",
    "target":       r"sbti|science[\- ]based target|validated by|approved by the science|near[\- ]term target|business ambition|1\.5\s?.?c|well[\- ]below 2",
    "time_horizon": r"by 20[2-5]\d|target year|2030|2040|2050",
    "scope":        r"scope [123]\b|scope1|scope2|scope3|scopes 1|value chain emiss|upstream emiss|downstream emiss",
    "verification": r"assur\w*|verif\w*|isae|independent (audit|practitioner|review|limited)|limited assurance|reasonable assurance|audited by|third[\- ]party",
    "consistency":  r"capex|capital expenditure|green (capex|invest)|lobby\w*|trade association|transition plan|capital allocation",
}
MAX_HITS, MAXLEN = 6, 200

def digest(src):
    cur = "?"
    hits = {d: [] for d in DIM_KW}
    seen = {d: set() for d in DIM_KW}
    with open(src, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"\[page (\d+)\]", line)
            if m:
                cur = m.group(1)
                continue
            ls = " ".join(line.split())
            if len(ls) < 25:
                continue
            low = ls.lower()
            for d, kw in DIM_KW.items():
                if len(hits[d]) >= MAX_HITS:
                    continue
                if re.search(kw, low):
                    k = ls[:55].lower()
                    if k in seen[d]:
                        continue
                    seen[d].add(k)
                    hits[d].append((cur, ls[:MAXLEN]))
    return hits

folders_arg = sys.argv[1:] or ["03", "06", "17", "23", "26", "27", "28", "32"]
out = []
for fn in folders_arg:
    fol = glob.glob(f"data/rag/corpus/{fn}_*")
    if not fol:
        continue
    src = f"{fol[0]}/_8test/source_text.txt"
    if not os.path.exists(src):
        continue
    header = open(src, encoding="utf-8").readline().strip()
    src2   = open(src, encoding="utf-8").readlines()[1].strip()
    h = digest(src)
    out.append("\n" + "=" * 78)
    out.append(f"{header}   |   {src2}")
    out.append("=" * 78)
    for d in DIM_KW:
        out.append(f"\n## {d}")
        if h[d]:
            for pg, txt in h[d]:
                out.append(f"  [p{pg}] {txt}")
        else:
            out.append("  (no keyword hits — likely MISSING)")

txt = "\n".join(out)
with open("outputs/rag/_evidence_digest.txt", "w", encoding="utf-8") as f:
    f.write(txt)
print(f"Evidence digest written: outputs/rag/_evidence_digest.txt  ({len(txt):,} chars, {len(folders_arg)} companies)")
