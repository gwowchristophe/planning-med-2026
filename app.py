import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import calendar
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Planning Mons/Warquignies 2026", layout="wide")

def get_gsheet():
    try:
        creds_dict = {
            "type": st.secrets["type"], "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"], "private_key": st.secrets["private_key"],
            "client_email": st.secrets["client_email"], "client_id": st.secrets["client_id"],
            "auth_uri": st.secrets["auth_uri"], "token_uri": st.secrets["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["client_x509_cert_url"]
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
    st.title("🏥 Planning Médical 2026")
    df_u = read_sheet("Users")
    if not df_u.empty:
        u_s = st.selectbox("Médecin", df_u["Medecin"].tolist())
        pw = st.text_input("Mot de passe", type="password")
        if st.button("Connexion"):
            db_pw = str(df_u.loc[df_u["Medecin"] == u_s, "MDP"].values[0])
            if pw == db_pw:
                st.session_state.u = u_s
                st.rerun()
            else: st.error("MDP incorrect")
    else: st.warning("Vérifiez l'onglet 'Users' (colonnes Medecin, MDP, ETP...)")

# --- 3. ESPACE CONNECTÉ ---
else:
    st.sidebar.success(f"Dr. {st.session_state.u}")
    menu = ["📅 Mes Désiderata", "📊 Planning Global", "🚀 Admin", "Sortie"]
    if st.session_state.u != "Christophe Angelo": menu.remove("🚀 Admin")
    choix = st.sidebar.radio("Navigation", menu)

    if choix == "Sortie":
        del st.session_state.u
        st.rerun()

    elif choix == "📅 Mes Désiderata":
        st.header("Vos absences (OFF)")
        m = st.selectbox("Mois", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
        df_d = read_sheet("Desiderata")
        jours_off = set(df_d[df_d["Medecin"] == st.session_state.u]["Date_OFF"].tolist()) if not df_d.empty else set()
        cal = calendar.monthcalendar(2026, m)
        cols_h = st.columns(7)
        for i, n in enumerate(["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"]): cols_h[i].write(f"**{n}**")
        for sem in cal:
            cols = st.columns(7)
            for i, jr in enumerate(sem):
                if jr != 0:
                    d_s = f"2026-{str(m).zfill(2)}-{str(jr).zfill(2)}"
                    lbl = f"{jr} {'❌' if d_s in jours_off else '✅'}"
                    if cols[i].button(lbl, key=d_s):
                        ws = get_gsheet().worksheet("Desiderata")
                        if d_s in jours_off:
                            try:
                                cell = ws.find(st.session_state.u)
                                rows = ws.get_all_values()
                                for idx, row in enumerate(rows):
                                    if row[0] == st.session_state.u and row[1] == d_s:
                                        ws.delete_rows(idx + 1)
                                        break
                            except: pass
                        else: ws.append_row([st.session_state.u, d_s])
                        st.rerun()

    elif choix == "📊 Planning Global":
        st.header("Planning Validé")
        m_v = st.selectbox("Mois", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
        df_p = read_sheet("Planning")
        if not df_p.empty:
            df_p['Date'] = pd.to_datetime(df_p['Date'])
            df_m = df_p[df_p['Date'].dt.month == m_v].sort_values("Date")
            st.dataframe(df_m, use_container_width=True)

    elif choix == "🚀 Admin":
        st.header("Console Administrateur")
        t1, t2 = st.tabs(["📊 Bilan d'Équité", "⚙️ Générateur (6 Critères)"])

        with t1:
            df_u = read_sheet("Users")
            df_p = read_sheet("Planning")
            if not df_u.empty:
                bilan = []
                for _, r in df_u.iterrows():
                    nom = r['Medecin']
                    etp = float(str(r['ETP']).replace(',','.')) if r['ETP'] else 1.0
                    m_p = df_p[df_p['Medecin'] == nom] if not df_p.empty else pd.DataFrame()
                    hrs = pd.to_numeric(m_p['Heures'], errors='coerce').sum()
                    bilan.append({
                        "Médecin": nom, "ETP": etp, "Heures": hrs,
                        "Dette (H/ETP)": round(hrs/etp, 1),
                        "Nuits": len(m_p[m_p['Poste'].str.contains("G", na=False)]),
                        "WE": len(m_p[m_p['Poste'].str.contains("GW", na=False)]),
                        "Kennedy": len(m_p[m_p['Poste'].str.contains("JK", na=False)]) // 4
                    })
                st.table(pd.DataFrame(bilan).sort_values("Dette (H/ETP)"))

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import calendar
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Planning Mons/Warquignies 2026", layout="wide")

def get_gsheet():
    try:
        creds_dict = {
            "type": st.secrets["type"], "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"], "private_key": st.secrets["private_key"],
            "client_email": st.secrets["client_email"], "client_id": st.secrets["client_id"],
            "auth_uri": st.secrets["auth_uri"], "token_uri": st.secrets["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["client_x509_cert_url"]
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
    st.title("🏥 Planning Médical 2026")
    df_u = read_sheet("Users")
    if not df_u.empty:
        u_s = st.selectbox("Médecin", df_u["Medecin"].tolist())
        pw = st.text_input("Mot de passe", type="password")
        if st.button("Connexion"):
            db_pw = str(df_u.loc[df_u["Medecin"] == u_s, "MDP"].values[0])
            if pw == db_pw:
                st.session_state.u = u_s
                st.rerun()
            else: st.error("MDP incorrect")
    else: st.warning("Vérifiez l'onglet 'Users' (colonnes Medecin, MDP, ETP...)")

# --- 3. ESPACE CONNECTÉ ---
else:
    st.sidebar.success(f"Dr. {st.session_state.u}")
    menu = ["📅 Mes Désiderata", "📊 Planning Global", "🚀 Admin", "Sortie"]
    if st.session_state.u != "Christophe Angelo": menu.remove("🚀 Admin")
    choix = st.sidebar.radio("Navigation", menu)

    if choix == "Sortie":
        del st.session_state.u
        st.rerun()

    elif choix == "📅 Mes Désiderata":
        st.header("Vos absences (OFF)")
        m = st.selectbox("Mois", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
        df_d = read_sheet("Desiderata")
        jours_off = set(df_d[df_d["Medecin"] == st.session_state.u]["Date_OFF"].tolist()) if not df_d.empty else set()
        cal = calendar.monthcalendar(2026, m)
        cols_h = st.columns(7)
        for i, n in enumerate(["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"]): cols_h[i].write(f"**{n}**")
        for sem in cal:
            cols = st.columns(7)
            for i, jr in enumerate(sem):
                if jr != 0:
                    d_s = f"2026-{str(m).zfill(2)}-{str(jr).zfill(2)}"
                    lbl = f"{jr} {'❌' if d_s in jours_off else '✅'}"
                    if cols[i].button(lbl, key=d_s):
                        ws = get_gsheet().worksheet("Desiderata")
                        if d_s in jours_off:
                            try:
                                cell = ws.find(st.session_state.u)
                                rows = ws.get_all_values()
                                for idx, row in enumerate(rows):
                                    if row[0] == st.session_state.u and row[1] == d_s:
                                        ws.delete_rows(idx + 1)
                                        break
                            except: pass
                        else: ws.append_row([st.session_state.u, d_s])
                        st.rerun()

    elif choix == "📊 Planning Global":
        st.header("Planning Validé")
        m_v = st.selectbox("Mois", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
        df_p = read_sheet("Planning")
        if not df_p.empty:
            df_p['Date'] = pd.to_datetime(df_p['Date'])
            df_m = df_p[df_p['Date'].dt.month == m_v].sort_values("Date")
            st.dataframe(df_m, use_container_width=True)

    elif choix == "🚀 Admin":
        st.header("Console Administrateur")
        t1, t2 = st.tabs(["📊 Bilan d'Équité", "⚙️ Générateur (6 Critères)"])

        with t1:
            df_u = read_sheet("Users")
            df_p = read_sheet("Planning")
            if not df_u.empty:
                bilan = []
                for _, r in df_u.iterrows():
                    nom = r['Medecin']
                    etp = float(str(r['ETP']).replace(',','.')) if r['ETP'] else 1.0
                    m_p = df_p[df_p['Medecin'] == nom] if not df_p.empty else pd.DataFrame()
                    hrs = pd.to_numeric(m_p['Heures'], errors='coerce').sum()
                    bilan.append({
                        "Médecin": nom, "ETP": etp, "Heures": hrs,
                        "Dette (H/ETP)": round(hrs/etp, 1),
                        "Nuits": len(m_p[m_p['Poste'].str.contains("G", na=False)]),
                        "WE": len(m_p[m_p['Poste'].str.contains("GW", na=False)]),
                        "Kennedy": len(m_p[m_p['Poste'].str.contains("JK", na=False)]) // 4
                    })
                st.table(pd.DataFrame(bilan).sort_values("Dette (H/ETP)"))

        with t2:
            st.subheader("Générateur Global (Avril à Août 2026)")
            st.info("L'algorithme calcule les 5 mois d'un coup pour garantir l'équité (Heures/ETP).")
            
            if st.button("🚀 Lancer la génération harmonisée sur 5 mois"):
                with st.spinner("Équilibrage des dettes horaires en cours..."):
                    # 1. PRÉPARATION DES DONNÉES
                    df_u = read_sheet("Users")
                    df_d = read_sheet("Desiderata")
                    
                    if df_u.empty:
                        st.error("L'onglet 'Users' est vide.")
                    else:
                        # Nettoyage ETP et préparation des profils
                        df_u['ETP'] = df_u['ETP'].apply(lambda x: float(str(x).replace(',','.')) if x else 1.0)
                        meds = df_u.to_dict('records')
                        absences = set(df_d['Medecin'] + "_" + df_d['Date_OFF']) if not df_d.empty else set()
                        
                        # Initialisation
                        dettes = {m['Medecin']: 0.0 for m in meds}
                        planning_global = []

                        # 2. BOUCLE SUR LES 5 MOIS (Avril à Août)
                        for mois in range(4, 9):
                            jours_mois = calendar.monthrange(2026, mois)[1]
                            for j in range(1, jours_mois + 1):
                                date_c = datetime(2026, mois, j)
                                d_str = date_c.strftime("%Y-%m-%d")
                                is_we = date_c.weekday() >= 5
                                
                                # Définition du poste (Ex: Garde 24h)
                                poste_nom, h_p = ("GW", 24) if is_we else ("GM", 24)

                                # FILTRAGE (REPOS J+1, DARYUSH, 8 JOURS)
                                candidats = []
                                for m in meds:
                                    nom = m['Medecin']
                                    # Règle 1: Pas OFF
                                    if f"{nom}_{d_str}" in absences: continue
                                    # Règle 2: Repos J+1
                                    h_hier = (date_c - timedelta(days=1)).strftime("%Y-%m-%d")
                                    if any(p[0] == h_hier and p[2] == nom for p in planning_global): continue
                                    # Règle 3: Daryush (Pas de WE)
                                    if m.get('Is_Daryush') == 'OUI' and is_we: continue
                                    # Règle 4: Max 2 postes sur 8 jours glissants
                                    h_8d = (date_c - timedelta(days=8)).strftime("%Y-%m-%d")
                                    if len([p for p in planning_global if p[2] == nom and p[0] > h_8d]) >= 2: continue
                                    
                                    candidats.append(m)

                                if candidats:
                                    choisi = min(candidats, key=lambda x: dettes[x['Medecin']])
                                    dettes[choisi['Medecin']] += (h_p / choisi['ETP'])
                                    planning_global.append([d_str, poste_nom, choisi['Medecin'], h_p])
                                else:
                                    planning_global.append([d_str, poste_nom, "⚠️ VIDE", 0])

                        # 3. AFFICHAGE ET EXPORT AUTOMATIQUE
                        df_res = pd.DataFrame(planning_global, columns=["Date", "Poste", "Medecin", "Heures"])
                        st.success("Planning généré et équilibré !")
                        st.dataframe(df_res)
                        
                        # Publication immédiate
                        ws_plan = get_gsheet().worksheet("Planning")
                        ws_plan.clear()
                        ws_plan.append_row(["Date", "Poste", "Medecin", "Heures"])
                        ws_plan.append_rows(df_res.values.tolist())
                        st.balloons()
