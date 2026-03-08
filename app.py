import streamlit as st
import pandas as pd
import os
import calendar
from datetime import date, timedelta
import random

# --- CONFIGURATION ET RÉGLES ---
st.set_page_config(page_title="Moteur Planning 2026", layout="wide")

# Paramètres horaires
HEURES = {"GW": 24, "GM": 24, "JK": 9, "JM": 7}
DB_FILE = "users_db.csv"
OFF_FILE = "desiderata_db.csv"

# Base de données médecins
MEDS = {
    "Alexandra Warnant": {"etp": 0.8, "jk": True, "trio": False, "jm_only": False},
    "Alfredo Vieira": {"etp": 0.8, "jk": True, "trio": False, "jm_only": False},
    "Camie Dupuis": {"etp": 0.8, "jk": True, "trio": False, "jm_only": False},
    "Christian Davin": {"etp": 0.8, "jk": False, "trio": True, "jm_only": False},
    "Christophe Angelo": {"etp": 0.6, "jk": True, "trio": False, "jm_only": False},
    "Daryush Valadi": {"etp": 0.4, "jk": False, "trio": False, "jm_only": True},
    "Elisa Mastrodiscasa": {"etp": 0.8, "jk": False, "trio": True, "jm_only": False},
    "Gauthier Nendumba": {"etp": 0.8, "jk": True, "trio": False, "jm_only": False},
    "Julie Henrie": {"etp": 0.6, "jk": True, "trio": False, "jm_only": False},
    "Martin Hachez": {"etp": 0.8, "jk": True, "trio": False, "jm_only": False},
    "PF Laterre": {"etp": 0.8, "jk": False, "trio": False, "jm_only": False, "pref_jm": True},
    "Raouf Sheta": {"etp": 0.8, "jk": False, "trio": True, "jm_only": False},
    "Simon Van Migem": {"etp": 0.8, "jk": True, "trio": False, "jm_only": False}
}

# --- FONCTIONS UTILES ---
def get_data(f): return pd.read_csv(f) if os.path.exists(f) else pd.DataFrame()

def est_valide(nom, date_obj, poste, planning, v_off):
    # 1. Vérifier les OFF encodés
    if date_obj.strftime("%Y-%m-%d") in v_off.get(nom, []): return False
    
    # 2. Repos Post-Garde (Pas de travail si garde la veille)
    veille = date_obj - timedelta(days=1)
    if veille in planning and nom in planning[veille].values(): return False

    # 3. Règle Daryush (Ma paires / Ve impaires)
    if nom == "Daryush Valadi":
        semaine = date_obj.isocalendar()[1]
        if date_obj.weekday() == 0: return False # Lundi OFF
        if date_obj.weekday() == 1 and semaine % 2 != 0: return False # Mardi Semaine Paire
        if date_obj.weekday() == 4 and semaine % 2 == 0: return False # Vendredi Semaine Impaire
        if poste != "JM": return False

    # 4. Trio Warquignies (Uniquement GW)
    if MEDS[nom]["trio"] and poste != "GW": return False
    if not MEDS[nom]["trio"] and poste == "GW" and nom not in ["Alexandra Warnant", "Alfredo Vieira", "Camie Dupuis", "Christophe Angelo", "Gauthier Nendumba", "Julie Henrie", "Martin Hachez", "PF Laterre", "Simon Van Migem"]: return False

    return True

# --- INTERFACE ---
if 'user' not in st.session_state:
    st.title("🏥 Système Expert Planning")
    user_sel = st.selectbox("Médecin", list(MEDS.keys()))
    if st.button("Accéder"): 
        st.session_state.user = user_sel
        st.rerun()
else:
    st.sidebar.title(f"Dr {st.session_state.user}")
    mode = st.sidebar.radio("Menu", ["📅 Mes OFF", "🚀 Générateur", "Logout"])

    if mode == "📅 Mes OFF":
        st.header("Vos indisponibilités (Avril - Août 2026)")
        m_sel = st.selectbox("Mois", [4,5,6,7,8])
        all_off = get_data(OFF_FILE)
        # Interface de calendrier (identique à la précédente)...
        # [Code de sélection de calendrier ici]
        st.write("Veuillez cliquer sur vos jours de congés dans le calendrier.")

    elif mode == "🚀 Générateur":
        st.header("Générateur d'horaire sous contraintes")
        mois_gen = st.slider("Mois à calculer", 4, 8)
        
        if st.button("Lancer la génération"):
            with st.spinner("Calcul des combinaisons en cours..."):
                off_data = get_data(OFF_FILE)
                v_off = off_data.groupby("Medecin")["Date_OFF"].apply(list).to_dict()
                
                # Initialisation Planning
                planning_final = {}
                dates_mois = [date(2026, mois_gen, d) for d in range(1, calendar.monthrange(2026, mois_gen)[1] + 1)]
                
                success = True
                for d in dates_mois:
                    jour_plan = {}
                    dispos = [m for m in MEDS.keys()]
                    random.shuffle(dispos) # Pour l'équité aléatoire au début
                    
                    # 1. Assigner GW (Priorité Trio)
                    try:
                        candidats_gw = [m for m in dispos if est_valide(m, d, "GW", planning_final, v_off)]
                        jour_plan["GW"] = candidats_gw[0]
                    except: success = False; break
                    
                    # 2. Assigner GM
                    try:
                        candidats_gm = [m for m in dispos if m != jour_plan["GW"] and est_valide(m, d, "GM", planning_final, v_off)]
                        jour_plan["GM"] = candidats_gm[0]
                    except: success = False; break
                    
                    # 3. Assigner JK (Lu, Ma, Me, Ve)
                    if d.weekday() in [0, 1, 2, 4]:
                        try:
                            candidats_jk = [m for m in dispos if m not in jour_plan.values() and MEDS[m]["jk"] and est_valide(m, d, "JK", planning_final, v_off)]
                            jour_plan["JK"] = candidats_jk[0]
                        except: success = False; break
                    
                    # 4. Assigner JM (Semaine)
                    if d.weekday() < 5:
                        try:
                            candidats_jm = [m for m in dispos if m not in jour_plan.values() and est_valide(m, d, "JM", planning_final, v_off)]
                            jour_plan["JM"] = candidats_jm[0]
                        except: success = False; break
                    
                    planning_final[d] = jour_plan

                if not success:
                    st.error("❌ IMPOSSIBLE : Incompatibilité avec les critères (Trop de OFF ou repos impossibles)")
                else:
                    st.success("✅ Horaire trouvé !")
                    st.table(pd.DataFrame.from_dict(planning_final, orient='index'))

    if mode == "Logout":
        del st.session_state.user
        st.rerun()
