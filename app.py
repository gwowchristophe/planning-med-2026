import streamlit as st
import pandas as pd
import os, calendar, random, io
from datetime import date, datetime, timedelta
import holidays

# --- PARAMETRAGE ---
st.set_page_config(page_title="Planning Médical 2026", layout="wide")
V = {"GW": 24, "GM": 24, "JK": 9, "JM": 7}
DB, OF = "users_db.csv", "desiderata_db.csv"
BH = holidays.BE(years=2026)
FR_D = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

MDS = {
    "Alexandra Warnant": {"e": 0.8, "j": 1, "t": 0},
    "Alfredo Vieira": {"e": 0.8, "j": 1, "t": 0},
    "Camie Dupuis": {"e": 0.8, "j": 1, "t": 0},
    "Christian Davin": {"e": 0.8, "j": 0, "t": 1},
    "Christophe Angelo": {"e": 0.6, "j": 1, "t": 0},
    "Daryush Valadi": {"e": 0.4, "j": 0, "t": 0},
    "Elisa Mastrodiscasa": {"e": 0.8, "j": 0, "t": 1},
    "Gauthier Nendumba": {"e": 0.8, "j": 1, "t": 0},
    "Julie Henrie": {"e": 0.6, "j": 1, "t": 0},
    "Martin Hachez": {"e": 0.8, "j": 1, "t": 0},
    "PF Laterre": {"e": 0.8, "j": 0, "t": 0},
    "Raouf Sheta": {"e": 0.8, "j": 0, "t": 1},
    "Simon Van Migem": {"e": 0.8, "j": 1, "t": 0}
}

# --- FONCTIONS ---
def gd(f): return pd.read_csv(f) if os.path.exists(f) else pd.DataFrame()
def sd(df, f): df.to_csv(f, index=False)

def ok(n, d, p, pl, vo):
    ds = d.strftime("%Y-%m-%d")
    if ds in vo.get(n, []): return False
    ve = d - timedelta(days=1)
    if ve in pl and n in pl[ve].values(): return False
    if n == "Daryush Valadi" and (d.weekday() == 0 or p != "JM"): return False
    if MDS[n]["t"] and p != "GW": return False
    if n == "PF Laterre" and p == "JK": return False
    if p == "JK" and not MDS[n]["j"]: return False
    return True

def get_s(n, stt): return stt[n] / MDS[n]["e"]

def create_ics(name, df_plan):
    ics = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//PlanningMed//FR"]
    for d, row in df_plan.iterrows():
        for poste, med in row.items():
            if med == name:
                d_str = d.strftime("%Y%m%d")
                ics.append("BEGIN:VEVENT")
                ics.append(f"DTSTART;VALUE=DATE:{d_str}")
                ics.append(f"SUMMARY:Garde {poste}")
                ics.append(f"DESCRIPTION:Poste de garde {poste} - Planning 2026")
                ics.append("END:VEVENT")
    ics.append("END:VCALENDAR")
    return "\n".join(ics)

# --- NAVIGATION ---
if 'u' not in st.session_state:
    st.title("🏥 Connexion Planning 2026")
    u_df = gd(DB)
    if u_df.empty:
        df_i = pd.DataFrame({"Medecin": list(MDS.keys()), "MDP": ["Doudoudragon"]*13})
        sd(df_i, DB); st.rerun()
    u_s = st.selectbox("Sélectionnez votre nom", list(MDS.keys()))
    pw = st.text_input("Code d'accès", type="password")
    if st.button("Se connecter"):
        v = str(u_df.loc[u_df["Medecin"]==u_s, "MDP"].values[0])
        if pw == v:
            st.session_state.u = u_s
            st.rerun()
        else: st.error("Code incorrect")
else:
    mn = ["📅 Mes OFF / Mon Agenda", "🚀 Générateur Global", "🔐 Mon Code", "Sortie"]
    if st.session_state.u != "Christophe Angelo": mn.remove("🚀 Générateur Global")
    sel = st.sidebar.radio("Navigation", mn)

    if sel == "📅 Mes OFF / Mon Agenda":
        st.header(f"Espace de {st.session_state.u}")
        
        # Section Téléchargement Agenda
        if os.path.exists("last_plan.csv"):
            st.subheader("📥 Mon Calendrier Personnel")
            df_full = pd.read_csv("last_plan.csv", index_col=0)
            df_full.index = pd.to_datetime(df_full.index)
            ics_data = create_ics(st.session_state.u, df_full)
            st.download_button(label="Télécharger mon fichier .ics (Agenda)", 
                               data=ics_data, 
                               file_name=f"agenda_{st.session_state.u}.ics", 
                               mime="text/calendar")
        
        st.divider()
        st.subheader("Encodage des indisponibilités")
        mo = st.selectbox("Choisir le mois", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
        df_off = gd(OF)
        c_o = set(df_off[df_off["Medecin"]==st.session_state.u]["Date_OFF"].tolist())
        
        cols_h = st.columns(7)
        for i, d_n in enumerate(FR_D): cols_h[i].info(f"**{d_n}**")
        
        cl = calendar.monthcalendar(2026, mo)
        for s in cl:
            cols = st.columns(7)
            for i, j in enumerate(s):
                if j != 0:
                    ds = f"2026-{mo:02d}-{j:02d}"
                    t = f"{j}\n{'❌' if ds in c_o else '✅'}"
                    if cols[i].button(t, key=ds, use_container_width=True):
                        if ds in c_o: df_off = df_off[~((df_off["Medecin"]==st.session_state.u)&(df_off["Date_OFF"]==ds))]
                        else: df_off = pd.concat([df_off, pd.DataFrame([{"Medecin":st.session_state.u,"Date_OFF":ds}])])
                        sd(df_off, OF); st.rerun()

    elif sel == "🚀 Générateur Global":
        st.header("Génération du Planning")
        if st.button("Lancer la simulation"):
            vo = gd(OF).groupby("Medecin")["Date_OFF"].apply(list).to_dict()
            pl, stt = {}, {m: 0 for m in MDS.keys()}
            sq = {m: {"S":0,"D":0,"F":0,"TotG":0} for m in MDS