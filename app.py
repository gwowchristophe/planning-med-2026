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
    else: st.warning("Vérifiez l'onglet 'Users' sur Google Sheets.")

# --- 3. INTERFACE ---
else:
    st.sidebar.success(f"Dr. {st.session_state.u}")
    menu_options = ["📅 Mes Désiderata", "📊 Planning Global", "🚀 Admin","⚖️ Bilan Équité", "Déconnexion"]
    if st.session_state.u != "Christophe Angelo":
        menu_options.remove("🚀 Admin")
    
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
        st.header("Planning Mensuel")
        df_p = read_sheet("Planning")
        if not df_p.empty:
            m_sel = st.selectbox("Mois", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
            df_p['Date_DT'] = pd.to_datetime(df_p['Date'])
            df_view = df_p[df_p['Date_DT'].dt.month == m_sel].copy()
            
            if not df_view.empty:
                df_pivot = df_view.pivot_table(index='Date', columns='Poste', values='Medecin', aggfunc='first').reset_index()
                for col in ["Date", "JM", "GM", "GW", "JK"]:
                    if col not in df_pivot.columns: df_pivot[col] = "-"
                
                df_pivot = df_pivot[["Date", "JM", "GM", "GW", "JK"]]
                
                def style_p(row):
                    d = pd.to_datetime(row['Date'])
                    f = ["2026-04-06", "2026-05-01", "2026-05-14", "2026-05-25", "2026-07-21", "2026-08-15"]
                    if d.weekday() >= 5 or row['Date'] in f: return ['background-color: #fff2f2'] * len(row)
                    return [''] * len(row)

                st.dataframe(df_pivot.style.apply(style_p, axis=1), use_container_width=True, height=700)
        else: st.info("Le planning est vide.")

    elif choix == "🚀 Admin":
        st.header("Console Administrateur")
        if st.button("🚀 Lancer la génération (Avril - Août 2026)"):
            with st.spinner("Application des règles métier..."):
                df_u = read_sheet("Users")
                df_d = read_sheet("Desiderata")
                df_r = read_sheet("Regles")
                
                df_u['ETP'] = df_u['ETP'].apply(lambda x: float(str(x).replace(',','.')) if x else 1.0)
                meds = df_u.to_dict('records')
                regles = {k.strip(): v for k, v in df_r.set_index('Medecin').to_dict('index').items()}
                absences = set(df_d['Medecin'].str.strip() + "_" + df_d['Date_OFF']) if not df_d.empty else set()
                feries = ["2026-04-06", "2026-05-01", "2026-05-14", "2026-05-25", "2026-07-21", "2026-08-15"]
                
                planning_final = []
                heures_reelles = {m['Medecin'].strip(): 0.0 for m in meds}
                rouges_reels = {m['Medecin'].strip(): 0 for m in meds}

                def select_best(cands):
                    if not cands: return None
                    return min(cands, key=lambda m: (heures_reelles[m['Medecin'].strip()]/m['ETP']) + (rouges_reels[m['Medecin'].strip()]/m['ETP']))

                def check_fatigue(nom, date_obj):
                    hier = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
                    return not any(p[0] == hier and p[2] == nom.strip() and p[1] in ["GM", "GW"] for p in planning_final)

                for mois in range(4, 9):
                    for j in range(1, calendar.monthrange(2026, mois)[1] + 1):
                        date_c = datetime(2026, mois, j)
                        d_str = date_c.strftime("%Y-%m-%d")
                        is_rouge = (date_c.weekday() >= 5 or d_str in feries)
                        
                        # A. JM (Daryush / PF Laterre)
                        nom_dv = "Daryush Valadi"
                        nom_pf = "PF Laterre"
                        sem_A = (date_c.isocalendar()[1] % 2 == 0)
                        jours_dv = [1, 2, 3] if sem_A else [2, 3, 4]
                        
                        pris_jm = False
                        if date_c.weekday() in jours_dv and not is_rouge and f"{nom_dv}_{d_str}" not in absences:
                            planning_final.append([d_str, "JM", nom_dv, 8])
                            heures_reelles[nom_dv] += 8
                            pris_jm = True
                        elif not is_rouge and f"{nom_pf}_{d_str}" not in absences and check_fatigue(nom_pf, date_c):
                            planning_final.append([d_str, "JM", nom_pf, 8])
                            heures_reelles[nom_pf] += 8

                        # B. Kennedy
                        if date_c.weekday() == 0:
                            jours_jk = [0, 1, 2, 4]
                            dates_jk = [(date_c + timedelta(days=d)).strftime("%Y-%m-%d") for d in jours_jk if (date_c + timedelta(days=d)).strftime("%Y-%m-%d") not in feries]
                            c_jk = [m for m in meds if str(regles.get(m['Medecin'].strip(), {}).get('Autorise_Kennedy', '')).strip().upper() == 'OUI']
                            dispos = [m for m in c_jk if all(f"{m['Medecin'].strip()}_{d}" not in absences for d in dates_jk) and check_fatigue(m['Medecin'], date_c)]
                            if dispos:
                                date_limite = date_c - timedelta(weeks=6)
                                frais = [m for m in dispos if not any(p[1] == "JK" and p[2] == m['Medecin'].strip() and datetime.strptime(p[0], "%Y-%m-%d") > date_limite for p in planning_final)]
                                elu = select_best(frais if frais else dispos)
                                if elu:
                                    for d_jk in dates_jk:
                                        if not any(p[0] == d_jk and p[1] == "JM" for p in planning_final):
                                            planning_final.append([d_jk, "JK", elu['Medecin'].strip(), 8])
                                            heures_reelles[elu['Medecin'].strip()] += 8

                        # C. Gardes GM (Exclusions)
                        excl = [nom_dv, "Christian Davin", "Elisa Mastrodicasa", "Raouf Sheta"]
                        c_gm = [m for m in meds if m['Medecin'].strip() not in excl and f"{m['Medecin'].strip()}_{d_str}" not in absences and check_fatigue(m['Medecin'].strip(), date_c) and not any(p[0] == d_str and p[2] == m['Medecin'].strip() for p in planning_final)]
                        elu_gm = select_best(c_gm)
                        if elu_gm:
                            planning_final.append([d_str, "GM", elu_gm['Medecin'].strip(), 24])
                            heures_reelles[elu_gm['Medecin'].strip()] += 24
                            if is_rouge: rouges_reels[elu_gm['Medecin'].strip()] += 1
                        else: planning_final.append([d_str, "GM", "⚠️ VIDE", 0])

                        # D. Gardes GW
                        c_gw = [m for m in meds if m['Medecin'].strip() != nom_dv and f"{m['Medecin'].strip()}_{d_str}" not in absences and check_fatigue(m['Medecin'].strip(), date_c) and not any(p[0] == d_str and p[2] == m['Medecin'].strip() for p in planning_final)]
                        elu_gw = select_best(c_gw)
                        if elu_gw:
                            planning_final.append([d_str, "GW", elu_gw['Medecin'].strip(), 24])
                            heures_reelles[elu_gw['Medecin'].strip()] += 24
                            if is_rouge: rouges_reels[elu_gw['Medecin'].strip()] += 1
                        else: planning_final.append([d_str, "GW", "⚠️ VIDE", 0])

                df_res = pd.DataFrame(planning_final, columns=["Date", "Poste", "Medecin", "Heures"])
                ws = get_gsheet().worksheet("Planning")
                ws.clear()
                ws.append_row(["Date", "Poste", "Medecin", "Heures"])
                ws.append_rows(df_res.values.tolist())
                st.success("Planning généré !")
                st.balloons()

    elif choix == "⚖️ Bilan Équité":
        st.header("Analyse de l'Équité")
        df_p = read_sheet("Planning")
        df_u = read_sheet("Users")
        if not df_p.empty and not df_u.empty:
            df_u['Medecin'] = df_u['Medecin'].str.strip()
            df_p['Medecin'] = df_p['Medecin'].str.strip()
            df_u['ETP_N'] = pd.to_numeric(df_u['ETP'].astype(str).str.replace(',', '.'), errors='coerce').fillna(1.0)
            df_p['H_N'] = pd.to_numeric(df_p['Heures'], errors='coerce').fillna(0)
            
            stats_h = df_p.groupby('Medecin')['H_N'].sum().reset_index()
            feries = ["2026-04-06", "2026-05-01", "2026-05-14", "2026-05-25", "2026-07-21", "2026-08-15"]
            df_p['is_r'] = df_p['Date'].apply(lambda d: pd.to_datetime(d).weekday() >= 5 or str(d) in feries)
            stats_r = df_p[df_p['is_r']].groupby('Medecin')['Date'].nunique().reset_index()
            
            bilan = pd.merge(df_u[['Medecin', 'ETP_N']], stats_h, on='Medecin', how='left').fillna(0)
            bilan = pd.merge(bilan, stats_r, on='Medecin', how='left').fillna(0)
            bilan.columns = ['Médecin', 'ETP', 'Total Heures', 'Jours Rouges']
            bilan['Charge %'] = (bilan['Total Heures'] / (bilan['ETP'] * 800)) * 100
            
            st.dataframe(bilan.style.format({'ETP': '{:.2f}', 'Total Heures': '{:.0f}h', 'Charge %': '{:.1f}%'}), use_container_width=True)
            st.bar_chart(data=bilan, x="Médecin", y="Total Heures")
