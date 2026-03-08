import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Planning Médical 2026", layout="centered")
DB_FILE = "users_db.csv"
OFF_FILE = "desiderata_db.csv"

# Nouveaux noms professionnels
LISTE_MEDECINS = [
    "Alexandra Warnant", "Alfredo Vieira", "Camie Dupuis", "Christian Davin", 
    "Christophe Angelo", "Daryush Valadi", "Elisa Mastrodiscasa", "Gauthier Nendumba", 
    "Julie Henrie", "Martin Hachez", "PF Laterre", "Raouf Sheta", "Simon Van Migem"
]

# Initialisation des fichiers
pd.DataFrame({"Medecin": LISTE_MEDECINS, "MDP": ["Doudoudragon"] * len(LISTE_MEDECINS)}).to_csv(DB_FILE, index=False)

if not os.path.exists(OFF_FILE):
    pd.DataFrame(columns=["Medecin", "Date_OFF"]).to_csv(OFF_FILE, index=False)

def get_data(file): return pd.read_csv(file)
def save_data(df, file): df.to_csv(file, index=False)

# --- CONNEXION ---
if 'user' not in st.session_state:
    st.title("🏥 Planning Médical 2026")
    u_df = get_data(DB_FILE)
    user_sel = st.selectbox("Sélectionnez votre nom", u_df["Medecin"].tolist())
    pwd_in = st.text_input("Mot de passe", type="password")
    
    if st.button("Se connecter"):
        correct_p = u_df.loc[u_df["Medecin"] == user_sel, "MDP"].values[0]
        if pwd_in == correct_p:
            st.session_state.user = user_sel
            st.rerun()
        else:
            st.error("Mot de passe incorrect.")
else:
    # --- INTERFACE ---
    st.sidebar.title(f"Dr {st.session_state.user}")
    menu = st.sidebar.radio("Menu", ["📅 Mes Desiderata", "🔐 Changer MDP", "⚙️ Admin", "Déconnexion"])

    if menu == "📅 Mes Desiderata":
        st.header("Gestion de vos indisponibilités")
        
        all_off = get_data(OFF_FILE)
        current_user_off = all_off[all_off["Medecin"] == st.session_state.user]["Date_OFF"].tolist()
        
        st.subheader("1. Sélectionner une date ou une période")
        selected_range = st.date_input(
            "Utilisez le calendrier (cliquez 2x pour une période) :",
            value=None,
            min_value=date(2026, 4, 1),
            max_value=date(2026, 8, 31),
        )

        dates_to_process = []
        if selected_range:
            if isinstance(selected_range, list) or isinstance(selected_range, tuple):
                if len(selected_range) == 2:
                    start, end = selected_range
                    delta = end - start
                    dates_to_process = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta.days + 1)]
                elif len(selected_range) == 1:
                    dates_to_process = [selected_range[0].strftime("%Y-%m-%d")]
            else:
                dates_to_process = [selected_range.strftime("%Y-%m-%d")]

        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("➕ AJOUTER", use_container_width=True):
                if dates_to_process:
                    new_rows = pd.DataFrame([{"Medecin": st.session_state.user, "Date_OFF": d} for d in dates_to_process if d not in current_user_off])
                    all_off = pd.concat([all_off, new_rows], ignore_index=True)
                    save_data(all_off, OFF_FILE)
                    st.success(f"Ajouté")
                    st.rerun()

        with col2:
            if st.button("➖ RETIRER", use_container_width=True):
                if dates_to_process:
                    all_off = all_off[~((all_off["Medecin"] == st.session_state.user) & (all_off["Date_OFF"].isin(dates_to_process)))]
                    save_data(all_off, OFF_FILE)
                    st.warning("Retiré")
                    st.rerun()

        st.divider()
        st.subheader("2. Votre récapitulatif")
        if current_user_off:
            current_user_off.sort()
            st.info(f"Total : {len(current_user_off)} jours OFF")
            st.write(", ".join(current_user_off))
            
            if st.button("🗑️ TOUT SUPPRIMER (RAZ)", type="secondary"):
                all_off = all_off[all_off["Medecin"] != st.session_state.user]
                save_data(all_off, OFF_FILE)
                st.rerun()
        else:
            st.write("Aucune date enregistrée.")

    elif menu == "⚙️ Admin":
        st.header("Zone Administrateur")
        off_data = get_data(OFF_FILE)
        st.dataframe(off_data)
        st.download_button("📥 Télécharger les Desiderata (CSV)", off_data.to_csv(index=False), "desiderata_complet.csv")

    elif menu == "🔐 Changer MDP":
        new_p = st.text_input("Nouveau mot de passe", type="password")
        if st.button("Valider le changement"):
            u_df = get_data(DB_FILE)
            u_df.loc[u_df["Medecin"] == st.session_state.user, "MDP"] = new_p
            save_data(u_df, DB_FILE)
            st.success("Mot de passe mis à jour !")

    if menu == "Déconnexion":
        del st.session_state.user
        st.rerun()
