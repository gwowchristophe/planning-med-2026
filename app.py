import streamlit as st
import pandas as pd
import os, calendar
from datetime import date, timedelta
import holidays

# --- CONFIGURATION ---
st.set_page_config(page_title="Planning Médical 2026", layout="wide")
V = {"GW": 24, "GM": 24, "JK": 9, "JM": 7}
DB, OF, LP, ECH = "users_db.csv", "desiderata_db.csv", "last_plan.csv", "echanges_db.csv"
BH = holidays.BE(years=2026)
FR_D = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

MDS = {
    "Alexandra Warnant": {"e": 0.8, "j": 1, "t": 0}, "Alfredo Vieira": {"e": 0.8, "j": 1, "t": 0},
    "Camie Dupuis": {"e": 0.8, "j": 1, "t": 0}, "Christian Davin": {"e": 0.8, "j": 0, "t": 1},
    "Christophe Angelo": {"e": 0.6, "j": 1, "t": 0}, "Daryush Valadi": {"e": 0.4, "j": 0, "t": 0},
    "Elisa Mastrodiscasa": {"e": 0.8, "j": 0, "t": 1}, "Gauthier Nendumba": {"e": 0.8, "j": 1, "t": 0},
    "Julie Henrie": {"e": 0.6, "j": 1, "t": 0}, "Martin Hachez": {"e": 0.8, "j": 1, "t": 0},
    "PF Laterre": {"e": 0.8, "j": 0, "t": 0}, "Raouf Sheta": {"e": 0.8, "j": 0, "t": 1},
    "Simon Van Migem": {"e": 0.8, "j": 1, "t": 0}
}

# --- INITIALISATION ---
def init_files():
    if not os.path.exists(DB):
        pd.DataFrame({"Medecin": list(MDS.keys()), "MDP": ["Doudoudragon"]*13}).to_csv(DB, index=False)
    if not os.path.exists(OF):
        pd.DataFrame(columns=["Medecin", "Date_OFF"]).to_csv(OF, index=False)
    if not os.path.exists(ECH):
        pd.DataFrame(columns=["Emetteur", "Destinataire", "Date", "Poste", "Statut"]).to_csv(ECH, index=False)

init_files()
def gd(f): return pd.read_csv(f)
def sd(df, f): df.to_csv(f, index=False)

# --- INTERFACE ---
if 'u' not in st.session_state:
    st.title("🏥 Planning Médical 2026")
    u_s = st.selectbox("Sélectionnez votre nom", list(MDS.keys()))
    pw = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        u_df = gd(DB)
        if pw == str(u_df.loc[u_df["Medecin"]==u_s, "MDP"].values[0]):
            st.session_state.u = u_s
            st.rerun()
        else: st.error("Mot de passe incorrect")
else:
    df_e = gd(ECH)
    mes_demandes = df_e[(df_e["Destinataire"] == st.session_state.u) & (df_e["Statut"] == "ATTENTE")]
    nb_notif = len(mes_demandes)
    
    label_echange = f"🔄 Échanges ({nb_notif})" if nb_notif > 0 else "🔄 Échanges"
    mn = ["📅 Désiderata de congé", label_echange, "🚀 Admin", "🔑 Changement de mot de passe", "Sortie"]
    if st.session_state.u != "Christophe Angelo": mn.remove("🚀 Admin")
    sel = st.sidebar.radio("Navigation", mn)

    # 1. DÉSIDERATA
    if sel == "📅 Désiderata de congé":
        st.header("Gestion des congés")
        mo = st.selectbox("Mois", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
        df_o = gd(OF)
        c_o = set(df_o[df_o["Medecin"]==st.session_state.u]["Date_OFF"].tolist())
        for s in calendar.monthcalendar(2026, mo):
            cols = st.columns(7)
            for i, j in enumerate(s):
                if j != 0:
                    ds = f"2026-{str(mo).zfill(2)}-{str(j