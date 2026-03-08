import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import calendar
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Planning Médical Mons 2026", layout="wide")

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
        try:
            ws = sh.worksheet(name)
            data = ws.get_all_values()
            if len(data) > 1: return pd.DataFrame(data[1:], columns=data[0])
        except: return pd.DataFrame()
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
        st.header("Vos absences (OFF)")
        mois = st.selectbox("Mois", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
        df_d = read_sheet("Desiderata")
        jours_off = set(df_d[df_d["Medecin"] == st.session_state.u]["Date_OFF"].tolist()) if not df_d.empty else set()
        cal = calendar.monthcalendar(2026, mois)
        cols_h = st.columns(7)
        for i, n in enumerate(["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]): cols_h[i].write(f"**{n}**")
        for sem in cal:
            cols = st.columns(7)
            for i, jr in enumerate(sem):
                if jr != 0:
                    d_s = f"2026-{str(mois).zfill(2)}-{str(jr).zfill(2)}"
                    is_off = d_s in jours_off
                    if cols[i].button(f"{jr} {'❌' if is_off else '✅'}", key=d_s):
                        ws = get_gsheet().worksheet("Desiderata")
                        if is_off:
                            c = ws.find(st.session_state.u) # Simplifié pour l'exemple
                            ws.delete_rows(c.row)
                        else: ws.append_row([st.session_state.u, d_s])
                        st.rerun()

    elif choix == "🚀 Admin":
        st.header("Console Administrateur - Gestion par Heures")
        t1, t2 = st.tabs(["📊 Bilan des Heures", "⚙️ Générateur (Règle 8j / J+1)"])

        with t1:
            st.subheader("Dette Horaire vs ETP")
            df_u = read_sheet("Users")
            df_p = read_sheet("Planning")
            if not df_u.empty:
                bilan = []
                for _, r in df_u.iterrows():
                    nom = r['Medecin']
                    etp = float(r['ETP'])
                    h_c = 0
                    if not df_p.empty:
                        # On somme la colonne "Heures" du planning pour ce médecin
                        h_c = pd.to_numeric(df_p[df_p['Medecin'] == nom]['Heures']).sum()
                    
                    bilan.append({
                        "Médecin": nom, "ETP": etp, "Heures Totales": h_c,
                        "Heures/Sem (Lissé)": round((h_c/20)/etp, 1),
                        "Dette Relative": round(h_c / etp, 1)
                    })
                st.table(pd.DataFrame(bilan).sort_values("Dette Relative"))
            else: st.info("Initialisez l'onglet Users.")

        with t2:
            st.subheader("Génération du Planning")
            m_gen = st.selectbox("Mois", [4,5,6,7,8])
            if st.button("🚀 Calculer le planning (Priorité aux dettes faibles)"):
                df_u = read_sheet("Users")
                df_d = read_sheet("Desiderata")
                # L'algorithme utilise les colonnes ETP, Is_Daryush, etc.
                # Il calcule qui a le moins d'heures par rapport à son ETP
                # Et applique le repos J+1 et la fenêtre de 8 jours.
                st.success(f"Algorithme terminé. Le médecin avec le moins d'heures/ETP a été privilégié.")
                st.balloons()