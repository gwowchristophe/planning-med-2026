import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os

# --- CONFIGURATION DE L'INTERFACE ---
st.set_page_config(page_title="Planning Médical Kennedy-Warquignies", layout="centered")

# --- INITIALISATION DE LA BASE DE DONNÉES LOCALE ---
DATA_FILE = "desiderata_db.csv"
if not os.path.exists(DATA_FILE):
    df_init = pd.DataFrame(columns=["Medecin", "Date_OFF", "Type"])
    df_init.to_csv(DATA_FILE, index=False)

# --- GESTION DE LA CONNEXION ---
if 'user' not in st.session_state:
    st.title("🏥 Connexion Planning")
    medecins = ["Alex", "Camie", "Christophe", "Julie", "Martin", "Simon", "Gauthier", "Alfredo", "Raouf", "Elisa", "Christian", "Daryush"]
    user = st.selectbox("Sélectionnez votre nom", medecins)
    password = st.text_input("Mot de passe", type="password", help="Par défaut: med123")
    
    if st.button("Se connecter"):
        if password == "med123": # Mot de passe simple pour l'exemple
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Mot de passe incorrect.")
else:
    # --- INTERFACE UTILISATEUR (SMARTPHONE) ---
    st.sidebar.title(f"👨‍⚕️ {st.session_state.user}")
    menu = st.sidebar.radio("Navigation", ["Encoder mes OFF", "Voir le planning final"])

    if menu == "Encoder mes OFF":
        st.header("📅 Vos Desiderata")
        st.write("Sélectionnez les jours où vous ne pouvez PAS travailler.")
        
        # Calendrier multi-sélection
        dates_selectionnees = st.date_input(
            "Cliquer sur les jours d'absence :",
            value=[],
            min_value=date(2026, 4, 1),
            max_value=date(2026, 8, 31)
        )
        
        motif = st.selectbox("Motif", ["Congé", "Formation/DIU", "Repos Contractuel"])

        if st.button("Enregistrer mes dates"):
            # Sauvegarde dans le fichier CSV
            current_db = pd.read_csv(DATA_FILE)
            # Supprimer les anciennes entrées pour ce médecin pour mettre à jour
            current_db = current_db[current_db['Medecin'] != st.session_state.user]
            
            new_entries = pd.DataFrame({
                "Medecin": [st.session_state.user] * len(dates_selectionnees),
                "Date_OFF": [d.strftime("%Y-%m-%d") for d in dates_selectionnees],
                "Type": [motif] * len(dates_selectionnees)
            })
            
            updated_db = pd.concat([current_db, new_entries])
            updated_db.to_csv(DATA_FILE, index=False)
            st.success("✅ Vos dates ont été enregistrées avec succès !")

    elif menu == "Voir le planning final":
        st.header("📋 Planning Généré")
        if st.button("🚀 Calculer/Actualiser l'horaire"):
            st.info("L'algorithme analyse les règles : V+D, Repos 48h, et 3ème WE...")
            # Ici on simule l'affichage du résultat
            st.warning("Fonctionnalité en cours de liaison avec l'algorithme complet.")

    if st.sidebar.button("Déconnexion"):
        del st.session_state.user
        st.rerun()
