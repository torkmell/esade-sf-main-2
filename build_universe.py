import pandas as pd, re
from difflib import SequenceMatcher

STOXX_FILE = r'C:\Users\ionva\Desktop\Sustainable Finance Project\STOXX600_Outperformers_5Y_10Y_with_tickers.xlsx'
CSV_FILE   = r'C:\Users\ionva\Desktop\Sustainable Finance Project\data\provided\equityBicsV2.csv'
OUT_FILE   = r'C:\Users\ionva\Desktop\Sustainable Finance Project\data\provided\universe_170.csv'

# Bloomberg exchange code → Yahoo Finance suffix
BB_TO_YF = {
    'BB': '.BR',  # Euronext Brussels
    'LN': '.L',   # London Stock Exchange
    'NA': '.AS',  # Euronext Amsterdam
    'SW': '.SW',  # SIX Swiss Exchange
    'FP': '.PA',  # Euronext Paris
    'IM': '.MI',  # Borsa Italiana
    'SM': '.MC',  # BME Madrid
    'SS': '.ST',  # Nasdaq Stockholm
    'GR': '.DE',  # Xetra (Germany)
    'FH': '.HE',  # Nasdaq Helsinki
    'DC': '.CO',  # Nasdaq Copenhagen
    'NO': '.OL',  # Oslo Bors
    'PW': '.WA',  # Warsaw Stock Exchange
    'AV': '.VI',  # Wiener Borse (Vienna)
    'ID': '.IR',  # Euronext Dublin
    'PL': '.LS',  # Euronext Lisbon
    'VX': '.SW',  # SIX Swiss (alt code)
}

def bb_to_yf_ticker(bb_ticker):
    """Convert Bloomberg ticker 'ARGX BB' to Yahoo Finance ticker 'ARGX.BR'."""
    if not bb_ticker or pd.isna(bb_ticker):
        return None
    parts = str(bb_ticker).strip().rsplit(' ', 1)
    if len(parts) != 2:
        return None
    local, exch = parts
    suffix = BB_TO_YF.get(exch)
    if not suffix:
        return None
    return local.replace(' ', '') + suffix

def normalize(s):
    s = str(s).lower().strip()
    s = s.replace('/', ' ')
    s = re.sub(r'([a-z])\.([a-z])\.?', r'\1\2', s)
    s = re.sub(r'[^\w\s]', '', s)
    s = re.sub(r'\b(nv|sa|spa|plc|ag|ab|asa|oyj|se|ltd|inc|group|holding|holdings|'
               r'class [ab]|aktiengesellschaft|abp|ruckversicherungs|gesellschaft|'
               r'spolka|akcyjna|polska|banca|banco|bank|banque|cantonale|'
               r'versicherungs|assurances|assicurazioni|financiere|financiero|'
               r'compagnie|generali|internationale)\b', '', s)
    return re.sub(r'\s+', ' ', s).strip()

# Load 170 outperformers from the new file (Constituents sheet)
df170 = pd.read_excel(STOXX_FILE, sheet_name='Constituents')
df170 = df170.dropna(subset=['Rank']).copy()
df170['Rank'] = df170['Rank'].astype(int)
df170 = df170.rename(columns={
    'Rank': 'rank', 'Company': 'company',
    '5Y TR (%)': 'return_5y_pct', '10Y TR (%)': 'return_10y_pct',
    'Bloomberg': 'bb_ticker'
})
df170['yf_ticker'] = df170['bb_ticker'].apply(bb_to_yf_ticker)

print(f"Loaded {len(df170)} companies from Constituents sheet")
missing_yf = df170[df170['yf_ticker'].isna()]
if len(missing_yf):
    print(f"No YF ticker for: {missing_yf[['rank','company','bb_ticker']].to_string(index=False)}")

# Load equityBicsV2 — one row per company for name matching
print('Loading equityBicsV2...')
df = pd.read_csv(CSV_FILE, low_memory=False)
df_co = df.drop_duplicates('idBbCompany').copy()
df_co['_norm'] = df_co['idBbGlobalCompanyName'].fillna('').apply(normalize)
norm_lookup = df_co.drop_duplicates('_norm').set_index('_norm')[['idBbCompany', 'idBbGlobalCompanyName']].to_dict('index')
all_norms = list(norm_lookup.keys())

# Manual overrides for companies whose names differ too much for automatic matching
MANUAL_IDS = {
    'Lion Finance Group PLC':                       60238741,  # Bank of Georgia Group PLC
    'UNIPOL ASSICURAZIONI SPA':                      128173,   # UnipolSai Assicurazioni SpA
    'Metso Corporation':                            8515484,   # Metso Outotec Oyj
    'PKO Bank Polski SA':                            201728,   # Powszechna Kasa Oszczednosci Bank Polski SA
    'FinecoBank SpA':                               9475473,   # FinecoBank Banca Fineco SpA
    'AL Sydbank A/S':                                120301,   # Sydbank AS
    'Munchener Ruckversicherungs-Gesellschaft AG':   117803,   # Muenchener Rueckversicherungs-Gesellschaft AG
    'Compagnie Financiere Richemont SA':             117896,   # Cie Financiere Richemont SA
    'KBC Ancora SCA':                               7282482,   # KBC Ancora
    'Buzzi Spa':                                     866731,   # Buzzi Unicem SpA
    'Helvetia Baloise Holding AG':                   191206,   # Helvetia Holding AG
    'ORLEN Spolka Akcyjna':                          823804,   # Polski Koncern Naftowy ORLEN SA
    'Heidelberg Materials AG':                       117596,   # HeidelbergCement AG
    'Julius Baer Gruppe AG':                       17149777,   # Julius Baer Group Ltd
    'Terna S.p.A.':                                1422581,   # Terna - Rete Elettrica Nazionale
    'Assicurazioni Generali S.p.A.':               115702,    # Assicurazioni Generali SpA (name normalizes to empty)
    'Siemens Aktiengesellschaft':                  115746,    # Siemens AG
    'NN Group N.V.':                               39780127,  # NN Group NV
    'Man Group PLC':                               63087888,  # Man Group PLC/Jersey
    # Hiab Oyj Class B: not yet in Bloomberg ESG dataset (recent Cargotec spin-off)
}

# Known duplicate ID fixes — both share same idBbCompany in professor's data
KNOWN_FIXES = {
    'Banca Generali S.p.A.': 1135757,   # was colliding with Assicurazioni Generali
}
KNOWN_NULLS = {
    'Erste Bank Polska S.A.',             # no separate Bloomberg entity
}

records = []
unmatched = []

for _, row in df170.iterrows():
    rank = row['rank']
    company = row['company']
    r5 = row['return_5y_pct']
    r10 = row['return_10y_pct']
    bb_ticker = row['bb_ticker']
    yf_t = row['yf_ticker']
    n = normalize(company)
    idc, matched_name = None, None

    # -1. Known null (no Bloomberg entity)
    if company in KNOWN_NULLS:
        idc, matched_name = None, None

    # 0. Known duplicate fix
    elif company in KNOWN_FIXES:
        idc = KNOWN_FIXES[company]
        matched_name = '[fix]'

    # 1. Manual override
    elif company in MANUAL_IDS:
        idc = MANUAL_IDS[company]
        matched_name = '[manual override]'

    # 2. Exact normalized name match
    elif n in norm_lookup:
        idc = norm_lookup[n]['idBbCompany']
        matched_name = norm_lookup[n]['idBbGlobalCompanyName']

    # 3. Fuzzy name match (ratio > 0.85, first-word guard)
    else:
        best_score, best_norm = 0, None
        for candidate in all_norms:
            if abs(len(n) - len(candidate)) > 8:
                continue
            score = SequenceMatcher(None, n, candidate).ratio()
            if score > best_score:
                best_score, best_norm = score, candidate
        first_word_match = (n.split()[0][:4] == best_norm.split()[0][:4]) if n and best_norm else False
        if best_score > 0.85 and first_word_match:
            idc = norm_lookup[best_norm]['idBbCompany']
            matched_name = norm_lookup[best_norm]['idBbGlobalCompanyName']

    records.append({
        'rank': rank, 'company': company,
        'return_5y_pct': r5, 'return_10y_pct': r10,
        'bb_ticker': bb_ticker, 'yf_ticker': yf_t,
        'idBbCompany': idc, 'matched_csv_name': matched_name
    })
    if not idc and company not in KNOWN_NULLS:
        unmatched.append((rank, company))

df_out = pd.DataFrame(records)
matched_count = int(df_out['idBbCompany'].notna().sum())
print(f'Matched: {matched_count}/170')
print(f'Unmatched ({len(unmatched)}):')
for r, c in unmatched:
    print(f'  Rank {r}: {c}')

# Verify no duplicate IDs
dups = df_out[df_out['idBbCompany'].notna()].groupby('idBbCompany')['company'].apply(list)
dups = dups[dups.apply(len) > 1]
if len(dups):
    print(f'\nWARNING: {len(dups)} duplicate Bloomberg IDs:')
    print(dups.to_string())
else:
    print('\nNo duplicate Bloomberg IDs.')

print()
print('--- Full verification table ---')
print(df_out[['rank', 'company', 'matched_csv_name', 'bb_ticker', 'yf_ticker']].to_string(index=False))

df_out.to_csv(OUT_FILE, index=False)
print(f'\nSaved to {OUT_FILE}')
