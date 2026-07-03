#!/usr/bin/env python3
"""
Pulls data from Google Sheets (public CSV) and writes data.json
Run by GitHub Actions monthly or manually.
"""
import csv, json, io, urllib.request, sys
from datetime import date

SHEET_ID = "1Fb8xAp-ofFU6mCZBnck-njeqwu4mYzIC39Bec8UO_3M"
GID      = "1803638887"
CSV_URL  = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

# Row indices (0-based) for each metric
ROWS = {
    "s_responses":      60,   # 100Staff отклики факт
    "s_leads_fact":     54,   # 100Staff лиды факт
    "s_qual_fact":      46,   # 100Staff квал лиды факт (переговоры)
    "s_sales_new":      38,   # 100Staff продажи из новых лидов
    "s_sales_old":      39,   # 100Staff продажи из старых лидов
    "s_margin":         40,   # 100Staff прибыль
    "s_revenue":        41,   # 100Staff выручка
    "s_budget":         94,   # 100Staff бюджет (расход Люба)
    "g_responses":      86,   # PROStaff отклики факт
    "g_leads_fact":     80,   # PROStaff лиды факт
    "g_qual_fact":      72,   # PROStaff квал лиды факт (переговоры)
    "g_sales_new":      64,   # PROStaff продажи из новых лидов
    "g_sales_old":      65,   # PROStaff продажи из старых лидов
    "g_margin":         66,   # PROStaff прибыль
    "g_revenue":        67,   # PROStaff выручка
    "g_budget":         95,   # PROStaff бюджет (расход Галя)
}

# Month column indices (Факт column for each month)
MONTH_COLS = {
    "apr": 132,
    "may": 177,
    "jun": 221,
    "jul": 265,
}

def safe_int(v):
    try: return int(str(v).replace(" ","").replace(",",""))
    except: return 0

def safe_float(v):
    try: return float(str(v).replace(" ","").replace(",","."))
    except: return 0.0

def fetch_rows():
    req = urllib.request.Request(CSV_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read().decode("utf-8")
    return list(csv.reader(io.StringIO(content)))

def get(rows, row_idx, col_idx):
    try: return rows[row_idx][col_idx].strip()
    except: return ""

def build_month(rows, m_col):
    s_leads    = safe_int(get(rows, ROWS["s_leads_fact"], m_col))
    s_qual     = safe_int(get(rows, ROWS["s_qual_fact"],  m_col))
    s_sales    = safe_int(get(rows, ROWS["s_sales_new"],  m_col)) + safe_int(get(rows, ROWS["s_sales_old"], m_col))
    s_resp     = safe_int(get(rows, ROWS["s_responses"],  m_col))
    s_margin   = safe_int(get(rows, ROWS["s_margin"],     m_col))
    s_revenue  = safe_int(get(rows, ROWS["s_revenue"],    m_col))
    s_budget   = safe_int(get(rows, ROWS["s_budget"],     m_col))
    s_cpl      = round(s_budget / s_leads, 1) if s_leads else 0

    g_leads    = safe_int(get(rows, ROWS["g_leads_fact"], m_col))
    g_qual     = safe_int(get(rows, ROWS["g_qual_fact"],  m_col))
    g_sales    = safe_int(get(rows, ROWS["g_sales_new"],  m_col)) + safe_int(get(rows, ROWS["g_sales_old"], m_col))
    g_resp     = safe_int(get(rows, ROWS["g_responses"],  m_col))
    g_margin   = safe_int(get(rows, ROWS["g_margin"],     m_col))
    g_revenue  = safe_int(get(rows, ROWS["g_revenue"],    m_col))
    g_budget   = safe_int(get(rows, ROWS["g_budget"],     m_col))
    g_cpl      = round(g_budget / g_leads, 1) if g_leads else 0

    return {
        "cpl": s_cpl, "responses": s_resp, "leads": s_leads,
        "qualLeads": s_qual, "sales": s_sales,
        "budget": s_budget, "returns": 0, "margin": s_margin, "marginEst": False,
        "proResponses": g_resp, "proLeads": g_leads, "proQualLeads": g_qual,
        "proSales": g_sales, "proBudget": g_budget, "proCPL": g_cpl,
    }

def main():
    print("Fetching Google Sheets data...")
    rows = fetch_rows()
    print(f"Got {len(rows)} rows, {max(len(r) for r in rows)} cols")

    out = {"updated": str(date.today()), "source": "Google Sheets"}
    for month, col in MONTH_COLS.items():
        out[month] = build_month(rows, col)
        s, g = out[month]["leads"], out[month]["proLeads"]
        print(f"  {month}: 100Staff leads={s}, PROStaff leads={g}")

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("data.json written OK")

if __name__ == "__main__":
    main()
