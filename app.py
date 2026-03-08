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

# Fonctions utilitaires
def gd(f):
    return pd.read_csv(f) if os.path.exists(f) else pd.DataFrame()

def sd(df, f):
    df.to_csv(f, index=False)

def check_rules(n, d, p, pl, vo):
    ds = d.strftime("%Y-%m-%d")
    if ds in vo.get(n, []): return False
    v = d - timedelta(days=1)
    if v in pl and n in pl[v].values(): return False
    if n == "Daryush Valadi" and (d.weekday() == 0 or p != "JM"): return False
    if MEDS[n]["trio"] and p != "GW": return False
    if n == "PF Laterre" and p == "JK": return False
    if p == "JK" and not MEDS[n]["jk"]: return False
    return True

# --- INTERFACE DE CONNEXION ---
if 'user' not in st.session_state:
    st.title("🏥 Connexion Planning")
    if not os.path.exists(DB_F):
        df_init = pd.DataFrame({"Medecin": list(MEDS.keys()), "MDP": ["Doudoudragon"]*13})
        sd(df_init, DB_F)
    
    u_df = gd(DB_F)
    u_sel = st.selectbox("Nom", list(MEDS.keys()))
    pw = st.text_input("Code", type="password")
    if st.button("Se connecter"):
        v_pw = str(u_df.loc[u_df["Medecin"]==u_sel, "MDP"].values[0])
        if pw == v_pw:
            st.session_state.user = u_sel
            st.rerun()
        else: st.error("Code incorrect")

# --- CONTENU PRINCIPAL ---
else:
    # Menu Sidebar
    m_list = ["📅 OFF", "🔐 Code", "Sortie"]
    if st.session_state.user == "Christophe Angelo":
        m_list.insert(1, "🚀 Générateur")
    
    sel = st.sidebar.radio("Menu", m_list)
    st.sidebar.write(f"Connecté : **{st.session_state.user}**")

    # 1. GESTION DES OFF
    if sel == "📅 OFF":
        st.header("Mes indisponibilités")
        nms = {4:"Avril", 5:"Mai", 6:"Juin", 7:"Juillet", 8:"Août"}
        mo = st.selectbox("Mois", [4,5,6,7,8], format_func=lambda x: nms[x])
        
        df_off = gd(OFF_F)
        user_off = set(df_off[df_off["Medecin"]==st.session_state.user]["Date_OFF"].tolist())
        
        cl = calendar.monthcalendar(2026, mo)
        for s in cl:
            cols = st.columns(7)
            for i, j in enumerate(s):
                if j != 0:
                    ds = f"2026-{mo:02d}-{j:02d}"
                    txt = f"{j} {'❌' if ds in user_off else '✅'}"
                    if cols[i].button(txt, key=ds):
                        if ds in user_off:
                            df_off = df_off[~((df_off["Medecin"]==st.session_state.user)&(df_off["Date_OFF"]==ds))]
                        else:
                            new_row = pd.DataFrame([{"Medecin":st.session_state.user, "Date_OFF":ds}])
                            df_off = pd.concat([df_off, new_row])
                        sd(df_off, OFF_F)
                        st.rerun()

    # 2. GÉNÉRATEUR (Uniquement pour Christophe)
    elif sel == "🚀 Générateur":
        st.header("Générateur Global (5 mois)")
        if st.button("Lancer la simulation"):
            vo = gd(OFF_F).groupby("Medecin")["Date_OFF"].apply(list).to_dict()
            pl, stt = {}, {m: 0 for m in MEDS.keys()}
            sq = {m: {"S": 0, "D": 0, "F": 0} for m in MEDS.keys()}
            
            # Création dates
            all_days = []
            for m_idx in range(4, 9):
                last = calendar.monthrange(2026, m_idx)[1]
                for j in range(1, last + 1): all_days.append(date(2026, m_idx, j))
            
            ok = True
            for d in all_days:
                jp = {}
                ml = list(MEDS.keys())
                ml.sort(key
