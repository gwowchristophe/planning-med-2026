import streamlit as st
import pandas as pd
import os, calendar, random, io
from datetime import date, datetime, timedelta
import holidays

# --- CONFIGURATION ---
st.set_page_config(page_title="Planning 2026", layout="wide")
VALS = {"GW": 24, "GM": 24, "JK": 9, "JM": 7}
DB_F, OFF_F = "users_db.csv", "desiderata_db.csv"
BE_H = holidays.BE(years=2026)

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

def gd(f):
    if os.path.exists(f): return pd.read_csv(f)
    return pd.DataFrame()

def sd(df, f):
    df.to_csv(f, index=False)

def check_rules(n, d, p, pl, vo):
    ds = d.strftime("%Y-%m-%d")
    if ds in vo.get(n, []): return False
    v = d - timedelta(days=1)
    if v in pl and n in pl[v].values(): return False
    if n == "Daryush Valadi":
        if d.weekday() == 0 or p != "JM": return False
    if MEDS[n]["trio"] and p != "GW": return False
    if n == "PF Laterre" and p == "JK": return False
    if p == "JK" and not MEDS[n]["jk"]: return False
    return True

def get_ratio(name, stt):
    num = stt[name]
    den = MEDS[name]["etp"]
    return num / den

def generer_planning_global(vo):
    pl, stt = {}, {m: 0 for m in MEDS.keys()}
    sq = {m: {"S": 0, "D": 0, "F": 0} for m in MEDS.keys()}
    dates = []
    for m_idx in range(4, 9):
        last = calendar.monthrange(2026, m_idx)[1]
        for j in range(1, last + 1):
            dates.append(date(2026, m_idx, j))
    
    for d in dates:
        jp = {}
        # Tri décomposé pour éviter la coupure de ligne
        ml = list(MEDS.keys())
        ml.sort(key=lambda x: get_ratio(x, stt))
        
        f, s, dim = (d in BE_H), (d.weekday()==5), (d.weekday()==6)
        is_we = f or s or dim
        
        for p in ["GW", "GM", "JK", "JM"]:
            if is_we and p in ["JK", "JM"]: continue
            if not is_we and p == "JK" and d.weekday() == 3: continue
            try:
                c = next(m for m in ml if m not in jp.values() and check_rules(m, d, p, pl, vo))
                jp[p] = c
                stt[c] += VALS[p]
                if s: sq[c]["S"] += 1
                if dim: sq[c]["D"] += 1
                if f: sq[c]["F"] += 1
            except StopIteration: return None, None, None
        pl[d] = jp
    return pl, stt, sq

# --- INTERFACE ---
if 'user' not in st.session_state:
    st.title("🏥 Planning 2026")
    u_df = gd(DB_F)
    if u_df.empty:
        df_init = pd.DataFrame({"Medecin": list(MEDS.keys()), "MDP": ["Doudoudragon"]*13})
        sd(df_init, DB_F)
        st.rerun()
    u_sel = st.selectbox("Nom", list(MEDS.keys()))
    pw = st.text_input("Code", type="password")
    if st.button("OK"):
        v_pw = u_df.loc[u_df["Medecin"]==u_sel, "MDP"].values[0]
        if pw == v_pw:
            st.session_state.user = u_sel
            st.rerun()
        else: st.error("Erreur")
else:
    st.sidebar.title(st.session_state.user)
    m = ["📅 OFF", "🔐 Code", "Sortie"]
    if st.session_state.user == "Christophe Angelo":
        m.insert(1, "🚀 Générateur")
    sel = st.sidebar.radio("Menu", m)
    nms = {4:"Avril", 5:"Mai", 6:"Juin", 7:"Juillet", 8:"Août"}
