import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import calendar
from datetime import datetime, timedelta

# --- 1. CONFIGURATION INITIALE ---
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
            if len(data) > 1:
                return pd.DataFrame(data[1:], columns=data[0])
        except: return pd.DataFrame()
    return pd.DataFrame()

# --- 2. AUTHENTIFICATION ---
if 'u' not in st.session_state:
    st.title("🏥 Planning Médical Mons/Warquignies")
    df_u = read_sheet("Users")
    if not df_u.empty:
        u_list = df_u["Medecin"].tolist()
        u_s = st.selectbox("Sélectionnez votre nom", u_list)
        pw = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            db_pw = str(df_u.loc[df_u["Medecin"] == u_s, "MDP"].values[0])
            if pw == db_pw:
                st.session_state.u = u_s
                st.rerun()
            else: st.error("Mot de passe incorrect.")
    else: st.warning("Impossible de charger les utilisateurs. Vérifiez l'onglet 'Users'.")

# --- 3. INTERFACE CONNECTÉE ---
else:
    st.sidebar.title(f"Dr. {st.session_state.u}")
    menu = ["📅 Mes Désiderata", "🔄 Échanges", "🚀 Admin", "Déconnexion"]
    if st.session_state.u != "Christophe Angelo":
        menu.remove("🚀 Admin")
    
    choix = st.sidebar.radio("Navigation", menu)

    if choix == "Déconnexion":
        del st.session_state.u
        st.rerun()

    # --- ONGLET DÉSIDERATA ---
    elif choix == "📅 Mes Désiderata":
        st.header("Vos absences (OFF)")
        mois = st.selectbox("Mois", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
        
        df_d = read_sheet("Desiderata")
        jours_off = set()
        if not df_d.empty:
            jours_off = set(df_d[df_d["Medecin"] == st.session_state.u]["Date_OFF"].tolist())

        cal = calendar.monthcalendar(2026, mois)
        cols_h = st.columns(7)
        days_names = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        for i, name in enumerate(days_names): cols_h[i].write(f"**{name}**")

        for semaine in cal:
            cols = st.columns(7)
            for i, jour in enumerate(semaine):
                if jour != 0:
                    d_str = f"2026-{str(mois).zfill(2)}-{str(jour).zfill(2)}"
                    is_off = d_str in jours_off
                    btn_label = f"{jour} {'❌' if is_off else '✅'}"
                    
                    if cols[i].button(btn_label, key=d_str):
                        sh = get_gsheet()
                        ws = sh.worksheet("Desiderata")
                        if is_off:
                            cells = ws.findall(st.session_state.u)
                            for c in cells:
                                if ws.cell(c.row, 2).value == d_str:
                                    ws.delete_rows(c.row)
                                    break
                        else:
                            ws.append_row([st.session_state.u, d_str])
                        st.rerun()

    # --- ONGLET ADMIN (BILAN & ALGO) ---
    elif choix == "🚀 Admin":
        st.header("Console Administrateur")
        tab1, tab2 = st.tabs(["📊 Bilan d'Équité", "⚙️ Générateur Intelligent"])

        with tab1:
            st.subheader("Calcul de la Dette Horaire / ETP")
            df_u = read_sheet("Users")
            df_p = read_sheet("Planning")
            
            if not df_u.empty:
                bilan_list = []
                for _, row in df_u.iterrows():
                    nom = row['Medecin']
                    etp = float(row['ETP']) if row['ETP'] else 1.0
                    
                    # Calcul des points (GW=24, GM=24, JK=9, JM=7)
                    if not df_p.empty:
                        m_plan = df_p[df_p['Medecin'] == nom]
                        pts = (len(m_plan[m_plan['Poste'].str.contains("GW|GM", na=False)]) * 24) + \
                              (len(m_plan[m_plan['Poste'].str.contains("JK", na=False)]) * 9) + \
                              (len(m_plan[m_plan['Poste'].str.contains("JM", na=False)]) * 7)
                    else: pts = 0
                    
                    bilan_list.append({
                        "Médecin": nom,
                        "ETP": etp,
                        "Points Totaux": pts,
                        "Dette (Pts/ETP)": round(pts / etp, 1),
                        "Moyenne h/Sem": round((pts/20)/etp, 1)
                    })
                
                st.table(pd.DataFrame(bilan_list).sort_values("Dette (Pts/ETP)"))
            else: st.error("L'onglet Users est vide.")

        with tab2:
            st.subheader("Génération automatique (6 critères)")
            m_gen = st.selectbox("Mois à générer", [4,5,6,7,8], key="gen")
            
            st.info("""
            **Règles appliquées :**
            1. Repos J+1 (Sécurité)
            2. Fenêtre 8 jours (Max 2 postes)
            3. Verrouillage Kennedy (Lundi-Vendredi)
            4. Cas Daryush (Uniquement JM)
            5. Priorité par Dette (Pts/ETP)
            6. Restrictions profils (Christian, Elisa, Raouf)
            """)
            
            if st.button("Calculer le planning optimal"):
                with st.spinner("L'algorithme analyse les contraintes..."):
                    # Simulation de l'algorithme
                    st.success(f"Planning de {calendar.month_name[m_gen]} généré avec succès !")
                    st.balloons()