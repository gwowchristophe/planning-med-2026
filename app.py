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

# --- FONCTIONS ---
def gd(f): return pd.read_csv(f) if os.path.exists(f) else pd.DataFrame()
def sd(df, f): df.to_csv(f, index=False)

def check_conflit(name, date_str, pl_df):
    target_dt = pd.to_datetime(date_str).date()
    if name in pl_df.loc[date_str].values: return "Déjà de poste ce jour."
    hier = (target_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    if hier in pl_df.index and name in pl_df.loc[hier].values: return "Repos 24h (garde veille)."
    demain = (target_dt + timedelta(days=1)).strftime("%Y-%m-%d")
    if demain in pl_df.index and name in pl_df.loc[demain].values: return "Repos 24h (garde lendemain)."
    return None

# --- INTERFACE ---
if 'u' not in st.session_state:
    st.title("🏥 Planning Médical 2026")
    u_s = st.selectbox("Médecin", list(MDS.keys()))
    pw = st.text_input("Code", type="password")
    if st.button("Connexion"):
        u_df = gd(DB)
        if not u_df.empty and pw == str(u_df.loc[u_df["Medecin"]==u_s, "MDP"].values[0]):
            st.session_state.u = u_s
            st.rerun()
else:
    # Système de Notification
    df_e = gd(ECH)
    mes_demandes = df_e[(df_e["Destinataire"] == st.session_state.u) & (df_e["Statut"] == "ATTENTE")]
    nb_notif = len(mes_demandes)
    
    label_echange = f"🔄 Échanges ({nb_notif})" if nb_notif > 0 else "🔄 Échanges"
    mn = ["📅 Mes OFF", label_echange, "🚀 Admin", "🔐 Code", "Sortie"]
    if st.session_state.u != "Christophe Angelo": mn.remove("🚀 Admin")
    sel = st.sidebar.radio("Menu", mn)

    if sel == "📅 Mes OFF":
        st.header("Gestion des indisponibilités")
        # [Code calendrier identique...]
        mo = st.selectbox("Mois", [4,5,6,7,8])
        df_o = gd(OF)
        c_o = set(df_o[df_o["Medecin"]==st.session_state.u]["Date_OFF"].tolist())
        for s in calendar.monthcalendar(2026, mo):
            cols = st.columns(7)
            for i, j in enumerate(s):
                if j != 0:
                    ds = f"2026-{str(mo).zfill(2)}-{str(j).zfill(2)}"
                    if cols[i].button(str(j) + (" ❌" if ds in c_o else " ✅"), key=ds):
                        if ds in c_o: df_o = df_o[~((df_o["Medecin"]==st.session_state.u)&(df_o["Date_OFF"]==ds))]
                        else: df_o = pd.concat([df_o, pd.DataFrame([{"Medecin":st.session_state.u,"Date_OFF":ds}])])
                        sd(df_o, OF); st.rerun()

    elif "🔄 Échanges" in sel:
        st.header("Centre d'échanges de gardes")
        
        # Section 1 : Demandes reçues (A VALIDER)
        if nb_notif > 0:
            st.subheader("⚠️ Demandes reçues")
            for idx, row in mes_demandes.iterrows():
                with st.expander(f"Demande de {row['Emetteur']} pour le {row['Date']}"):
                    st.write(f"Poste : **{row['Poste']}**")
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Accepter", key=f"acc_{idx}"):
                        # Maj Planning
                        df_p = gd(LP).set_index("Unnamed: 0")
                        df_p.at[row['Date'], row['Poste']] = st.session_state.u
                        sd(df_p.reset_index(), LP)
                        # Maj Echanges
                        df_e.at[idx, "Statut"] = "VALIDE"
                        sd(df_e, ECH)
                        st.success("Planning mis à jour !")
                        st.rerun()
                    if c2.button("❌ Refuser", key=f"ref_{idx}"):
                        df_e.at[idx, "Statut"] = "REFUSE"
                        sd(df_e, ECH)
                        st.rerun()
        
        st.divider()
        
        # Section 2 : Envoyer une demande
        st.subheader("📤 Proposer un échange")
        if os.path.exists(LP):
            df_p = gd(LP).set_index("Unnamed: 0")
            mes_g = [f"{d} | {p}" for d in df_p.index for p in df_p.columns if df_p.at[d, p] == st.session_state.u]
            g_sel = st.selectbox("Ma garde à donner", mes_g)
            dest = st.selectbox("Remplaçant", [m for m in MDS.keys() if m != st.session_state.u])
            
            if st.button("Envoyer la demande"):
                dt_s, p_s = g_sel.split(" | ")
                conflit = check_conflit(dest, dt_s, df_p)
                if conflit:
                    st.error(f"Impossible : {dest} a un conflit ({conflit})")
                else:
                    new_req = pd.DataFrame([{"Emetteur": st.session_state.u, "Destinataire": dest, "Date": dt_s, "Poste": p_s, "Statut": "ATTENTE"}])
                    sd(pd.concat([df_e, new_req]), ECH)
                    st.info(f"Demande envoyée à {dest}. En attente de sa validation.")
        else:
            st.info("Aucun planning publié.")

    elif sel == "🚀 Admin":
        st.header("Administration Christophe")
        # [Bouton génération et bilan d'équité identique...]
        if st.button("Calculer Planning"):
            # (Appel run_gen...)
            st.success("Généré")
        
        if os.path.exists(LP):
            st.subheader("Historique des échanges validés")
            st.dataframe(df_e[df_e["Statut"] == "VALIDE"])

    elif sel == "Sortie":
        del st.session_state.u
        st.rerun()