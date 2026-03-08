import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta
import holidays

# --- CONFIGURATION ---
st.set_page_config(page_title="Planning Médical 2026", layout="wide")
V = {"GW": 24, "GM": 24, "JK": 9, "JM": 7}
SHEET_ID = "1tk032kmegtMoTwhbOzopRns-NW4gVeyeuAe7CUmvbUE"

# --- FONCTION DE LECTURE UNIVERSELLE ---
def load_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    return pd.read_csv(url)

# --- LISTE DES MÉDECINS ---
MDS_LIST = [
    "Alexandra Warnant", "Alfredo Vieira", "Camie Dupuis", "Christian Davin",
    "Christophe Angelo", "Daryush Valadi", "Elisa Mastrodiscasa", "Gauthier Nendumba",
    "Julie Henrie", "Martin Hachez", "PF Laterre", "Raouf Sheta", "Simon Van Migem"
]

# --- INTERFACE ---
if 'u' not in st.session_state:
    st.title("🏥 Planning Mons/Warquignies")
    u_s = st.selectbox("Sélectionnez votre nom", MDS_LIST)
    pw = st.text_input("Mot de passe", type="password")
    
    if st.button("Se connecter"):
        df_u = load_data("Users")
        # On vérifie le mot de passe dans le Google Sheet
        user_data = df_u[df_u["Medecin"] == u_s]
        if not user_data.empty and str(user_data.iloc[0]["MDP"]) == pw:
            st.session_state.u = u_s
            st.rerun()
        else:
            st.error("Mot de passe incorrect ou utilisateur non trouvé dans l'onglet 'Users'")

else:
    # Récupération des données pour les notifications
    try:
        df_e = load_data("Echanges")
        mes_demandes = df_e[(df_e["Destinataire"] == st.session_state.u) & (df_e["Statut"] == "ATTENTE")]
        nb_notif = len(mes_demandes)
    except:
        nb_notif = 0

    label_echange = f"🔄 Échanges ({nb_notif})" if nb_notif > 0 else "🔄 Échanges"
    mn = ["📅 Désiderata de congé", label_echange, "🚀 Admin", "🔑 Changement de mot de passe", "Sortie"]
    if st.session_state.u != "Christophe Angelo": mn.remove("🚀 Admin")
    sel = st.sidebar.radio("Navigation", mn)

    # 1. DÉSIDERATA
    if sel == "📅 Désiderata de congé":
        st.header("Vos Désiderata")
        st.info("Cliquez sur un jour pour basculer entre Présent ✅ et Absent ❌")
        # (La logique de sauvegarde ici nécessite une configuration plus poussée pour écrire sur Google Sheets)
        st.warning("Note : La lecture est active. L'écriture vers Google Sheets nécessite l'ID client dans vos Secrets.")

    # 2. ÉCHANGES
    elif "🔄 Échanges" in sel:
        st.header("Centre d'échanges")
        st.write(f"Bonjour Dr. {st.session_state.u}")
        
        if nb_notif > 0:
            st.subheader("📬 Demandes en attente de votre validation")
            for idx, row in mes_demandes.iterrows():
                with st.expander(f"Demande de {row['Emetteur']} pour le {row['Date']}"):
                    st.write(f"Poste : **{row['Poste']}**")
                    st.button("✅ Accepter (Indisponible en lecture seule)", disabled=True)
        else:
            st.info("Vous n'avez aucune demande d'échange en attente.")

    # 3. ADMIN
    elif sel == "🚀 Admin":
        st.header("Espace Administrateur")
        st.subheader("État actuel du personnel")
        df_users = load_data("Users")
        st.dataframe(df_users)
        
        if st.button("Simuler la génération du planning"):
            st.write("Moteur de calcul prêt.")

    # 4. CHANGEMENT DE MOT DE PASSE
    elif sel == "🔑 Changement de mot de passe":
        st.header("Modifier votre mot de passe")
        new_p = st.text_input("Nouveau mot de passe", type="password")
        if st.button("Enregistrer"):
            st.info("Cette fonction nécessite les droits d'écriture sur le Google Sheet.")

    # 5. SORTIE
    elif sel == "Sortie":
        del st.session_state.u
        st.rerun()