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
        st.header("Planning Mensuel par Poste")
        df_p = read_sheet("Planning")
        
        if not df_p.empty:
            # 1. Filtre par mois
            mois_selectionne = st.selectbox("Mois", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
            
            # 2. Préparation des données
            df_p['Date_DT'] = pd.to_datetime(df_p['Date'])
            df_view = df_p[df_p['Date_DT'].dt.month == mois_selectionne].copy()
            
            if not df_view.empty:
                # Création du pivot : Lignes=Date, Colonnes=Poste, Valeurs=Medecin
                # On utilise 'first' au cas où il y aurait des doublons par erreur
                df_pivot = df_view.pivot_table(
                    index='Date', 
                    columns='Poste', 
                    values='Medecin', 
                    aggfunc='first'
                ).reset_index()

                # S'assurer que toutes les colonnes demandées existent, même si vides
                for col in ["JM", "GM", "GW", "JK (Kennedy)"]:
                    if col not in df_pivot.columns:
                        df_pivot[col] = ""

                # Réorganiser les colonnes dans l'ordre demandé
                colonnes_ordre = ["Date", "JM", "GM", "GW", "JK (Kennedy)"]
                df_pivot = df_pivot[colonnes_ordre]

                # 3. Style et Affichage
                def style_planning(row):
                    date_obj = pd.to_datetime(row['Date'])
                    feries = ["2026-04-06", "2026-05-01", "2026-05-14", "2026-05-25", "2026-07-21", "2026-08-15"]
                    # Colorer toute la ligne si c'est un WE ou Férié
                    if date_obj.weekday() >= 5 or row['Date'] in feries:
                        return ['background-color: #fff2f2'] * len(row)
                    return [''] * len(row)

                st.dataframe(
                    df_pivot.style.apply(style_planning, axis=1),
                    use_container_width=True,
                    height=800
                )
            else:
                st.info("Aucune donnée pour ce mois.")
        else:
            st.info("Le planning est vide. Allez dans l'onglet 'Admin' pour le générer.")
    elif choix == "🚀 Admin":
        st.header("Console Administrateur")
        t1, t2 = st.tabs(["📊 Bilan d'Équité", "⚙️ Générateur 5 Mois"])

        with t1:
            st.subheader("Bilan Réel (Équilibre Heures et Jours Rouges)")
            df_u = read_sheet("Users")
            df_p = read_sheet("Planning")
            
            if not df_u.empty and not df_p.empty:
                df_p['Heures'] = pd.to_numeric(df_p['Heures'], errors='coerce').fillna(0)
                feries = ["2026-04-06", "2026-05-01", "2026-05-14", "2026-05-25", "2026-07-21", "2026-08-15"]
                bilan = []
                
                for _, r in df_u.iterrows():
                    nom = r['Medecin']
                    etp = float(str(r['ETP']).replace(',','.')) if r['ETP'] else 1.0
                    m_p = df_p[df_p['Medecin'] == nom]
                    
                    hrs_tot = m_p['Heures'].sum()
                    jours_rouges = sum(1 for d in m_p['Date'] if pd.to_datetime(d).weekday() >= 5 or d in feries)
                    
                    bilan.append({
                        "Médecin": nom, "ETP": etp,
                        "Heures Totales": int(hrs_tot),
                        "Ratio H/ETP": round(hrs_tot / etp, 1),
                        "Nb Gardes (Nuits)": len(m_p[m_p['Poste'].isin(["GM", "GW"])]),
                        "Jours Rouges (WE+Fériés)": jours_rouges,
                        "Ratio Rouges/ETP": round(jours_rouges / etp, 1),
                        "Blocs JK": len(m_p[m_p['Poste'] == "JK (Kennedy)"]) // 4
                    })
                st.table(pd.DataFrame(bilan).sort_values("Ratio H/ETP"))

        with t2:
            st.subheader("Générateur : Configuration GM 7j/7 & Christian Davin")
            if st.button("🚀 Lancer la génération"):
                with st.spinner("Application des règles strictes (GM 7/7)..."):
                    # --- 1. CHARGEMENT ---
                    df_u = read_sheet("Users")
                    df_d = read_sheet("Desiderata")
                    df_r = read_sheet("Regles")
                    
                    if df_u.empty or df_r.empty:
                        st.error("Données manquantes.")
                        st.stop()

                    df_u['ETP'] = df_u['ETP'].apply(lambda x: float(str(x).replace(',','.')) if x else 1.0)
                    meds = df_u.to_dict('records')
                    regles = df_r.set_index('Medecin').to_dict('index')
                    absences = set(df_d['Medecin'] + "_" + df_d['Date_OFF']) if not df_d.empty else set()
                    feries = ["2026-04-06", "2026-05-01", "2026-05-14", "2026-05-25", "2026-07-21", "2026-08-15"]
                    
                    planning_final, jk_hist = [], []
                    heures_reelles = {m['Medecin']: 0.0 for m in meds}
                    rouges_reels = {m['Medecin']: 0 for m in meds}

                    def select_best_candidate(candidats):
                        return min(candidats, key=lambda m: (heures_reelles[m['Medecin']]/m['ETP']) + (rouges_reels[m['Medecin']]/m['ETP']))

                    def check_fatigue(nom, date_obj):
                        start_f = date_obj - timedelta(days=7)
                        recent = [p for p in planning_final if p[2] == nom and start_f <= datetime.strptime(p[0], "%Y-%m-%d") < date_obj]
                        if len(recent) >= 2:
                            if (date_obj - datetime.strptime(recent[-1][0], "%Y-%m-%d")).days < 2: return False
                        if any(p[0] == (date_obj - timedelta(days=1)).strftime("%Y-%m-%d") and p[2] == nom for p in planning_final): return False
                        return True

                    for mois in range(4, 9):
                        jours = calendar.monthrange(2026, mois)[1]
                        for j in range(1, jours + 1):
                            date_c = datetime(2026, mois, j)
                            d_str = date_c.strftime("%Y-%m-%d")
                            is_rouge = (date_c.weekday() >= 5 or d_str in feries)
                            
                            # --- A. JK (Kennedy) : Priorité Lundi ---
                            # On force un Kennedy chaque semaine, même si écourtée par un férié
                            if date_c.weekday() == 0:
                                jours_potentiels = [0, 1, 2, 4] # Lun, Mar, Mer, Ven
                                dates_jk = [(date_c + timedelta(days=d)).strftime("%Y-%m-%d") for d in jours_potentiels]
                                # Filtrer les jours qui tombent sur un férié
                                dates_jk_actives = [d for d in dates_jk if d not in feries]
                                
                                c_jk = [m for m in meds if regles.get(m['Medecin'], {}).get('Autorise_Kennedy') == 'OUI' and m['Medecin'] not in jk_hist[:7]]
                                dispos = [m for m in c_jk if all(f"{m['Medecin']}_{d}" not in absences for d in dates_jk_actives) and all(check_fatigue(m['Medecin'], datetime.strptime(d, "%Y-%m-%d")) for d in dates_jk_actives)]
                                
                                if dispos:
                                    elu = select_best_candidate(dispos)
                                    for d_jk in dates_jk_actives:
                                        planning_final.append([d_jk, "JK", elu['Medecin'], 8])
                                        heures_reelles[elu['Medecin']] += 8
                                    jk_hist.append(elu['Medecin'])

                            # --- B. DARYUSH VALADI (JM) ---
                            nom_dv = "Daryush Valadi"
                            if nom_dv in heures_reelles:
                                is_sem_A = (date_c.isocalendar()[1] % 2 == 0)
                                if date_c.weekday() in ([1,2,3] if is_sem_A else [2,3,4]) and not is_rouge:
                                    if f"{nom_dv}_{d_str}" not in absences and not any(p[0]==d_str and p[1]=="JK" for p in planning_final):
                                        planning_final.append([d_str, "JM", nom_dv, 8])
                                        heures_reelles[nom_dv] += 8

                            # --- C. JM (Pour les autres) ---
                            if not is_rouge and not any(p[0] == d_str and p[1] in ["JK", "JM"] for p in planning_final):
                                c_jm = [m for m in meds if m['Medecin'] != nom_dv and regles.get(m['Medecin'], {}).get('Autorise_Kennedy') == 'OUI' and not any(p[0] == d_str and p[2] == m['Medecin'] for p in planning_final) and f"{m['Medecin']}_{d_str}" not in absences and check_fatigue(m['Medecin'], date_c)]
                                if c_jm:
                                    elu = select_best_candidate(c_jm)
                                    planning_final.append([d_str, "JM", elu['Medecin'], 8])
                                    heures_reelles[elu['Medecin']] += 8

                            # --- D. GARDES (GM et GW) ---
                            # GM TOUS LES JOURS
                            c_gm = [m for m in meds if m['Medecin'] not in [nom_dv, "Christian Davin", "Raouf", "Elisa"] and regles.get(m['Medecin'], {}).get('Autorise_Garde_Semaine') == 'OUI']
                            cands_gm = [m for m in c_gm if not any(p[0] == d_str and p[2] == m['Medecin'] for p in planning_final) and f"{m['Medecin']}_{d_str}" not in absences and check_fatigue(m['Medecin'], date_c)]
                            if cands_gm:
                                elu = select_best_candidate(cands_gm)
                                planning_final.append([d_str, "GM", elu['Medecin'], 24])
                                heures_reelles[elu['Medecin']] += 24
                                if is_rouge: rouges_reels[elu['Medecin']] += 1
                            else: planning_final.append([d_str, "GM", "⚠️ VIDE", 0])

                            # GW TOUS LES JOURS
                            c_gw = [m for m in meds if m['Medecin'] != nom_dv]
                            # Christian, Raouf et Elisa sont inclus ici par défaut
                            cands_gw = [m for m in c_gw if not any(p[0] == d_str and p[2] == m['Medecin'] for p in planning_final) and f"{m['Medecin']}_{d_str}" not in absences and check_fatigue(m['Medecin'], date_c)]
                            if cands_gw:
                                elu = select_best_candidate(cands_gw)
                                planning_final.append([d_str, "GW", elu['Medecin'], 24])
                                heures_reelles[elu['Medecin']] += 24
                                if is_rouge: rouges_reels[elu['Medecin']] += 1
                            else: planning_final.append([d_str, "GW", "⚠️ VIDE", 0])

                    # --- 4. ENVOI ---
                    df_res = pd.DataFrame(planning_final, columns=["Date", "Poste", "Medecin", "Heures"])
                    ws = get_gsheet().worksheet("Planning")
                    ws.clear()
                    ws.append_row(["Date", "Poste", "Medecin", "Heures"])
                    ws.append_rows(df_res.values.tolist())
                    st.success("Planning généré avec GM 7/7 et Christian Davin en GW !")
                    st.balloons()
