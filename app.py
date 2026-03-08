import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import calendar
from datetime import date, timedelta
import holidays

# --- CONFIGURATION ---
st.set_page_config(page_title="Planning Médical 2026", layout="wide")
V = {"GW": 24, "GM": 24, "JK": 9, "JM": 7}
URL_SHEET = "https://docs.google.com/spreadsheets/d/1tk032kmegtMoTwhbOzopRns-NW4gVeyeuAe7CUmvbUE/edit?usp=sharing" # À REMPLACER

# Connexion à Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FONCTIONS DE LECTURE/ÉCRITURE ---
def load_data(sheet_name):
    return conn.read(spreadsheet=URL_SHEET, worksheet=sheet_name)

def save_data(df, sheet_name):
    conn.update(spreadsheet=URL_SHEET, worksheet=sheet_name, data=df)
    st.cache_data.clear()

# --- INTERFACE ---
if 'u' not in st.session_state:
    st.title("🏥 Planning Mons/Warquignies 2026")
    u_s = st.selectbox("Médecin", [
        "Alexandra Warnant", "Alfredo Vieira", "Camie Dupuis", "Christian Davin",
        "Christophe Angelo", "Daryush Valadi", "Elisa Mastrodiscasa", "Gauthier Nendumba",
        "Julie Henrie", "Martin Hachez", "PF Laterre", "Raouf Sheta", "Simon Van Migem"
    ])
    pw = st.text_input("Mot de passe", type="password")
    
    if st.button("Se connecter"):
        df_users = load_data("Users")
        user_row = df_users[df_users["Medecin"] == u_s]
        if not user_row.empty and pw == str(user_row.iloc[0]["MDP"]):
            st.session_state.u = u_s
            st.rerun()
        else: st.error("Identifiants incorrects")

else:
    # Récupération des notifications d'échanges
    df_e = load_data("Echanges")
    mes_notifs = df_e[(df_e["Destinataire"] == st.session_state.u) & (df_e["Statut"] == "ATTENTE")]
    
    menu = [
        "📅 Désiderata de congé", 
        f"🔄 Échanges ({len(mes_notifs)})", 
        "🚀 Admin", 
        "🔑 Changement de mot de passe", 
        "Sortie"
    ]
    if st.session_state.u != "Christophe Angelo": menu.remove("🚀 Admin")
    sel = st.sidebar.radio("Navigation", menu)

    # --- LOGIQUE DÉSIDERATA ---
    if sel == "📅 Désiderata de congé":
        st.header("Encoder vos congés (✅ disponible / ❌ absent)")
        mo = st.selectbox("Mois", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
        df_off = load_data("Desiderata")
        
        # Filtre les dates OFF du médecin actuel
        mes_off = set(df_off[df_off["Medecin"] == st.session_state.u]["Date_OFF"].tolist())
        
        for s in calendar.monthcalendar(2026, mo):
            cols = st.columns(7)
            for i, j in enumerate(s):
                if j != 0:
                    ds = f"2026-{str(mo).zfill(2)}-{str(j).zfill(2)}"
                    label = f"{j} ❌" if ds in mes_off else f"{j} ✅"
                    if cols[i].button(label, key=ds):
                        if ds in mes_off:
                            df_off = df_off[~((df_off["Medecin"] == st.session_state.u) & (df_off["Date_OFF"] == ds))]
                        else:
                            new_row = pd.DataFrame([{"Medecin": st.session_state.u, "Date_OFF": ds}])
                            df_off = pd.concat([df_off, new_row])
                        save_data(df_off, "Desiderata")
                        st.rerun()

    # --- CHANGEMENT MOT DE PASSE ---
    elif sel == "🔑 Changement de mot de passe":
        st.header("Modifier votre accès")
        new_p = st.text_input("Nouveau mot de passe", type="password")
        conf = st.text_input("Confirmer", type="password")
        if st.button("Valider"):
            if new_p == conf and new_p != "":
                df_u = load_data("Users")
                df_u.loc[df_u["Medecin"] == st.session_state.u, "MDP"] = new_p
                save_data(df_u, "Users")
                st.success("Mot de passe mis à jour dans Google Sheets !")

    elif sel == "Sortie":
        del st.session_state.u
        st.rerun()