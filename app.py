import streamlit as st
import pandas as pd
import os
from datetime import date

# --- CONFIGURATION ---
st.set_page_config(page_title="Planning Dragon", layout="centered")
DB_FILE = "users_db.csv"
OFF_FILE = "desiderata_db.csv"

# Initialisation de la base de données utilisateurs si elle n'existe pas
if not os.path.exists(DB_FILE):
    # Création de la liste initiale avec le MDP par défaut
    meds = ["Alex", "Christophe", "Julie", "Camie", "Martin", "Simon", "Gauthier", "Alfredo", "Raouf", "Elisa", "Christian", "Daryush"]
    df_users = pd.DataFrame({"Medecin": meds, "MDP": ["Doudoudragon"] * len(meds)})
    df_users.to_csv(DB_FILE, index=False)

def get_users():
    return pd.read_csv(DB_FILE)

def save_users(df):
    df.to_csv(DB_FILE, index=False)

# --- LOGIQUE DE CONNEXION ---
if 'user' not in st.session_state:
    st.title("🏥 Planning Médical")
    st.info("Mot de passe initial : Doudoudragon")
    
    users_df = get_users()
    user_select = st.selectbox("Sélectionnez votre nom", users_df["Medecin"].tolist())
    pwd_input = st.text_input("Mot de passe", type="password")
    
    if st.button("Se connecter"):
        correct_pwd = users_df.loc[users_df["Medecin"] == user_select, "MDP"].values[0]
        if pwd_input == correct_pwd:
            st.session_state.user = user_select
            st.rerun()
        else:
            st.error("Mot de passe incorrect.")
else:
    # --- INTERFACE UNE FOIS CONNECTÉ ---
    st.sidebar.title(f"Dr {st.session_state.user}")
    menu = st.sidebar.radio("Menu", ["Encoder mes OFF", "Changer mon mot de passe", "Déconnexion"])

    if menu == "Encoder mes OFF":
        st.header("📅 Vos Desiderata")
        dates = st.date_input("Cliquer sur vos jours d'absence :", value=[], min_value=date(2026, 4, 1), max_value=date(2026, 8, 31))
        if st.button("Enregistrer mes dates"):
            st.success("Dates enregistrées ! (Simulé)")

    elif menu == "Changer mon mot de passe":
        st.header("🔐 Sécurisez votre compte")
        new_pwd = st.text_input("Nouveau mot de passe", type="password")
        conf_pwd = st.text_input("Confirmez le mot de passe", type="password")
        
        if st.button("Mettre à jour le MDP"):
            if new_pwd == conf_pwd and len(new_pwd) > 3:
                users_df = get_users()
                users_df.loc[users_df["Medecin"] == st.session_state.user, "MDP"] = new_pwd
                save_users(users_df)
                st.success("Mot de passe modifié avec succès !")
            else:
                st.error("Les mots de passe ne correspondent pas ou sont trop courts.")

    if menu == "Déconnexion":
        del st.session_state.user
        st.rerun()
