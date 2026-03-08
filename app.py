import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Planning Médical 2026", layout="centered")
DB_FILE = "users_db.csv"
OFF_FILE = "desiderata_db.csv"

LISTE_MEDECINS = [
    "Alexandra Warnant", "Alfredo Vieira", "Camie Dupuis", "Christian Davin", 
    "Christophe Angelo", "Daryush Valadi", "Elisa Mastrodiscasa", "Gauthier Nendumba", 
    "Julie Henrie", "Martin Hachez", "PF Laterre", "Raouf Sheta", "Simon Van Migem"
]

# Initialisation
if not os.path.exists(DB_FILE):
    pd.DataFrame({"Medecin": LISTE_MEDECINS, "MDP": ["Doudoudragon"] * len(LISTE_MEDECINS)}).to_csv(DB_FILE, index=False)
if not os.path.exists(OFF_FILE):
    pd.DataFrame(columns=["Medecin", "Date_OFF"]).to_csv(OFF_FILE, index=False)

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
    st.sidebar.title(f"Dr {st.session_state.user}")
    menu = st.sidebar.radio("Menu", ["📅 Mes OFF", "🔐 Changer MDP", "⚙️ Admin", "Logout"])

    if menu == "📅 Mes OFF":
        st.header("Gestion de vos indisponibilités")
        all_off = get_data(OFF_FILE)
        current_user_off = all_off[all_off["Medecin"] == st.session_state.user]["Date_OFF"].astype(str).tolist()

        # --- NOUVELLE MÉTHODE DE SÉLECTION ---
        st.subheader("1. Ajouter des dates")
        type_ajout = st.radio("Format d'ajout :", ["Jour unique", "Période (Début - Fin)"], horizontal=True)

        dates_a_ajouter = []

        if type_ajout == "Jour unique":
            d_unique = st.date_input("Choisir le jour :", value=date(2026, 4, 1), min_value=date(2026, 4, 1), max_value=date(2026, 8, 31))
            if st.button("➕ Ajouter ce jour"):
                dates_a_ajouter = [str(d_unique)]
        
        else:
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                debut = st.date_input("Du :", value=date(2026, 4, 1), min_value=date(2026, 4, 1), max_value=date(2026, 8, 31))
            with col_d2:
                fin = st.date_input("Au :", value=date(2026, 4, 7), min_value=date(2026, 4, 1), max_value=date(2026, 8, 31))
            
            if st.button("➕ Ajouter toute la période"):
                if debut <= fin:
                    delta = fin - debut
                    dates_a_ajouter = [(debut + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta.days + 1)]
                else:
                    st.error("La date de fin doit être après le début.")

        # Traitement de l'ajout
        if dates_a_ajouter:
            new_rows = pd.DataFrame([{"Medecin": st.session_state.user, "Date_OFF": d} for d in dates_a_ajouter if d not in current_user_off])
            all_off = pd.concat([all_off, new_rows], ignore_index=True)
            save_data(all_off, OFF_FILE)
            st.success(f"{len(new_rows)} jour(s) ajouté(s)")
            st.rerun()

        st.divider()
        st.subheader("2. Votre récapitulatif")
        if current_user_off:
            current_user_off.sort()
            st.write(f"Total : **{len(current_user_off)}** jours OFF.")
            st.write(", ".join(current_user_off))
            
            if st.button("🗑️ TOUT SUPPRIMER"):
                all_off = all_off[all_off["Medecin"] != st.session_state.user]
                save_data(all_off, OFF_FILE)
                st.rerun()
        else:
            st.write("Aucune date enregistrée.")

    # (Le reste du code reste identique pour Admin et MDP)
    elif menu == "⚙️ Admin":
        st.header("Admin")
        off_data = get_data(OFF_FILE)
        st.dataframe(off_data)
        st.download_button("📥 Télécharger CSV", off_data.to_csv(index=False), "desiderata.csv")
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
