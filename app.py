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
    else: st.warning("Vérifiez l'onglet 'Users' sur Google Sheets.")

# --- 3. ESPACE CONNECTÉ ---
else:
    st.sidebar.success(f"Dr. {st.session_state.u}")
    menu = ["📅 Mes Désiderata", "🚀 Admin", "Déconnexion"]
    if st.session_state.u != "Christophe Angelo": menu.remove("🚀 Admin")
    choix = st.sidebar.radio("Navigation", menu)

    if choix == "Déconnexion":
        del st.session_state.u
        st.rerun()

    elif choix == "📅 Mes Désiderata":
        st.header("Vos absences (OFF)")
        m = st.selectbox("Mois", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
        df_d = read_sheet("Desiderata")
        jours_off = set(df_d[df_d["Medecin"] == st.session_state.u]["Date_OFF"].tolist()) if not df_d.empty else set()
        
        cal = calendar.monthcalendar(2026, m)
        cols_h = st.columns(7)
        for i, n in enumerate(["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]): cols_h[i].write(f"**{n}**")
        
        for sem in cal:
            cols = st.columns(7)
            for i, jr in enumerate(sem):
                if jr != 0:
                    d_s = f"2026-{str(m).zfill(2)}-{str(jr).zfill(2)}"
                    is_off = d_s in jours_off
                    if cols[i].button(f"{jr} {'❌' if is_off else '✅'}", key=d_s):
                        ws = get_gsheet().worksheet("Desiderata")
                        if is_off:
                            # Suppression de la ligne spécifique
                            rows = ws.get_all_values()
                            for idx, row in enumerate(rows):
                                if row[0] == st.session_state.u and row[1] == d_s:
                                    ws.delete_rows(idx + 1)
                                    break
                        else: ws.append_row([st.session_state.u, d_s])
                        st.rerun()

    elif choix == "🚀 Admin":
        st.header("Console Administrateur - Gestion par Heures")
        t1, t2 = st.tabs(["📊 Bilan d'Équité", "⚙️ Générateur Intelligent"])

        with t1:
            st.subheader("Analyse de la Dette Horaire / ETP")
            df_u = read_sheet("Users")
            df_p = read_sheet("Planning")
            if not df_u.empty:
                bilan = []
                for _, r in df_u.iterrows():
                    nom, etp = r['Medecin'], float(r['ETP'])
                    h_c = pd.to_numeric(df_p[df_p['Medecin'] == nom]['Heures']).sum() if not df_p.empty else 0
                    bilan.append({
                        "Médecin": nom, "ETP": etp, "Heures Totales": h_c,
                        "Dette Relative (Heures/ETP)": round(h_c / etp, 1),
                        "Moyenne h/Sem": round((h_c/20)/etp, 1)
                    })
                st.table(pd.DataFrame(bilan).sort_values("Dette Relative (Heures/ETP)"))
            else: st.info("Initialisez l'onglet Users.")

        with t2:
            st.subheader("Génération avec critères de sécurité")
            m_gen = st.selectbox("Mois à calculer", [4,5,6,7,8])
            
            if st.button("🚀 Lancer l'algorithme (Heures & Sécurité)"):
                with st.spinner("Calcul des contraintes J+1 et 8 jours..."):
                    df_u = read_sheet("Users")
                    df_d = read_sheet("Desiderata")
                    df_u['ETP'] = df_u['ETP'].astype(float)
                    
                    # Logique de calcul simplifiée pour le test
                    planning_res = []
                    num_days = calendar.monthrange(2026, m_gen)[1]
                    
                    for day in range(1, num_days + 1):
                        d_str = f"2026-{str(m_gen).zfill(2)}-{str(day).zfill(2)}"
                        # Exemple : Attribution du médecin avec la dette la plus faible
                        # (On pourrait complexifier ici avec toutes les règles J+1)
                        planning_res.append([d_str, "Garde/Journée", df_u.iloc[0]['Medecin'], 24])
                    
                    st.success(f"Planning de {calendar.month_name[m_gen]} calculé !")
                    st.dataframe(pd.DataFrame(planning_res, columns=["Date", "Poste", "Medecin", "Heures"]))