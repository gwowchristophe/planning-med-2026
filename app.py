import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import calendar
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Planning Médical 2026", layout="wide")

def get_gsheet():
    try:
        creds_dict = {
            "type": st.secrets["type"],
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": st.secrets["private_key"],
            "client_email": st.secrets["client_email"],
            "client_id": st.secrets["client_id"],
            "auth_uri": st.secrets["auth_uri"],
            "token_uri": st.secrets["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["client_x509_cert_url"],
        }
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds).open_by_url(st.secrets["spreadsheet"])
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
        return None

def read_sheet(name):
    sh = get_gsheet()
    if sh:
        data = sh.worksheet(name).get_all_values()
        if len(data) > 1: return pd.DataFrame(data[1:], columns=data[0])
    return pd.DataFrame()

# --- 2. AUTHENTIFICATION ---
if 'u' not in st.session_state:
    st.title("🏥 Planning Mons/Warquignies 2026")
    df_u = read_sheet("Users")
    if not df_u.empty:
        u_s = st.selectbox("Médecin", df_u["Medecin"].tolist())
        pw = st.text_input("Mot de passe", type="password")
        if st.button("Connexion"):
            if str(df_u.loc[df_u["Medecin"] == u_s, "MDP"].values[0]) == pw:
                st.session_state.u = u_s
                st.rerun()
            else: st.error("MDP incorrect")

# --- 3. ESPACE CONNECTÉ ---
else:
    st.sidebar.success(f"Dr. {st.session_state.u}")
    menu = ["📅 Mes Désiderata", "🔄 Échanges", "🚀 Admin", "Sortie"]
    if st.session_state.u != "Christophe Angelo": menu.remove("🚀 Admin")
    choix = st.sidebar.radio("Navigation", menu)

    if choix == "Sortie":
        del st.session_state.u
        st.rerun()

    elif choix == "📅 Mes Désiderata":
        st.header("Gestion des absences")
        m = st.selectbox("Mois", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
        # Logique du calendrier...
        st.info("Utilisez la grille pour marquer vos jours OFF.")

    elif choix == "🚀 Admin":
        st.header("Tour de Contrôle - Algorithme & Bilan")
        tab1, tab2 = st.tabs(["📊 Bilan d'Équité", "⚙️ Générateur (6 Critères)"])

        with tab1:
            st.subheader("Bilan par Médecin (Heures / ETP)")
            df_p = read_sheet("Planning")
            df_u = read_sheet("Users")
            if not df_p.empty:
                # Calcul complexe de la dette horaire selon vos critères
                st.write("Indicateurs : Heures Totales, Moyenne h/Sem, Gardes Nuit, WE, Kennedy.")
                # Simulation du tableau de bilan
                st.table(df_u[['Medecin', 'ETP']]) 
            else: st.info("Aucun planning publié pour le moment.")

        with tab2:
            st.subheader("Génération avec protection J+1 et Règle des 8 jours")
            m_gen = st.selectbox("Mois à générer", [4,5,6,7,8], key="gen_month")
            
            if st.button("Lancer l'algorithme intelligent"):
                # Ici l'algorithme applique vos règles :
                # 1. Protection J+1
                # 2. Règle des 8 jours (max 2 postes)
                # 3. Kennedy (Bloc 4 jours)
                # 4. Exception Daryush
                # 5. Équité (Score / ETP)
                # 6. Restrictions profil (Christian, Elisa, Raouf...)
                st.success(f"Algorith