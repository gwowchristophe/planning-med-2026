import streamlit as st
import pandas as pd
import os, calendar, random, io
from datetime import date, datetime, timedelta
import holidays

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

def check(n, d, p, pl, vo):
    if d.strftime("%Y-%m-%d") in vo.get(n, []): return False
    v = d - timedelta(days=1)
    if v in pl and n in pl[v].values(): return False
    if n == "Daryush Valadi" and (d.weekday() == 0 or p != "JM"): return False
    if MEDS[n]["trio"] and p != "GW": return False
    if n == "PF Laterre" and p == "JK": return False
    if p == "JK" and not MEDS[n]["jk"]: return False
    return True

if 'user' not in st.session_state:
    st.title("🏥 Accès Planning 2026")
    u_df = gd(DB_F)
    if not os.path.exists(DB_F):
        pd.DataFrame({"Medecin": list(MEDS.keys()), "MDP": ["Doudoudragon"]*13}).to_csv(DB_F, index=False)
        st.rerun()
    u_sel = st.selectbox("Nom", list(MEDS.keys()))
    pw = st.text_input("Code", type="password")
    if st.button("OK"):
        if pw == u_df.loc[u_df["Medecin"]==u_sel, "MDP"].values[0]:
            st.session_state.user = u_sel
            st.rerun()
else:
    st.sidebar.title(st.session_state.user)
    m = ["📅 Mes OFF", "🚀 Générateur Global", "🔐 Code", "Sortie"]
    if st.session_state.user != "Christophe Angelo": m.remove("🚀 Générateur Global")
    sel = st.sidebar.radio("Menu", m)
    
    nms = {4:"Avril", 5:"Mai", 6:"Juin", 7:"Juillet", 8:"Août"}
    fr_days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

    if sel == "📅 Mes OFF":
        mo = st.selectbox("Mois pour encoder", [4,5,6,7,8], format_func=lambda x: nms[x])
        df = gd(OFF_F)
        co = set(df[df["Medecin"]==st.session_state.user]["Date_OFF"].tolist())
        cl = calendar.monthcalendar(2026, mo)
        for s in cl:
            cols = st.columns(7)
            for i, j in enumerate(s):
                if j != 0:
                    ds = f"2026-{mo:02d}-{j:02d}"
                    t = f"{j} {'❌' if ds in co else '✅'}"
                    if cols[i].button(t, key=ds):
                        if ds in co: df = df[~((df["Medecin"]==st.session_state.user)&(df["Date_OFF"]==ds))]
                        else: df = pd.concat([df, pd.DataFrame([{"Medecin":st.session_state.user, "Date_OFF":ds}])])
                        sd(df, OFF_F); st.rerun()

    elif sel == "🚀 Générateur Global":
        st.header("Génération Equilibrée (Avril - Août 2026)")
        if st.button("Lancer la simulation complète"):
            vo = gd(OFF_F).groupby("Medecin")["Date_OFF"].apply(list).to_dict()
            pl, stt = {}, {m: 0 for m in MEDS.keys()}
            # Nouveaux compteurs pour l'équité qualitative
            stats_qual = {m: {"Sam": 0, "Dim": 0, "Ferie": 0} for m in MEDS.keys()}
            
            ds = []
            for m_idx in range(4, 9):
                last_j = calendar.monthrange(2026, m_idx)[1]
                for j_idx in range(1, last_j + 1):
                    ds.append(date(2026, m_idx, j_idx))
            
            ok = True
            for d in ds:
                jp = {}
                ml = sorted(list(MEDS.keys()), key=lambda x: stt[x] / MEDS[x]["etp"])
                is_ferie = d in BE_HOLIDAYS
                is_sam = d.weekday() == 5
                is_dim = d.weekday() == 6
                
                for p in ["GW", "GM", "JK", "JM"]:
                    is_off_day = (is_sam or is_dim or is_ferie)
                    if is_off_day and p in ["JK", "JM"]: continue
                    if not is_off_day and p == "JK" and d.weekday() == 3: continue 
                    
                    try:
                        c = next(m for m in ml if m not in jp.values() and check(m, d, p, pl, vo))
                        jp[p], stt[c] = c, stt[c] + VALS[p]
                        # Mise à jour des compteurs qualitatifs
                        if is
