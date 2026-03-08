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
        st.header("Encoder vos indisponibilités")
        
        # Récupérer les dates déjà sauvées
        all_off = get_data(OFF_FILE)
        current_user_off = all_off[all_off["Medecin"] == st.session_state.user]["Date_OFF"].tolist()
        
        st.subheader("1. Ajouter des dates")
        st.info("Sélectionnez une date seule ou une période (Début et Fin).")
        
        # Calendrier mode 'range'
        selected_range = st.date_input(
            "Sélectionnez vos dates :",
            value=None,
            min_value=date(2026, 4, 1),
            max_value=date(2026, 8, 31),
            help="Cliquez une fois pour un jour seul, deux fois pour une période."
        )

        if st.button("➕ Ajouter à ma liste"):
            if selected_range:
                # Si c'est une période (liste de 2 dates)
                if isinstance(selected_range, list) or isinstance(selected_range, tuple):
                    if len(selected_range) == 2:
                        start, end = selected_range
                        delta = end - start
                        new_dates = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta.days + 1)]
                    else: # Une seule date sélectionnée dans le calendrier
                        new_dates = [selected_range[0].strftime("%Y-%m-%d")]
                else: # Date unique
                    new_dates = [selected_range.strftime("%Y-%m-%d")]

                # Ajouter sans doublons
                new_rows = pd.DataFrame([{"Medecin": st.session_state.user, "Date_OFF": d} for d in new_dates if d not in current_user_off])
                all_off = pd.concat([all_off, new_rows], ignore_index=True)
                save_data(all_off, OFF_FILE)
                st.success(f"{len(new_rows)} jour(s) ajouté(s) !")
                st.rerun()

        st.divider()
        st.subheader("2. Récapitulatif de vos jours OFF")
        if current_user_off:
            current_user_off.sort()
            st.write(f"Vous avez **{len(current_user_off)}** jours d'indisponibilité au total.")
            st.write(", ".join(current_user_off))
            
            if st.button("🗑️ Tout effacer et recommencer"):
                all_off = all_off[all_off["Medecin"] != st.session_state.user]
                save_data(all_off, OFF_FILE)
                st.warning("Toutes vos dates ont été supprimées.")
                st.rerun()
        else:
            
