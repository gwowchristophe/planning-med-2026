import streamlit as st
import gspread
import pandas as pd

# Connexion sécurisée pour l'écriture
def get_sheet_client():
    # Utilise les secrets configurés dans Streamlit Cloud
    credentials = {
        "type": st.secrets["type"],
        "project_id": st.secrets["project_id"],
        "private_key_id": st.secrets["private_key_id"],
        "private_key": st.secrets["private_key"],
        "client_email": st.secrets["client_email"],
        "client_id": st.secrets["client_id"],
        "auth_uri": st.secrets["auth_uri"],
        "token_uri": st.secrets["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["client_x509_cert_url"]
    }
    gc = gspread.service_account_from_dict(credentials)
    return gc.open_by_key("1tk032kmegtMoTwhbOzopRns-NW4gVeyeuAe7CUmvbUE")

# Fonction pour SAUVEGARDER
def save_to_google(df, sheet_name):
    sh = get_sheet_client()
    worksheet = sh.worksheet(sheet_name)
    worksheet.clear()
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())