import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import calendar

# --- 1. CONFIGURATION (DOIT ÊTRE LA PREMIÈRE LIGNE) ---
st.set_page_config(page_title="Planning Médical 2026", layout="wide")

# --- 2. FONCTION DE CONNEXION ---
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
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_url(st.secrets["spreadsheet"])
    except Exception as e:
        st.error(f"Erreur de connexion Google : {e}")
        return None

def read_sheet(name):
    sh = get_gsheet()
    if sh:
        return pd.DataFrame(sh.worksheet(name).get_all_records())
    return pd.DataFrame()

# --- 3. LOGIQUE D'AFFICHAGE ---
if 'u' not in st.session_state:
    st.title("🏥 Planning Mons/Warquignies")
    
    # Tentative de lecture des utilisateurs
    try:
        df_u = read_sheet("Users")
        if not df_u.empty:
            u_s = st.selectbox("Sélectionnez votre nom", df_u["Medecin"].tolist())
            pw = st.text_input("Mot de passe", type="password")
            
            if st.button("Connexion"):
                # Vérification du mot de passe (on convertit en string pour éviter les bugs)
                correct_pw = str(df_u.loc[df_u["Medecin"] == u_s, "MDP"].values[0])
                if pw == correct_pw:
                    st.session_state.u = u_s
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect")
        else:
            st.error("L'onglet 'Users' est vide ou inaccessible.")
    except Exception as e:
        st.error(f"Erreur lors du chargement des utilisateurs : {e}")

else:
    # Interface une fois connecté
    st.sidebar.success(f"Connecté : Dr. {st.session_state.u}")
    if st.sidebar.button("Déconnexion"):
        del st.session_state.u
        st.rerun()
    
    st.write(f"Bienvenue sur votre espace de gestion, Dr. {st.session_state.u}")
    # Ajoutez ici la suite de vos onglets (Désiderata, etc.)