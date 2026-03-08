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
                    ds = f"2026-{str(mo).zfill(2)}-{str(j).zfill(2)}"
                    if cols[i].button(str(j) + (" ❌" if ds in c_o else " ✅"), key=ds):
                        if ds in c_o: df_o = df_o[~((df_o["Medecin"]==st.session_state.u)&(df_o["Date_OFF"]==ds))]
                        else: df_o = pd.concat([df_o, pd.DataFrame([{"Medecin":st.session_state.u,"Date_OFF":ds}])])
                        sd(df_o, OF); st.rerun()

    # 2. ÉCHANGES
    elif label_echange in sel:
        st.header("Centre d'échanges")
        if nb_notif > 0:
            st.subheader("📬 Demandes reçues")
            for idx, row in mes_demandes.iterrows():
                with st.expander(f"Demande de {row['Emetteur']} : {row['Date']}"):
                    if st.button("✅ Accepter", key=f"acc_{idx}"):
                        df_p = gd(LP).set_index("Unnamed: 0")
                        df_p.at[row['Date'], row['Poste']] = st.session_state.u
                        df_p.reset_index().to_csv(LP, index=False)
                        df_e.at[idx, "Statut"] = "VALIDE"
                        sd(df_e, ECH); st.success("Validé !"); st.rerun()
                    if st.button("❌ Refuser", key=f"ref_{idx}"):
                        df_e.at[idx, "Statut"] = "REFUSE"
                        sd(df_e, ECH); st.rerun()
        
        st.divider()
        st.subheader("📤 Envoyer une proposition")
        if os.path.exists(LP):
            df_p = gd(LP).set_index("Unnamed: 0")
            mes_g = [f"{d} | {p}" for d in df_p.index for p in df_p.columns if df_p.at[d, p] == st.session_state.u]
            g_sel = st.selectbox("Ma garde", mes_g)
            dest = st.selectbox("Remplaçant", [m for m in MDS.keys() if m != st.session_state.u])
            if st.button("Proposer l'échange"):
                dt_s, p_s = g_sel.split(" | ")
                new_r = pd.DataFrame([{"Emetteur": st.session_state.u, "Destinataire": dest, "Date": dt_s, "Poste": p_s, "Statut": "ATTENTE"}])
                sd(pd.concat([df_e, new_r]), ECH); st.info("Demande envoyée !")
        else: st.info("Planning non publié.")

    # 3. CHANGEMENT DE MOT DE PASSE (CORRIGÉ)
    elif sel == "🔑 Changement de mot de passe":
        st.header("Sécurisez votre compte")
        st.write(f"Utilisateur actuel : **{st.session_state.u}**")
        nouveau_mdp = st.text_input("Entrez votre nouveau mot de passe", type="password")
        confirmation = st.text_input("Confirmez le mot de passe", type="password")
        
        if st.button("Enregistrer le nouveau mot de passe"):
            if nouveau_mdp == "":
                st.warning("Le mot de passe ne peut pas être vide.")
            elif nouveau_mdp != confirmation:
                st.error("Les mots de passe ne correspondent pas.")
            else:
                u_df = gd(DB)
                u_df.loc[u_df["Medecin"] == st.session_state.u, "MDP"] = nouveau_mdp
                sd(u_df, DB)
                st.success("Mot de passe mis à jour avec succès !")

    # 4. ADMIN
    elif sel == "🚀 Admin":
        st.header("Espace Administrateur")
        if st.button("🔄 Lancer la génération du planning"):
            # (Ici on utiliserait la fonction run_gen définie en V9)
            st.warning("Le moteur de calcul se lance ici...")

    # 5. SORTIE
    elif sel == "Sortie":
        del st.session_state.u
        st.rerun()