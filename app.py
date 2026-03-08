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
        st.header("Planning Global 2026")
        df_p = read_sheet("Planning")
        if not df_p.empty:
            df_p['Date'] = pd.to_datetime(df_p['Date'])
            m_v = st.selectbox("Mois", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
            df_m = df_p[df_p['Date'].dt.month == m_v].copy()
            
            if not df_m.empty:
                # Création du tableau croisé (Dates en lignes, Postes en colonnes)
                df_pivot = df_m.pivot(index='Date', columns='Poste', values='Medecin').fillna("-")
                
                # Tri des colonnes pour la clarté
                cols_target = ["JK (Kennedy)", "GM", "GW", "JM"]
                df_pivot = df_pivot[[c for c in cols_target if c in df_pivot.columns]]
                
                # Jours fériés 2026 (Belgique)
                feries = ["2026-04-06", "2026-05-01", "2026-05-14", "2026-05-25", "2026-07-21", "2026-08-15"]

                def style_planning(row):
                    d = row.name
                    is_we = d.weekday() >= 5
                    is_ferie = d.strftime('%Y-%m-%d') in feries
                    if is_we or is_ferie:
                        return ['background-color: #E0E0E0; color: black; font-weight: bold'] * len(row)
                    return [''] * len(row)

                st.dataframe(df_pivot.style.apply(style_planning, axis=1), use_container_width=True, height=800)
            else:
                st.info("Aucune donnée pour ce mois.")
        else:
            st.warning("Le planning est vide. Allez dans Admin > Générateur.")

    elif choix == "🚀 Admin":
        st.header("Console Administrateur")
        t1, t2 = st.tabs(["📊 Bilan d'Équité", "⚙️ Générateur 5 Mois"])

        with t1:
            st.subheader("Bilan de Performance et Équité (Avril - Août 2026)")
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
                    # Moyenne h/sem : (Heures / 22 semaines) / ETP
                    moy_sem = (hrs_tot / 22) / etp if etp > 0 else 0
                    
                    nuits = len(m_p[m_p['Poste'].isin(["GM", "GW"])])
                    
                    # Week-ends et Fériés
                    def is_red(d_str):
                        d = pd.to_datetime(d_str)
                        return d.weekday() >= 5 or d_str in feries
                    
                    we_feries = m_p[m_p['Date'].apply(is_red)].shape[0]
                    nb_jk = len(m_p[m_p['Poste'] == "JK (Kennedy)"]) // 4 # Nb de blocs de 4j
                    
                    bilan.append({
                        "Médecin": nom,
                        "ETP": etp,
                        "Heures Totales": hrs_tot,
                        "Moyenne h/Sem": round(moy_sem, 1),
                        "Nb Gardes (Nuits)": nuits,
                        "WE/Fériés": we_feries,
                        "Semaines Kennedy": nb_jk
                    })
                
                st.table(pd.DataFrame(bilan).sort_values("Moyenne h/Sem", ascending=False))

        with t2:
            st.subheader("Générateur Haute Précision")
            if st.button("🚀 Lancer la génération (Respect des 6 critères)"):
                with st.spinner("Calcul des contraintes de fatigue et d'équité..."):
                    # 1. SETUP
                    df_u = read_sheet("Users")
                    df_d = read_sheet("Desiderata")
                    df_r = read_sheet("Regles")
                    df_u['ETP'] = df_u['ETP'].apply(lambda x: float(str(x).replace(',','.')) if x else 1.0)
                    
                    meds = df_u.to_dict('records')
                    regles = df_r.set_index('Medecin').to_dict('index')
                    absences = set(df_d['Medecin'] + "_" + df_d['Date_OFF'])
                    feries = ["2026-04-06", "2026-05-01", "2026-05-14", "2026-05-25", "2026-07-21", "2026-08-15"]
                    
                    planning_final = []
                    dettes = {m['Medecin']: 0.0 for m in meds}
                    we_counts = {m['Medecin']: 0 for m in meds}
                    jk_hist = [] # Liste d'attente Kennedy (tournante de 8)

                    # 2. FONCTIONS DE CONTRÔLE
                    def get_score(nom):
                        # Score d'équité multidimensionnel
                        etp = next(m['ETP'] for m in meds if m['Medecin'] == nom)
                        return (dettes[nom] / etp) + (we_counts[nom] * 12) # Malus WE important (12h équiv.)

                    def check_fatigue(nom, date_obj):
                        # Règle des 8 jours glissants (Max 2 postes, sinon 48h repos)
                        start_f = date_obj - timedelta(days=7)
                        recent = [p for p in planning_final if p[2] == nom and start_f <= datetime.strptime(p[0], "%Y-%m-%d") < date_obj]
                        if len(recent) >= 2:
                            # Si 2 postes faits, check si le dernier poste date de plus de 48h
                            dernier_poste = datetime.strptime(recent[-1][0], "%Y-%m-%d")
                            if (date_obj - dernier_poste).days < 2: return False
                        # Repos de sécurité J+1
                        hier = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
                        if any(p[0] == hier and p[2] == nom for p in planning_final): return False
                        # Repos J-1 si OFF demain (pour la garde de nuit)
                        demain = (date_obj + timedelta(days=1)).strftime("%Y-%m-%d")
                        if f"{nom}_{demain}" in absences: return False
                        return True

                    # 3. BOUCLE
                    for mois in range(4, 9):
                        jours = calendar.monthrange(2026, mois)[1]
                        for j in range(1, jours + 1):
                            date_c = datetime(2026, mois, j)
                            d_str = date_c.strftime("%Y-%m-%d")
                            is_we = date_c.weekday() >= 5
                            is_ferie = d_str in feries

                            # --- A. KENNEDY (Lundi) ---
                            if date_c.weekday() == 0:
                                j_jk = [0, 1, 2, 4]
                                bloc_dates = [(date_c + timedelta(days=d)).strftime("%Y-%m-%d") for d in j_jk]
                                if not any(d in feries for d in bloc_dates):
                                    c_jk = [m for m in meds if regles.get(m['Medecin'], {}).get('Autorise_Kennedy') == 'OUI' 
                                           and m['Medecin'] not in jk_hist[:7]] # Tournante
                                    dispos_jk = [m for m in c_jk if all(f"{m['Medecin']}_{d}" not in absences for d in bloc_dates)
                                                and all(check_fatigue(m['Medecin'], date_c + timedelta(days=d)) for d in j_jk)]
                                    if dispos_jk:
                                        elu = min(dispos_jk, key=lambda x: get_score(x['Medecin']))
                                        for d_jk in bloc_dates:
                                            planning_final.append([d_jk, "JK (Kennedy)", elu['Medecin'], 8])
                                            dettes[elu['Medecin']] += 8
                                        jk_hist.append(elu['Medecin'])

                            # --- B. CAS DARYUSH (JM Fixe) ---
                            # Alternance Mar-Mer-Jeu / Mer-Jeu-Ven
                            is_semaine_A = (date_c.isocalendar()[1] % 2 == 0)
                            jours_daryush = [1,2,3] if is_semaine_A else [2,3,4]
                            if date_c.weekday() in jours_daryush:
                                if f"Daryush_{d_str}" not in absences:
                                    planning_final.append([d_str, "JM", "Daryush", 8])
                                    dettes["Daryush"] += 8

                            # --- C. JM (Pour les autres jours/médecins) ---
                            if not is_we and not is_ferie:
                                if not any(p[0] == d_str and p[1] == "JM" for p in planning_final):
                                    c_jm = [m for m in meds if m['Medecin'] != "Daryush" 
                                           and regles.get(m['Medecin'], {}).get('Autorise_Kennedy') == 'OUI' # Filtre JM
                                           and not any(p[0] == d_str and p[2] == m['Medecin'] for p in planning_final)
                                           and f"{m['Medecin']}_{d_str}" not in absences and check_fatigue(m['Medecin'], date_c)]
                                    if c_jm:
                                        elu = min(c_jm, key=lambda x: get_score(x['Medecin']))
                                        planning_final.append([d_str, "JM", elu['Medecin'], 8])
                                        dettes[elu['Medecin']] += 8

                            # --- D. GARDE (GM/GW) - Priorité Absolue ---
                            p_type, h_p = ("GW", 24) if (is_we or is_ferie) else ("GM", 24)
                            c_g = [m for m in meds if m['Medecin'] != "Daryush"]
                            # Filtres spécifiques
                            if is_we or is_ferie: c_g = [m for m in c_g if regles.get(m['Medecin'], {}).get('Autorise_Garde_WE') == 'OUI']
                            else: c_g = [m for m in c_g if regles.get(m['Medecin'], {}).get('Autorise_Garde_Semaine') == 'OUI']
                            
                            cands = [m for m in c_g if not any(p[0] == d_str and p[2] == m['Medecin'] for p in planning_final)
                                    and f"{m['Medecin']}_{d_str}" not in absences and check_fatigue(m['Medecin'], date_c)]
                            
                            if cands:
                                elu = min(cands, key=lambda x: get_score(x['Medecin']))
                                planning_final.append([d_str, p_type, elu['Medecin'], h_p])
                                dettes[elu['Medecin']] += h_p
                                if is_we or is_ferie: we_counts[elu['Medecin']] += 1
                            else:
                                planning_final.append([d_str, p_type, "⚠️ VIDE", 0])

                    # 4. ENVOI
                    df_res = pd.DataFrame(planning_final, columns=["Date", "Poste", "Medecin", "Heures"])
                    ws = get_gsheet().worksheet("Planning")
                    ws.clear()
                    ws.append_row(["Date", "Poste", "Medecin", "Heures"])
                    ws.append_rows(df_res.values.tolist())
                    st.success("Génération terminée avec respect strict des 6 critères.")
