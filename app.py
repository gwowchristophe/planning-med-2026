import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import calendar

# --- 1. CONFIGURATION (TOUJOURS EN PREMIER) ---
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
        st.error(f"Erreur de connexion : {e}")
        return None

def read_sheet(name):
    sh = get_gsheet()
    if sh:
        ws = sh.worksheet(name)
        data = ws.get_all_values()
        if len(data) > 1:
            return pd.DataFrame(data[1:], columns=data[0])
    return pd.DataFrame()

# --- 3. LOGIQUE D'AUTHENTIFICATION ---
if 'u' not in st.session_state:
    st.title("🏥 Planning Mons/Warquignies")
    df_u = read_sheet("Users")
    
    if not df_u.empty:
        u_s = st.selectbox("Sélectionnez votre nom", df_u["Medecin"].tolist())
        pw = st.text_input("Mot de passe", type="password")
        
        if st.button("Connexion"):
            correct_pw = str(df_u.loc[df_u["Medecin"] == u_s, "MDP"].values[0])
            if pw == correct_pw:
                st.session_state.u = u_s
                st.rerun()
            else:
                st.error("Mot de passe incorrect")
    else:
        st.warning("Chargement des utilisateurs... Vérifiez votre onglet 'Users'.")

# --- 4. ESPACE CONNECTÉ ---
else:
    st.sidebar.success(f"Dr. {st.session_state.u}")
    menu = ["📅 Mes Désiderata", "🔄 Échanges", "🚀 Admin", "Sortie"]
    if st.session_state.u != "Christophe Angelo":
        menu.remove("🚀 Admin")
    
    choix = st.sidebar.radio("Navigation", menu)

    if choix == "Sortie":
        del st.session_state.u
        st.rerun()

    elif choix == "📅 Mes Désiderata":
        st.header("Vos congés 2026")
        mois_noms = {4: "Avril", 5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août"}
        m = st.selectbox("Mois", options=list(mois_noms.keys()), format_func=lambda x: mois_noms[x])

        df_d = read_sheet("Desiderata")
        jours_off = set()
        if not df_d.empty:
            jours_off = set(df_d[df_d["Medecin"] == st.session_state.u]["Date_OFF"].tolist())

        cal = calendar.monthcalendar(2026, m)
        cols_h = st.columns(7)
        for i, j_nom in enumerate(["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]):
            cols_h[i].write(f"**{j_nom}**")

        for semaine in cal:
            cols = st.columns(7)
            for i, jour in enumerate(semaine):
                if jour != 0:
                    d_str = f"2026-{str(m).zfill(2)}-{str(jour).zfill(2)}"
                    is_off = d_str in jours_off
                    label = f"{jour} {'❌' if is_off else '✅'}"
                    
                    if cols[i].button(label, key=d_str):
                        sh = get_gsheet()
                        ws = sh.worksheet("Desiderata")
                        if is_off:
                            # Supprimer
                            cells = ws.findall(st.session_state.u)
                            for cell in cells:
                                if ws.cell(cell.row, 2).value == d_str:
                                    ws.delete_rows(cell.row)
                                    break
                        else:
                            # Ajouter
                            ws.append_row([st.session_state.u, d_str])
                        st.rerun()

    elif choix == "🚀 Admin":
        st.header("Vue Administrateur")
        st.write("Voici tous les desiderata encodés :")
        st.dataframe(read_sheet("Desiderata"))