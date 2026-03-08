import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Planning Dragon 2026", layout="centered")
DB_FILE = "users_db.csv"
OFF_FILE = "desiderata_db.csv"

# Initialisation des fichiers
if not os.path.exists(DB_FILE):
    meds = ["Alex", "Christophe", "Julie", "Camie", "Martin", "Simon", "Gauthier", "Alfredo", "Raouf", "Elisa", "Christian", "Daryush"]
    pd.DataFrame({"Medecin": meds, "MDP": ["Doudoudragon"] * len(meds)}).to_csv(DB_FILE, index=False)

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
    # --- INTERFACE ---
    st.sidebar.title(f"Dr {st.session_state.user}")
    menu = st.sidebar.radio("Menu", ["📅 Mes Desiderata", "🔐 Changer MDP", "⚙️ Admin", "Logout"])

    if menu == "📅 Mes Desiderata":
        st.header("Gestion de vos indisponibilités")
        
        all_off = get_data(OFF_FILE)
        current_user_off = all_off[all_off["Medecin"] == st.session_state.user]["Date_OFF"].tolist()
        
        st.subheader("1. Sélectionner une date ou une période")
        selected_range = st.date_input(
            "Utilisez le calendrier :",
            value=None,
            min_value=date(2026, 4, 1),
            max_value=date(2026, 8, 31),
        )

        # Transformation de la sélection en liste de dates
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
                    st.success(f"{len(new_rows)} jour(s) ajouté(s)")
                    st.rerun()

        with col2:
            if st.button("➖ RETIRER", use_container_width=True):
                if dates_to_process:
                    # On garde uniquement les dates qui NE sont PAS dans la sélection actuelle
                    all_off = all_off[~((all_off["Medecin"] == st.session_state.user) & (all_off["Date_OFF"].isin(dates_to_process)))]
                    save_data(all_off, OFF_FILE)
                    st.warning("Sélection retirée")
                    st.rerun()

        st.divider()
        st.subheader("2. Votre récapitulatif")
        if current_user_off:
            current_user_off.sort()
            st.info(f"Total : {len(current_user_off)} jours OFF enregistrés.")
            # Affichage en colonnes pour plus de clarté
            st.write(", ".join(current_user_off))
            
            if st.button("🗑️ TOUT SUPPRIMER (RAZ)", type="secondary"):
                all_off = all_off[all_off["Medecin"] != st.session_state.user]
                save_data(all_off, OFF_FILE)
                st.rerun()
        else:
            st.write("Aucune date enregistrée.")

    # ... (Le reste du code Admin/MDP reste identique)
    elif menu == "⚙️ Admin":
        st.header("Zone Administrateur")
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
