import streamlit as st
import pandas as pd
import os
import calendar
from datetime import date, datetime, timedelta
import random

# --- CONFIGURATION ---
st.set_page_config(page_title="Planning Médical Expert 2026", layout="wide")

# Paramètres métiers
VALEURS_HEURES = {"GW": 24, "GM": 24, "JK": 9, "JM": 7}
DB_FILE = "users_db.csv"
OFF_FILE = "desiderata_db.csv"

# Configuration des médecins (ETP et contraintes)
MEDS = {
    "Alexandra Warnant": {"etp": 0.8, "jk": True, "trio": False},
    "Alfredo Vieira": {"etp": 0.8, "jk": True, "trio": False},
    "Camie Dupuis": {"etp": 0.8, "jk": True, "trio": False},
    "Christian Davin": {"etp": 0.8, "jk": False, "trio": True},
    "Christophe Angelo": {"etp": 0.6, "jk": True, "trio": False},
    "Daryush Valadi": {"etp": 0.4, "jk": False, "trio": False, "jm_only": True},
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

# Initialisation des fichiers système
if not os.path.exists(DB_FILE):
    pd.DataFrame({"Medecin": list(MEDS.keys()), "MDP": ["Doudoudragon"] * len(MEDS)}).to_csv(DB_FILE, index=False)
if not os.path.exists(OFF_FILE):
    pd.DataFrame(columns=["Medecin", "Date_OFF"]).to_csv(OFF_FILE, index=False)

# --- FONCTION EXPORT CALENDRIER (.ICS) ---
def generate_ics(user_name, planning):
    ics_content = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Planning Dragon 2026//FR"]
    for d, postes in planning.items():
        for p_code, p_nom in postes.items():
            if p_nom == user_name:
                start = d.strftime("%Y%m%d")
                ics_content.append("BEGIN:VEVENT")
                ics_content.append(f"SUMMARY:Poste {p_code}")
                ics_content.append(f"DTSTART;VALUE=DATE:{start}")
                ics_content.append(f"DESCRIPTION:Planning Médical 2026 - Poste {p_code}")
                ics_content.append("END:VEVENT")
    ics_content.append("END:VCALENDAR")
    return "\n".join(ics_content)

# --- MOTEUR DE VALIDATION DES RÈGLES ---
def est_valide(nom, date_obj, poste, planning, v_off):
    if date_obj.strftime("%Y-%m-%d") in v_off.get(nom, []): return False
    veille = date_obj - timedelta(days=1)
    if veille in planning and nom in planning[veille].values(): return False
    if nom == "Daryush Valadi":
        if date_obj.weekday() == 0 or poste != "JM": return False
    if MEDS[nom]["trio"] and poste != "GW": return False
    return True

# --- INTERFACE DE CONNEXION ---
if 'user' not in st.session_state:
    st.title("🏥 Accès Planning Médical 2026")
    u_df = get_data(DB_FILE)
    user_sel = st.selectbox("Sélectionnez votre nom", list(MEDS.keys()))
    pwd_in = st.text_input("Mot de passe", type="password")
    
    if st.button("Se connecter"):
        if not u_df.empty:
            correct_pwd = u_df.loc[u_df["Medecin"] == user_sel, "MDP"].values[0]
            if pwd_in == correct_pwd:
                st.session_state.user = user_sel
                st.rerun()
            else:
                st.error("Mot de passe incorrect.")
else:
    # --- ESPACE CONNECTÉ ---
    st.sidebar.title(f"Dr {st.session_state.user}")
    
    # Restriction d'accès : Seul Christophe Angelo voit le Générateur
    ADMIN_USER = "Christophe Angelo"
    options_menu = ["📅 Mes OFF", "🔐 Sécurité", "Déconnexion"]
    
    if st.session_state.user == ADMIN_USER:
        options_menu.insert(1, "🚀 Générateur")
        
    mode = st.sidebar.radio("Menu", options_menu)

    # --- MODE : MES OFF ---
    if mode == "📅 Mes OFF":
        st.header("Gestion de vos indisponibilités")
        annee = 2026
        m_sel = st.selectbox("Choisir le mois :", [4, 5, 6, 7, 8], format_func=lambda x: calendar.month_name[x])
        
        all_off = get_data(OFF_FILE)
        curr_off = set(all_off[all_off["Medecin"] == st.session_state.user]["Date_OFF"].astype(str).tolist())
        
        cal = calendar.monthcalendar(annee, m_sel)
        cols_h = st.columns(7)
        for i, jn in enumerate(["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]): cols_h[i].write(f"**{jn}**")
        
        for sem in cal:
