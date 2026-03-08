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
            mois_selectionne = st.selectbox("Mois", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
            
            df_p['Date_DT'] = pd.to_datetime(df_p['Date'])
            df_view = df_p[df_p['Date_DT'].dt.month == mois_selectionne].copy()
            
            if not df_view.empty:
                # Création du pivot
                df_pivot = df_view.pivot_table(
                    index='Date', 
                    columns='Poste', 
                    values='Medecin', 
                    aggfunc='first'
                ).reset_index()

                # --- SÉCURITÉ ANTI-PLANTAGE ---
                # Liste exacte des colonnes attendues
                colonnes_ordre = ["Date", "JM", "GM", "GW", "JK"]
                
                # Si une colonne manque (ex: JK), on la crée vide pour éviter l'erreur KeyError
                for col in colonnes_ordre:
                    if col not in df_pivot.columns:
                        df_pivot[col] = ""
                
                # Maintenant on peut réorganiser sans risque
                df_pivot = df_pivot[colonnes_ordre]

                def style_planning(row):
                    date_obj = pd.to_datetime(row['Date'])
                    feries = ["2026-04-06", "2026-05-01", "2026-05-14", "2026-05-25", "2026-07-21", "2026-08-15"]
                    if date_obj.weekday() >= 5 or row['Date'] in feries:
                        return ['background-color: #fff2f2'] * len(row)
                    return [''] * len(row)

                st.dataframe(df_pivot.style.apply(style_planning, axis=1), use_container_width=True, height=800)
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
            st.subheader("Générateur de Planning Final")
            if st.button("🚀 Lancer la génération"):
                with st.spinner("Application des règles complexes..."):
                    # 1. CHARGEMENT
                    df_u = read_sheet("Users")
                    df_d = read_sheet("Desiderata")
                    df_r = read_sheet("Regles")
                    
                    if df_u.empty or df_r.empty:
                        st.error("Données 'Users' ou 'Regles' manquantes.")
                        st.stop()

                    df_u['ETP'] = df_u['ETP'].apply(lambda x: float(str(x).replace(',','.')) if x else 1.0)
                    meds = df_u.to_dict('records')
                    regles = df_r.set_index('Medecin').to_dict('index')
                    absences = set(df_d['Medecin'] + "_" + df_d['Date_OFF']) if not df_d.empty else set()
                    feries = ["2026-04-06", "2026-05-01", "2026-05-14", "2026-05-25", "2026-07-21", "2026-08-15"]
                    
                    planning_final, jk_hist = [], []
                    heures_reelles = {m['Medecin']: 0.0 for m in meds}
                    rouges_reels = {m['Medecin']: 0 for m in meds}

                    # 2. LOGIQUE D'ÉQUITÉ ET SÉCURITÉ
                    def select_best_candidate(candidats):
                        return min(candidats, key=lambda m: (heures_reelles[m['Medecin']]/m['ETP']) + (rouges_reels[m['Medecin']]/m['ETP']))

                    def check_fatigue(nom, date_obj):
                        # Pas de poste si garde la veille
                        hier = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
                        if any(p[0] == hier and p[2] == nom for p in planning_final): return False
                        return True

                    # 3. BOUCLE TEMPORELLE
                    for mois in range(4, 9):
                        jours = calendar.monthrange(2026, mois)[1]
                        for j in range(1, jours + 1):
                            date_c = datetime(2026, mois, j)
                            d_str = date_c.strftime("%Y-%m-%d")
                            is_rouge = (date_c.weekday() >= 5 or d_str in feries)
                            
                            # --- A. KENNEDY (Attribution Bloc Semaine le Lundi) ---
                            if date_c.weekday() == 0:
                                jours_theo = [0, 1, 2, 4] # Lun, Mar, Mer, Ven
                                dates_reelles_jk = [(date_c + timedelta(days=d)).strftime("%Y-%m-%d") for d in jours_theo if (date_c + timedelta(days=d)).strftime("%Y-%m-%d") not in feries]
                                
                                # Vérification du contenu de la colonne Regles (on nettoie les espaces)
                                c_jk = [m for m in meds if str(regles.get(m['Medecin'], {}).get('Autorise_Kennedy', '')).strip().upper() == 'OUI']
                                
                                # Diagnostic si la liste est vide
                                if not c_jk:
                                    st.warning(f"Semaine du {d_str} : Aucun médecin n'a 'OUI' dans la colonne Autorise_Kennedy")
                                
                                # Un candidat est dispo s'il n'a pas d'OFF sur les jours RÉELS de travail
                                dispos = [m for m in c_jk if all(f"{m['Medecin']}_{d}" not in absences for d in dates_reelles_jk)]
                                
                                if dispos:
                                    # On prend le plus équitable (on réduit la contrainte jk_hist pour le test)
                                    elu = select_best_candidate(dispos)
                                    for d_jk in dates_reelles_jk:
                                        # IMPORTANT : On utilise "JK" comme nom de poste court
                                        planning_final.append([d_jk, "JK", elu['Medecin'], 8])
                                        heures_reelles[elu['Medecin']] += 8
                                    jk_hist.append(elu['Medecin'])
                                else:
                                    if c_jk: # S'il y avait des candidats mais tous occupés
                                        st.error(f"Semaine du {d_str} : Les médecins JK ont des OFF qui bloquent la semaine.")
                                    for d_jk in dates_reelles_jk:
                                        planning_final.append([d_jk, "JK", "⚠️ VIDE", 0])

                            # --- B. DARYUSH VALADI (JM FIXE) ---
                            nom_dv = "Daryush Valadi"
                            is_sem_A = (date_c.isocalendar()[1] % 2 == 0)
                            jours_dv = [1, 2, 3] if is_sem_A else [2, 3, 4]
                            
                            if date_c.weekday() in jours_dv and not is_rouge:
                                # Priorité à JK : si JK occupe déjà la journée, Daryush ne se met pas en JM
                                if f"{nom_dv}_{d_str}" not in absences and not any(p[0]==d_str and p[1]=="JK" for p in planning_final):
                                    planning_final.append([d_str, "JM", nom_dv, 8])
                                    heures_reelles[nom_dv] += 8

                            # --- C. JM (COMPLÉMENT) ---
                            if not is_rouge and not any(p[0]==d_str and p[1] in ["JK", "JM"] for p in planning_final):
                                c_jm = [m for m in meds if m['Medecin'] != nom_dv and regles.get(m['Medecin'], {}).get('Autorise_Kennedy') == 'OUI' and not any(p[0] == d_str and p[2] == m['Medecin'] for p in planning_final) and f"{m['Medecin']}_{d_str}" not in absences and check_fatigue(m['Medecin'], date_c)]
                                if c_jm:
                                    elu = select_best_candidate(c_jm)
                                    planning_final.append([d_str, "JM", elu['Medecin'], 8])
                                    heures_reelles[elu['Medecin']] += 8

                            # --- D. GARDES GM (7j/7) ---
                            exclus_gm = [nom_dv, "Christian Davin", "Elisa Mastrodicasa", "Raouf Sheta"]
                            c_gm = [m for m in meds if m['Medecin'] not in exclus_gm]
                            cands_gm = [m for m in c_gm if not any(p[0] == d_str and p[2] == m['Medecin'] for p in planning_final) and f"{m['Medecin']}_{d_str}" not in absences and check_fatigue(m['Medecin'], date_c)]
                            if cands_gm:
                                elu = select_best_candidate(cands_gm)
                                planning_final.append([d_str, "GM", elu['Medecin'], 24])
                                heures_reelles[elu['Medecin']] += 24
                                if is_rouge: rouges_reels[elu['Medecin']] += 1
                            else: planning_final.append([d_str, "GM", "⚠️ VIDE", 0])

                            # --- E. GARDES GW (7j/7) ---
                            c_gw = [m for m in meds if m['Medecin'] != nom_dv]
                            cands_gw = [m for m in c_gw if not any(p[0] == d_str and p[2] == m['Medecin'] for p in planning_final) and f"{m['Medecin']}_{d_str}" not in absences and check_fatigue(m['Medecin'], date_c)]
                            if cands_gw:
                                elu = select_best_candidate(cands_gw)
                                planning_final.append([d_str, "GW", elu['Medecin'], 24])
                                heures_reelles[elu['Medecin']] += 24
                                if is_rouge: rouges_reels[elu['Medecin']] += 1
                            else: planning_final.append([d_str, "GW", "⚠️ VIDE", 0])

                    # 4. ENVOI VERS GOOGLE SHEETS
                    df_res = pd.DataFrame(planning_final, columns=["Date", "Poste", "Medecin", "Heures"])
                    ws = get_gsheet().worksheet("Planning")
                    ws.clear()
                    ws.append_row(["Date", "Poste", "Medecin", "Heures"])
                    ws.append_rows(df_res.values.tolist())
                    st.success("Planning généré avec succès !")
                    st.balloons()
