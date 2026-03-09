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
    menu_options = ["📅 Mes Désiderata", "📊 Planning Global", "🚀 Admin","⚖️ Bilan Équité", "Déconnexion"]
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
                    # On nettoie les noms des clés du dictionnaire pour éviter les erreurs d'espaces
                    regles = {k.strip(): v for k, v in df_r.set_index('Medecin').to_dict('index').items()}
                    absences = set(df_d['Medecin'].str.strip() + "_" + df_d['Date_OFF']) if not df_d.empty else set()
                    feries = ["2026-04-06", "2026-05-01", "2026-05-14", "2026-05-25", "2026-07-21", "2026-08-15"]
                    
                    planning_final = []
                    heures_reelles = {m['Medecin'].strip(): 0.0 for m in meds}
                    rouges_reels = {m['Medecin'].strip(): 0 for m in meds}

                    def select_best_candidate(candidats):
                        if not candidats: return None
                        # On compare les ratios d'heures pour l'équité
                        return min(candidats, key=lambda m: (heures_reelles[m['Medecin'].strip()]/m['ETP']) + (rouges_reels[m['Medecin'].strip()]/m['ETP']))

                    def check_fatigue(nom, date_obj):
                        hier = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
                        if any(p[0] == hier and p[2] == nom.strip() for p in planning_final): return False
                        return True

                    # 3. BOUCLE TEMPORELLE (Une seule fois !)
                    for mois in range(4, 9):
                        jours = calendar.monthrange(2026, mois)[1]
                        for j in range(1, jours + 1):
                            date_c = datetime(2026, mois, j)
                            d_str = date_c.strftime("%Y-%m-%d")
                            is_rouge = (date_c.weekday() >= 5 or d_str in feries)
                            
                            # --- A. DARYUSH VALADI (PRIORITÉ JM) ---
                            nom_dv = "Daryush Valadi"
                            is_sem_A = (date_c.isocalendar()[1] % 2 == 0)
                            jours_dv = [1, 2, 3] if is_sem_A else [2, 3, 4]
                            
                            daryush_present = False
                            if date_c.weekday() in jours_dv and not is_rouge:
                                if f"{nom_dv}_{d_str}" not in absences:
                                    planning_final.append([d_str, "JM", nom_dv, 8])
                                    heures_reelles[nom_dv] += 8
                                    daryush_present = True

                            # --- B. PF LATERRE (Remplaçant JM si Daryush absent) ---
                            nom_pf = "PF Laterre"
                            if not is_rouge and not daryush_present:
                                if f"{nom_pf}_{d_str}" not in absences and check_fatigue(nom_pf, date_c):
                                    planning_final.append([d_str, "JM", nom_pf, 8])
                                    heures_reelles[nom_pf] += 8

                            # --- C. KENNEDY (BLOC SEMAINE) ---
                            if date_c.weekday() == 0:
                                jours_theo = [0, 1, 2, 4]
                                dates_reelles_jk = [(date_c + timedelta(days=d)).strftime("%Y-%m-%d") for d in jours_theo if (date_c + timedelta(days=d)).strftime("%Y-%m-%d") not in feries]
                                c_jk = [m for m in meds if str(regles.get(m['Medecin'].strip(), {}).get('Autorise_Kennedy', '')).strip().upper() == 'OUI']
                                dispos = [m for m in c_jk if all(f"{m['Medecin'].strip()}_{d}" not in absences for d in dates_reelles_jk) and check_fatigue(m['Medecin'], date_c)]
                                if dispos:
                                    date_limite = date_c - timedelta(weeks=6)
                                    dispos_frais = [m for m in dispos if not any(p[1] == "JK" and p[2] == m['Medecin'].strip() and datetime.strptime(p[0], "%Y-%m-%d") > date_limite for p in planning_final)]
                                    elu = select_best_candidate(dispos_frais if dispos_frais else dispos)
                                    if elu:
                                        for d_jk in dates_reelles_jk:
                                            # On n'écrase pas le JM de Daryush ou PF
                                            if not any(p[0] == d_jk and p[1] == "JM" for p in planning_final):
                                                planning_final.append([d_jk, "JK", elu['Medecin'].strip(), 8])
                                                heures_reelles[elu['Medecin'].strip()] += 8

                            # --- D. GARDES GM (7j/7) ---
                            # Exclusion STRICTE (stripping des noms pour éviter les erreurs d'espaces)
                            exclus_gm = [nom_dv, "Christian Davin", "Elisa Mastrodicasa", "Raouf Sheta"]
                            cands_gm = [
                                m for m in meds if m['Medecin'].strip() not in exclus_gm and 
                                f"{m['Medecin'].strip()}_{d_str}" not in absences and 
                                check_fatigue(m['Medecin'].strip(), date_c) and
                                not any(p[0] == d_str and p[2] == m['Medecin'].strip() for p in planning_final)
                            ]
                            elu_gm = select_best_candidate(cands_gm)
                            if elu_gm:
                                planning_final.append([d_str, "GM", elu_gm['Medecin'].strip(), 24])
                                heures_reelles[elu_gm['Medecin'].strip()] += 24
                                if is_rouge: rouges_reels[elu_gm['Medecin'].strip()] += 1
                            else:
                                planning_final.append([d_str, "GM", "⚠️ VIDE", 0])

                            # --- E. GARDES GW (7j/7) ---
                            cands_gw = [
                                m for m in meds if m['Medecin'].strip() != nom_dv and 
                                f"{m['Medecin'].strip()}_{d_str}" not in absences and 
                                check_fatigue(m['Medecin'].strip(), date_c) and
                                not any(p[0] == d_str and p[2] == m['Medecin'].strip() for p in planning_final)
                            ]
                            elu_gw = select_best_candidate(cands_gw)
                            if elu_gw:
                                planning_final.append([d_str, "GW", elu_gw['Medecin'].strip(), 24])
                                heures_reelles[elu_gw['Medecin'].strip()] += 24
                                if is_rouge: rouges_reels[elu_gw['Medecin'].strip()] += 1
                            else:
                                planning_final.append([d_str, "GW", "⚠️ VIDE", 0])

                    # 4. ENVOI VERS GOOGLE SHEETS
                    df_res = pd.DataFrame(planning_final, columns=["Date", "Poste", "Medecin", "Heures"])
                    ws = get_gsheet().worksheet("Planning")
                    ws.clear()
                    ws.append_row(["Date", "Poste", "Medecin", "Heures"])
                    ws.append_rows(df_res.values.tolist())
                    st.success("Planning généré avec succès !")
                    st.balloons()
    elif choix == "⚖️ Bilan Équité":
        st.header("Analyse de l'Équité et de la Charge")
        
        df_p = read_sheet("Planning")
        df_u = read_sheet("Users")
        
        if df_p.empty or df_u.empty:
            st.warning("⚠️ Aucune donnée disponible. Générez d'abord le planning.")
        else:
            # 1. Nettoyage strict des colonnes de base
            df_u['Medecin'] = df_u['Medecin'].astype(str).str.strip()
            df_p['Medecin'] = df_p['Medecin'].astype(str).str.strip()
            
            # Conversion forcée de l'ETP (Gestion des virgules et erreurs)
            df_u['ETP_Num'] = pd.to_numeric(df_u['ETP'].astype(str).str.replace(',', '.'), errors='coerce').fillna(1.0)
            df_u.loc[df_u['ETP_Num'] <= 0, 'ETP_Num'] = 1.0 # Éviter division par zéro

            # 2. Agrégation des Heures (On s'assure que Heures est numérique)
            df_p['Heures_Num'] = pd.to_numeric(df_p['Heures'], errors='coerce').fillna(0)
            stats_h = df_p.groupby('Medecin')['Heures_Num'].sum().reset_index()
            stats_h.columns = ['Medecin', 'Total_Heures']
            
            # 3. Calcul des Jours Rouges
            feries = ["2026-04-06", "2026-05-01", "2026-05-14", "2026-05-25", "2026-07-21", "2026-08-15"]
            df_p['is_rouge'] = df_p['Date'].apply(lambda d: pd.to_datetime(d).weekday() >= 5 or str(d) in feries)
            stats_r = df_p[df_p['is_rouge']].groupby('Medecin')['Date'].nunique().reset_index()
            stats_r.columns = ['Medecin', 'Jours Rouges']
            
            # 4. Fusion des données
            bilan = pd.merge(df_u[['Medecin', 'ETP_Num']], stats_h, on='Medecin', how='left')
            bilan = pd.merge(bilan, stats_r, on='Medecin', how='left')
            
            # Remplacement final des NaN par 0 avant calcul
            bilan['Total_Heures'] = bilan['Total_Heures'].fillna(0)
            bilan['Jours Rouges'] = bilan['Jours Rouges'].fillna(0)

            # 5. Calcul de la Charge (Calcul sécurisé)
            # On utilise .to_numpy() pour éviter les problèmes de types de Series
            h = bilan['Total_Heures'].to_numpy(dtype=float)
            e = bilan['ETP_Num'].to_numpy(dtype=float)
            bilan['Charge Relative (%)'] = (h / (e * 800)) * 100

            # --- AFFICHAGE ---
            col1, col2, col3 = st.columns(3)
            col1.metric("Moyenne", f"{int(bilan['Total_Heures'].mean())}h")
            col2.metric("Max Week-ends", f"{int(bilan['Jours Rouges'].max())}")
            col3.metric("Effectif", f"{len(df_u)}")

            st.dataframe(
                bilan.style.background_gradient(subset=['Total_Heures'], cmap="OrRd")
                .format({
                    'ETP_Num': '{:.2f}', 
                    'Total_Heures': '{:.0f}h', 
                    'Jours Rouges': '{:.0f}', 
                    'Charge Relative (%)': '{:.1f}%'
                }),
                use_container_width=True
            )

            st.bar_chart(data=bilan, x="Medecin", y="Total_Heures")
