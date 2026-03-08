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

# --- INITIALISATION DES FICHIERS (Anti-KeyError) ---
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

def check_conflit(name, date_str, pl_df):
    target_dt = pd.to_datetime(date_str).date()
    if name in pl_df.loc[date_str].values: return "Déjà de poste ce jour."
    hier = (target_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    if hier in pl_df.index and name in pl_df.loc[hier].values: return "Repos 24h (était de garde la veille)."
    demain = (target_dt + timedelta(days=1)).strftime("%Y-%m-%d")
    if demain in pl_df.index and name in pl_df.loc[demain].values: return "Repos 24h (garde le lendemain)."
    return None

# --- MOTEUR DE GÉNÉRATION ---
def run_gen(vo):
    pl, stt = {}, {m: 0 for m in MDS.keys()}
    sq = {m: {"T":0, "WE":0, "JK":0, "G":0} for m in MDS.keys()}
    jk_cand = [m for m in MDS.keys() if MDS[m]["j"] == 1 and m not in ["PF Laterre", "Christian Davin", "Elisa Mastrodiscasa", "Raouf Sheta"]]
    jk_hist, jk_owner = [], None
    ads = [date(2026, m, j) for m in range(4,9) for j in range(1, calendar.monthrange(2026,m)[1]+1)]
    
    for d in ads:
        if d.weekday() == 0: jk_owner = None
        jp = {}
        ds = d.strftime("%Y-%m-%d")
        f, s, di = (d in BH), (d.weekday()==5), (d.weekday()==6)
        is_we = (f or s or di)

        # Kennedy (JK)
        if not is_we and d.weekday() != 3:
            if jk_owner is None:
                pool = [m for m in jk_cand if m not in jk_hist]
                if not pool: jk_hist = []; pool = jk_cand
                pool = sorted(pool, key=lambda x: stt[x]/MDS[x]["e"])
                try:
                    jk_owner = next(m for m in pool if ds not in vo.get(m, []))
                    jk_hist.append(jk_owner)
                except StopIteration: pass
            if jk_owner:
                jp["JK"] = jk_owner
                stt[jk_owner] += V["JK"]
                sq[jk_owner]["JK"] += 1

        # Gardes (GW, GM, JM)
        postes = ["GW", "GM"] + (["JM"] if not is_we else [])
        for p in postes:
            if p in jp: continue
            ml = sorted(list(MDS.keys()), key=lambda x: (stt[x]/MDS[x]["e"]) + (sq[x]["WE"] * 5))
            try:
                c = next(m for m in ml if m not in jp.values() and ds not in vo.get(m, []))
                jp[p], stt[c] = c, stt[c] + V[p]
                if p in ["GW", "GM"]: sq[c]["G"] += 1
                if is_we: sq[c]["WE"] += 1
            except StopIteration: pass
        pl[ds] = jp
    return pl

# --- INTERFACE ---
if 'u' not in st.session_state:
    st.title("🏥 Planning Médical 2026")
    u_s = st.selectbox("Médecin", list(MDS.keys()))
    pw = st.text_input("Code", type="password")
    if st.button("Connexion"):
        u_df = gd(DB)
        if pw == str(u_df.loc[u_df["Medecin"]==u_s, "MDP"].values[0]):
            st.session_state.u = u_s
            st.rerun()
else:
    df_e = gd(ECH)
    # Filtrage sécurisé des demandes
    mes_demandes = df_e[(df_e["Destinataire"] == st.session_state.u) & (df_e["Statut"] == "ATTENTE")]
    nb_notif = len(mes_demandes)
    
    label_echange = f"🔄 Échanges ({nb_notif})" if nb_notif > 0 else "🔄 Échanges"
    mn = ["📅 Mes OFF", label_echange, "🚀 Admin", "🔐 Code", "Sortie"]
    if st.session_state.u != "Christophe Angelo": mn.remove("🚀 Admin")
    sel = st.sidebar.radio("Menu", mn)

    if sel == "📅 Mes OFF":
        st.header("Mes jours OFF")
        mo = st.selectbox("Mois", [4,5,6