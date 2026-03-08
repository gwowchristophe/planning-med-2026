import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import calendar

# --- CONFIGURATION ---
st.set_page_config(page_title="Planning Médical 2026", layout="wide")

# --- CONNEXION GOOGLE ---
def get_gsheet():
    # Récupère les secrets au format TOML
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
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_url(st.secrets["spreadsheet"])

# Fonctions de lecture/écriture
def read_sheet(name):
    sh = get_gsheet()
    return pd.DataFrame(sh.worksheet(name).get_all_records())

def write_sheet(df, name):
    sh = get_gsheet()
    ws = sh.worksheet(name)
    ws.clear()
    ws.update([df.columns.values.tolist()] + df.values.tolist())

# --- LOGIQUE APP ---
if 'u' not in st.session_state:
    st.title("🏥 Planning Mons/Warquignies")
    df_u = read_sheet("Users")
    u_s = st.selectbox("Médecin", df_u["Medecin"].tolist())
    pw = st.text_input("Mot de passe", type="password")
    
    if st.button("Connexion"):
        if str(df_u.loc[df_u["Medecin"] == u_s, "MDP"].values[0]) == pw:
            st.session_state.u = u_s
            st.rerun()
        else: st.error("Mot de passe incorrect")

else:
    st.sidebar.title(f"Dr. {st.session_state.u}")
    sel = st.sidebar.radio("Menu", ["📅 Désiderata de congé", "🔄 Échanges", "🔑 Mot de passe", "Sortie"])

    if sel == "📅 Désiderata de congé":
        st.header("Vos congés 2026")
        mo = st.selectbox("Mois", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
        df_off = read_sheet("Desiderata")
        
        # Affichage calendrier simplifié
        mes_off = set(df_off[df_off["Medecin"] == st.session_state.u]["Date_OFF"].astype(str).tolist())
        st.write("Cochez les jours où vous êtes ABSENT :")
        
        # Création des boutons par semaine
        for week in calendar.monthcalendar(2026, mo):
            cols = st.columns(7)
            for i, d in enumerate(week):
                if d != 0:
                    ds = f"2026-{str(mo).zfill(2)}-{str(d).zfill(2)}"
                    if cols[i].button(str(d) + (" ❌" if ds in mes_off else " ✅"), key=ds):
                        if ds in mes_off:
                            df_off = df_off[~((df_off["Medecin"] == st.session_state.u) & (df_off["Date_OFF"].astype(str) == ds))]
                        else:
                            df_off = pd.concat([df_off, pd.DataFrame([{"Medecin": st.session_state.u, "Date_OFF": ds}])])
                        write_sheet(df_off, "Desiderata")
                        st.rerun()

    elif sel == "Sortie":
        del st.session_state.u
        st.rerun()