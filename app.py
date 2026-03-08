import streamlit as st
import pandas as pd
import os, calendar, random, io
from datetime import date, datetime, timedelta
import holidays

# --- CONFIGURATION & DATA ---
st.set_page_config(page_title="Planning Expert 2026", layout="wide")
VALS = {"GW": 24, "GM": 24, "JK": 9, "JM": 7}
DB_F, OFF_F = "users_db.csv", "desiderata_db.csv"
BE_HOLIDAYS = holidays.BE(years=2026)

MEDS = {
    "Alexandra Warnant": {"etp": 0.8, "jk": 1, "trio": 0},
    "Alfredo Vieira": {"etp": 0.8, "jk": 1, "trio": 0},
    "Camie Dupuis": {"etp": 0.8, "jk": 1, "trio": 0},
    "Christian Davin": {"etp": 0.8, "jk": 0, "trio": 1},
    "Christophe Angelo": {"etp": 0.6, "jk": 1, "trio": 0},
    "Daryush Valadi": {"etp": 0.4, "jk": 0, "trio": 0},
    "Elisa Mastrodiscasa": {"etp": 0.8, "jk": 0, "trio": 1},
    "Gauthier Nendumba": {"etp": 0.8, "jk": 1, "trio": 0},
    "Julie Henrie": {"etp": 0.6, "jk": 1, "trio": 0},
    "Martin Hachez": {"etp": 0.8, "jk": 1, "trio": 0},
    "PF Laterre": {"etp": 0.8, "jk": 0, "trio": 0},
    "Raouf Sheta": {"etp": 0.8, "jk": 0, "trio": 1},
    "Simon Van Migem": {"etp": 0.8, "jk": 1, "trio": 0}
}

def gd(f): return pd.read_csv(f) if os.path.exists(f) else pd.DataFrame()
def sd(df, f): df.to_csv(f, index=False)

def check_rules(n, d, p, pl, vo):
    if d.strftime("%Y-%m-%d") in vo.get(n, []): return False
    v = d - timedelta(days=1)
    if v in pl and n in pl[v].values(): return False
    if n == "Daryush Valadi" and (d.weekday() == 0 or p != "JM"): return False
    if MEDS[n]["trio"] and p != "GW": return False
    if n == "PF Laterre" and p == "JK": return False
    if p == "JK" and not MEDS[n]["jk"]: return False
    return True

# --- MOTEUR DE GÉNÉRATION ---
def generer_planning_global(vo):
    pl, stt = {}, {m: 0 for m in MEDS.keys()}
    sq = {m: {"Sam": 0, "Dim": 0, "Ferie": 0} for m in MEDS.keys()}
    dates = []
    for m_idx in range(4, 9):
        last = calendar.monthrange(2026, m_idx)[1]
        for j in range(1, last + 1): dates.append(date(2026, m_idx, j))
    
    for d in dates:
        jp = {}
        ml = sorted(list(MEDS.keys()), key=lambda x: stt[x
