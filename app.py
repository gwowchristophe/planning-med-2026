import streamlit as st
import pandas as pd
import os, calendar, random
from datetime import date, datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Planning Médical 2026", layout="wide")
VALEURS = {"GW": 24, "GM": 24, "JK": 9, "JM": 7}
DB_FILE, OFF_FILE = "users_db.csv", "desiderata_db.csv"

# Configuration complète des profils
MEDS = {
    "Alexandra Warnant": {"etp": 0.8, "jk": True, "trio": False},
    "Alfredo Vieira": {"etp": 0.8, "jk": True, "trio": False},
    "Camie Dupuis": {"etp": 0.8, "jk": True, "trio": False},
    "Christian Davin": {"etp": 0.8, "jk": False, "trio": True},
    "Christophe Angelo": {"etp": 0.6, "jk": True, "trio": False},
    "Daryush Valadi": {"etp": 0.4, "jk": False, "trio": False},
    "Elisa Mastrodiscasa": {"etp": 0.8, "jk": False, "trio": True},
    "Gauthier Nendumba": {"etp": 0.8, "jk": True, "trio": False},
    "Julie Henrie": {"etp": 0.6, "jk": True, "trio": False},
    "Martin Hachez": {"etp": 0.8, "jk": True, "trio": False},
    "PF Laterre": {"etp": 0.8, "jk": False, "trio": False},
    "Raouf Sheta": {"etp": 0.8, "jk": False, "trio": True},
    "Simon Van Migem": {"etp": 0.8, "jk": True, "trio": False}
}

def get_data(f): return pd.read_csv(f) if os.path.exists(f) else pd.DataFrame()
def save_data(df, f): df.to_csv(f, index=False)

# Initialisation
if not os.path.exists(DB_FILE):
    pd.DataFrame({"Medecin": list(MEDS.keys()), "MDP": ["Doudoudragon"]*13}).to_csv(DB_FILE, index=False)
if not os.path.exists(OFF_FILE):
    pd.DataFrame(columns=["Medecin", "Date_OFF"]).to_csv(OFF_FILE, index=False)

def generate_ics(name, planning):
    ics = ["BEGIN:VCALENDAR", "VERSION:2.0"]
    for d, p in planning.items():
        for pc, pn in p.items():
            if pn == name:
                ics += ["BEGIN:VEVENT", f"SUMMARY:Poste {pc}", f"DTSTART;VALUE=DATE:{d.strftime('%Y%m%d')}", "END:VEVENT"]
    ics.append("END:VCALENDAR")
    return "\n".join(ics)

def est_valide(nom, d, p, plan, v_off):
    if d.strftime("%Y-%m-%d") in v_off.get(nom, []): return False
    veille = d - timedelta(days=1)
    if veille in plan and nom in plan[veille].values(): return False
    if nom == "Daryush Valadi" and (d.weekday() == 0 or p != "JM"): return False
    if MEDS[nom]["trio"] and p != "GW": return False
    if nom == "PF Laterre" and p == "JK": return False
    if p == "JK" and not MEDS[nom]["jk"]: return False
    return True

# --- INTERFACE ---
if 'user' not in st.session_state:
    st.title("🏥 Accès Planning 2026")
    u_df = get_data(DB_FILE)
    user_sel = st.selectbox("Nom", list(MEDS.keys()))
    pwd_in = st.text_input("Code", type="password")
    if st.button("Connexion"):
        if not u_df.empty and pwd_in == u_df.loc[u_df["Medecin"]==user_sel, "MDP"].values[0]:
            st.session_state.user = user_sel
            st.rerun()
        else: st.error("Erreur code.")
else:
    st.sidebar.title(f"Dr {st.session_state.user}")
    menu = ["📅 OFF", "🔐 Sécurité", "Sortie"]
    if st.session_state.user == "Christophe Angelo": menu.insert(1, "🚀 Générateur")
    mode = st.sidebar.radio("Menu", menu)

    if mode == "📅 OFF":
        st.header("Gestion de vos indisponibilités")
        # Sélecteur de mois avec noms écrits
        m_sel = st.selectbox("Choisir le mois :", [4, 5, 6, 7, 8], format_func=lambda x: calendar.month_name[x])
        all_off = get_data(OFF_FILE)
        curr_off = set(all_off[all_off["Medecin"]==st.session_state.user]["Date_OFF"].astype(str).tolist())
        cal = calendar.monthcalendar(2026, m_sel)
        for sem in cal:
            cols = st.columns(7)
            for i, j in enumerate(sem):
                if j != 0:
                    ds = f"2026-{m_sel:02d}-{j:02d}"
                    label = f"{j} {'❌' if ds in curr_off else '✅'}"
                    if cols[i].button(label, key=ds):
                        if ds in curr_off: all_off = all_off[~((all_off["Medecin"]==st.session_state.user)&(all_off["Date_OFF"]==ds))]
                        else: all_off = pd.concat([all_off, pd.DataFrame([{"Medecin":st.session_state.user, "Date_OFF":ds}])])
                        save_data(all_off, OFF_FILE); st.rerun()

    elif mode == "🚀 Générateur":
        st.header("Moteur de génération d'horaire")
        # REMPLACEMENT DU SLIDER PAR SELECTBOX ICI
        mois_gen = st.selectbox("Mois à générer :", [4, 5, 6, 7, 8], format_func=lambda x:
