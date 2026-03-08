import streamlit as st
import pandas as pd
import os
import calendar
from datetime import date

# --- CONFIGURATION ---
st.set_page_config(page_title="Planning Médical 2026", layout="wide")
DB_FILE = "users_db.csv"
OFF_FILE = "desiderata_db.csv"

LISTE_MEDECINS = ["Alexandra Warnant", "Alfredo Vieira", "Camie Dupuis", "Christian Davin", "Christophe Angelo", "Daryush Valadi", "Elisa Mastrodiscasa", "Gauthier Nendumba", "Julie Henrie", "Martin Hachez", "PF Laterre", "Raouf Sheta", "Simon Van Migem"]

if not os.path.exists(DB_FILE):
    pd.DataFrame({"Medecin": LISTE_MEDECINS, "MDP": ["Doudoudragon"] * len(LISTE_MEDECINS)}).to_csv(DB_FILE, index=False)
if not os.path.exists(OFF_FILE):
    pd.DataFrame(columns=["Medecin", "Date_OFF"]).to_csv(OFF_FILE, index=False)

def get_data(file): return pd.read_csv(file)
def save_data(df, file): df.to_csv(file, index=False)

# --- CONNEXION ---
if 'user' not in st.session_state:
    st.title("🏥 Accès Planning 2026")
    u_df = get_data(DB_FILE)
    user_sel = st.selectbox("Qui êtes-vous ?", u_df["Medecin"].tolist())
    pwd_in = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        if pwd_in == u_df.loc[u_df["Medecin"] == user_sel, "MDP"].values[0]:
            st.session_state.user = user_sel
            st.rerun()
        else:
            st.error("Erreur de mot de passe.")
else:
    # --- INTERFACE CALENDRIER ---
    st.sidebar.title(f"Dr {st.session_state.user}")
    annee = 2026
    mois_noms = {4: "Avril", 5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août"}
    mois_sel = st.sidebar.selectbox("Mois :", list(mois_noms.keys()), format_func=lambda x: mois_noms[x])
    
    if st.sidebar.button("Déconnexion"):
        del st.session_state.user
        st.rerun()

    st.title(f"📅 Disponibilités - {mois_noms[mois_sel]} {annee}")
    st.write("Cliquer pour basculer : **Bleu = DISPO** | **Gris = OFF**")

    all_off = get_data(OFF_FILE)
    current_user_off = set(all_off[all_off["Medecin"] == st.session_state.user]["Date_OFF"].astype(str).tolist())

    cal = calendar.monthcalendar(annee, mois_sel)
    jours_semaine = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    
    # En-têtes
    cols_h = st.columns(7)
    for i, j_nom in enumerate(jours_semaine):
        cols_h[i].write(f"**{j_nom}**")

    # Grille
    for semaine in cal:
        cols = st.columns(7)
        for i, jour in enumerate(semaine):
            if jour == 0:
                cols[i].write("") 
            else:
                date_str = f"{annee}-{mois_sel:02d}-{jour:02d}"
                is_off = date_str in current_user_off
                
                label = f"{jour}\n{'❌ OFF' if is_off else '✅ OK'}"
                style = "secondary" if is_off else "primary"
                
                if cols[i].button(label, key=date_str, use_container_width=True, type=style):
                    if is_off:
                        # Retirer des OFF
                        all_off = all_off[~((all_off["Medecin"] == st.session_state.user) & (all_off["Date_OFF"] == date_str))]
                    else:
                        # Ajouter aux OFF
                        new_row = pd.DataFrame([{"Medecin": st.session_state.user, "Date_OFF": date_str}])
                        all_off = pd.concat([all_off, new_row], ignore_index=True)
                    
                    save_data(all_off, OFF_FILE)
                    st.rerun()

    st.divider()
    with st.expander("⚙️ Export des données"):
        st.download_button("📥 Télécharger CSV", all_off.to_csv(index=False), "planning_complet.csv")
