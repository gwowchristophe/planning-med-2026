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
    st.title("🏥 Planning Mons/Warquignies 2026")
    df_u = read_sheet("Users")
    if not df_u.empty:
        u_s = st.selectbox("Médecin", df_u["Medecin"].tolist(), key="login_select")
        pw = st.text_input("Mot de passe", type="password")
        if st.button("Connexion"):
            db_pw = str(df_u.loc[df_u["Medecin"] == u_s, "MDP"].values[0])
            if pw == db_pw:
                st.session_state.u = u_s
                st.rerun()
            else: st.error("MDP incorrect")
    else: st.warning("Vérifiez l'onglet 'Users'.")

# --- 3. INTERFACE ---
else:
    st.sidebar.success(f"Dr. {st.session_state.u}")
    menu_options = ["📅 Mes Désiderata", "📊 Planning Global", "🚀 Admin", "Déconnexion"]
    if st.session_state.u != "Christophe Angelo":
        menu_options.remove("🚀 Admin")
    
    # Navigation unique avec clé pour éviter StreamlitDuplicateElementId
    choix = st.sidebar.radio("Navigation", menu_options, key="main_nav")

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
                            rows = ws.get_all_values()
                            for idx, r in enumerate(rows):
                                if r[0] == st.session_state.u and r[1] == d_s:
                                    ws.delete_rows(idx + 1)
                                    break
                        else: ws.append_row([st.session_state.u, d_s])
                        st.rerun()

    elif choix == "📊 Planning Global":
        st.header("Consulter le planning")
        df_p = read_sheet("Planning")
        if not df_p.empty:
            df_p['Date'] = pd.to_datetime(df_p['Date'])
            m_v = st.selectbox("Mois", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
            df_m = df_p[df_p['Date'].dt.month == m_v].sort_values("Date")
            st.dataframe(df_m, use_container_width=True)

    elif choix == "🚀 Admin":
        st.header("Console Administrateur")
        t1, t2 = st.tabs(["📊 Bilan d'Équité", "⚙️ Générateur 5 Mois"])

        with t1:
            st.subheader("Analyse de la Dette (Heures / ETP)")
            df_u = read_sheet("Users")
            df_p = read_sheet("Planning")
            
            # --- CORRECTION ROBUSTE ---
            # Si le planning est vide, on crée un tableau vide avec la colonne Heures pour éviter le crash
            if df_p.empty or 'Heures' not in df_p.columns:
                df_p = pd.DataFrame(columns=["Date", "Poste", "Medecin", "Heures"])
            
            if not df_u.empty:
                bilan = []
                for _, r in df_u.iterrows():
                    nom = r['Medecin']
                    # Sécurité sur l'ETP
                    try:
                        etp = float(str(r['ETP']).replace(',','.')) if r['ETP'] else 1.0
                    except:
                        etp = 1.0
                    
                    m_p = df_p[df_p['Medecin'] == nom]
                    # On force la conversion en nombre, si vide ou erreur -> 0
                    hrs = pd.to_numeric(m_p['Heures'], errors='coerce').sum()
                    
                    bilan.append({
                        "Médecin": nom, 
                        "ETP": etp, 
                        "Heures": hrs,
                        "Dette (H/ETP)": round(hrs/etp, 1) if etp > 0 else 0,
                        "Nuits": len(m_p[m_p['Poste'].str.contains("G", na=False)]),
                        "WE": len(m_p[m_p['Poste'].str.contains("GW", na=False)])
                    })
                st.table(pd.DataFrame(bilan).sort_values("Dette (H/ETP)"))

        with t2:
            st.subheader("Génération Dynamique via Google Sheets")
            if st.button("🚀 Lancer la génération (Lecture des règles...)"):
                with st.spinner("Synchronisation des règles et calcul..."):
                    # --- 1. CHARGEMENT DES DONNÉES ---
                    df_u = read_sheet("Users")
                    df_d = read_sheet("Desiderata")
                    df_r = read_sheet("Regles") # <--- LIT VOTRE NOUVEL ONGLET
                    
                    if df_r.empty:
                        st.error("L'onglet 'Regles' est introuvable ou vide dans Google Sheets.")
                        st.stop()

                    df_u['ETP'] = df_u['ETP'].apply(lambda x: float(str(x).replace(',','.')) if x else 1.0)
                    meds = df_u.to_dict('records')
                    absences = set(df_d['Medecin'] + "_" + df_d['Date_OFF']) if not df_d.empty else set()
                    
                    # Transformation des règles en dictionnaire pour accès rapide
                    regles = df_r.set_index('Medecin').to_dict('index')
                    
                    dettes, planning_final = {m['Medecin']: 0.0 for m in meds}, []

                    # --- 2. BOUCLE DE GÉNÉRATION (5 MOIS) ---
                    for mois in range(4, 9):
                        jours = calendar.monthrange(2026, mois)[1]
                        for j in range(1, jours + 1):
                            date_c = datetime(2026, mois, j)
                            d_str = date_c.strftime("%Y-%m-%d")
                            is_we = date_c.weekday() >= 5
                            
                            # --- A. KENNEDY (Lun, Mar, Mer, Ven) ---
                            if date_c.weekday() == 0:
                                j_jk = [0, 1, 2, 4]
                                c_jk = [m for m in meds if regles.get(m['Medecin'], {}).get('Autorise_Kennedy') == 'OUI']
                                dispos_jk = [m for m in c_jk if all(f"{m['Medecin']}_{(date_c + timedelta(days=d)).strftime('%Y-%m-%d')}" not in absences for d in j_jk)]
                                
                                if dispos_jk:
                                    elu_jk = min(dispos_jk, key=lambda x: dettes[x['Medecin']])
                                    for d in j_jk:
                                        planning_final.append([(date_c + timedelta(days=d)).strftime("%Y-%m-%d"), "JK (Kennedy)", elu_jk['Medecin'], 8])
                                        dettes[elu_jk['Medecin']] += (8 / elu_jk['ETP'])

                            # --- B. GARDE (24h) ---
                            poste, h_p = ("GW", 24) if is_we else ("GM", 24)
                            cands = []
                            for m in meds:
                                nom = m['Medecin']
                                r = regles.get(nom, {})
                                
                                # Filtres dynamiques selon Google Sheets
                                if is_we and r.get('Autorise_Garde_WE') != 'OUI': continue
                                if not is_we and r.get('Autorise_Garde_Semaine') != 'OUI': continue
                                
                                # Sécurités automatiques (Kennedy, OFF, Repos J+1, 8 jours)
                                if any(p[0] == d_str and p[2] == nom and "JK" in p[1] for p in planning_final): continue
                                if f"{nom}_{d_str}" in absences: continue
                                
                                h_hier = (date_c - timedelta(days=1)).strftime("%Y-%m-%d")
                                if any(p[0] == h_hier and p[2] == nom and "G" in p[1] for p in planning_final): continue
                                
                                h_8d = (date_c - timedelta(days=8)).strftime("%Y-%m-%d")
                                if len([p for p in planning_final if p[2] == nom and "G" in p[1] and p[0] > h_8d]) >= 2: continue
                                
                                cands.append(m)

                            if cands:
                                elu = min(cands, key=lambda x: dettes[x['Medecin']])
                                dettes[elu['Medecin']] += (h_p / elu['ETP'])
                                planning_final.append([d_str, poste, elu['Medecin'], h_p])
                            else:
                                planning_final.append([d_str, poste, "⚠️ VIDE", 0])

                    # --- 3. PUBLICATION FINALE ---
                    df_res = pd.DataFrame(planning_final, columns=["Date", "Poste", "Medecin", "Heures"])
                    ws_p = get_gsheet().worksheet("Planning")
                    ws_p.clear()
                    ws_p.append_row(["Date", "Poste", "Medecin", "Heures"])
                    ws_p.append_rows(df_res.values.tolist())
                    st.success("Planning généré selon vos règles Google Sheet !")
                    st.balloons()
