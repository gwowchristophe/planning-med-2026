import streamlit as st
import pandas as pd
import os
from datetime import date

# --- CONFIGURATION ---
st.set_page_config(page_title="Planning Dragon 2026", layout="centered")
DB_FILE = "users_db.csv"
OFF_FILE = "desiderata_db.csv"

# Initialisation des fichiers si inexistants
if not os.path.exists(DB_FILE):
    meds = ["Alex", "Christophe", "Julie", "Camie", "Martin", "Simon", "Gauthier", "Alfredo", "Raouf", "Elisa", "Christian", "Daryush"]
    pd.DataFrame({"Medecin": meds, "MDP": ["Doudoudragon"] * len(meds)}).to_csv(DB_FILE, index=False)

if not os.path.exists(OFF_FILE):
    pd.DataFrame(columns=["Medecin", "Date_OFF"]).to_csv(OFF_FILE, index=False)

# Fonctions de lecture/écriture
def get_data(file): return pd.read_csv(file)
def save_data(df, file): df.to_csv(file, index=False)

# --- CONNEXION ---
if 'user' not in st.session_state:
    st.title("🏥 Planning Médical 2026")
    u_df = get_data(DB_FILE)
    user_sel = st.selectbox("Qui êtes-vous ?", u_df["Medecin"].tolist())
    pwd_in = st.text_input("Mot de passe", type="password")
    
    if st.button("Se connecter"):
        correct_p = u_df.loc[u_df["Medecin"] == user_sel, "MDP"].values[0]
        if pwd_in == correct_p:
            st.session_state.user = user_sel
            st.rerun()
        else:
            st.error("Mot de passe incorrect.")
else:
    # --- INTERFACE CONNECTÉE ---
    st.sidebar.title(f"Dr {st.session_state.user}")
    menu = st.sidebar.radio("Menu", ["📅 Mes OFF (Multiples)", "🔐 Changer MDP", "⚙️ Admin (Sauvegarde)", "Logout"])

    if menu == "📅 Mes OFF (Multiples)":
        st.header("Encoder vos indisponibilités")
        st.info("Vous pouvez sélectionner plusieurs dates isolées.")
        
        # SOLUTION : Utiliser l'option 'toggle' ou une liste de sélection
        # Pour Streamlit, le plus propre pour du multi-dates éparpillées :
        all_off = get_data(OFF_FILE)
        current_off = all_off[all_off["Medecin"] == st.session_state.user]["Date_OFF"].tolist()
        
        st.write("Dates déjà enregistrées :", ", ".join(current_off) if current_off else "Aucune")
        
        new_date = st.date_input("Ajouter une date OFF :", min_value=date(2026, 4, 1), max_value=date(2026, 8, 31))
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Ajouter cette date"):
                if str(new_date) not in current_off:
                    new_row = pd.DataFrame({"Medecin": [st.session_state.user], "Date_OFF": [str(new_date)]})
                    all_off = pd.concat([all_off, new_row])
                    save_data(all_off, OFF_FILE)
                    st.success(f"Date {new_date} ajoutée.")
                    st.rerun()
        with col2:
            if st.button("🗑️ Tout effacer mes OFF"):
                all_off = all_off[all_off["Medecin"] != st.session_state.user]
                save_data(all_off, OFF_FILE)
                st.warning("Toutes vos dates ont été supprimées.")
                st.rerun()

    elif menu == "⚙️ Admin (Sauvegarde)":
        st.header("Zone Administrateur")
        st.write("Téléchargez les données pour ne rien perdre sur votre PC :")
        
        off_data = get_data(OFF_FILE)
        st.download_button("📥 Télécharger les Desiderata (CSV)", off_data.to_csv(index=False), "export_desiderata.csv", "text/csv")
        
        user_data = get_data(DB_FILE)
        st.download_button("📥 Télécharger les Mots de Passe (CSV)", user_data.to_csv(index=False), "export_users.csv", "text/csv")

    elif menu == "🔐 Changer MDP":
        new_p = st.text_input("Nouveau MDP", type="password")
        if st.button("Valider"):
            u_df = get_data(DB_FILE)
            u_df.loc[u_df["Medecin"] == st.session_state.user, "MDP"] = new_p
            save_data(u_df, DB_FILE)
            st.success("MDP changé !")

    if menu == "Logout":
        del st.session_state.user
        st.rerun()
