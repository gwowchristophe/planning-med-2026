import streamlit as st
import pandas as pd
import os, calendar
from datetime import date, timedelta
import holidays

# --- CONFIG ---
st.set_page_config(page_title="Planning 2026", layout="wide")
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
def get_s(n, stt): return stt[n] / MDS[n]["e"]

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

def run_gen(vo):
    pl, stt = {}, {m: 0 for m in MDS.keys()}
    sq = {m: {"S":0,"D":0,"F":0,"T":0} for m in MDS.keys()}
    # Génération des dates
    ads = []
    for m in range(4, 9):
        for d in range(1, calendar.monthrange(2026, m)[1] + 1):
            ads.append(date(2026, m, d))
    
    for d in ads:
        jp = {}
        ml = sorted(list(MDS.keys()), key=lambda x: get_s(x, stt))
        f, s, di = (d in BH), (d.weekday()==5), (d.weekday()==6)
        is_we = (f or s or di)
        
        for p in ["GW", "GM", "JK", "JM"]:
            if is_we and p in ["JK", "JM"]: continue
            if not is_we and p == "JK" and d.weekday() == 3: continue
            try:
                c = next(m for m in ml if m not in jp.values() and ok(m, d, p, pl, vo))
                jp[p], stt[c] = c, stt[c] + V[p]
                sq[c]["T"] += 1
                if s: sq[c]["S"] += 1
                if di: sq[c]["D"] += 1
                if f: sq[c]["F"] += 1
            except StopIteration:
                return None, d, p # Retourne le jour du blocage
        pl[d] = jp
    return pl, stt, sq

# --- APP ---
if 'u' not in st.session_state:
    st.title("🏥 Connexion")
    if not os.path.exists(DB):
        sd(pd.DataFrame({"Medecin":list(MDS.keys()),"MDP":["Doudoudragon"]*13}), DB)
    u_df = gd(DB)
    u_s = st.selectbox("Nom", list(MDS.keys()))
    pw = st.text_input("Code", type="password")
    if st.button("Valider"):
        if pw == str(u_df.loc[u_df["Medecin"]==u_s, "MDP"].values[0]):
            st.session_state.u = u_s
            st.rerun()
        else: st.error("Code erroné")
else:
    mn = ["📅 OFF / Agenda", "🚀 Générateur", "🔐 Code", "Sortie"]
    if st.session_state.u != "Christophe Angelo": mn.remove("🚀 Générateur")
    sel = st.sidebar.radio("Menu", mn)

    if sel == "🚀 Générateur":
        st.header("Générateur Global")
        if st.button("Lancer la création du planning"):
            try:
                vo = gd(OF).groupby("Medecin")["Date_OFF"].apply(list).to_dict()
                pl, stt, sq = run_gen(vo)
                
                if pl is None:
                    st.error(f"Bloqué le {stt} sur le poste {sq}. Trop de médecins en OFF ce jour-là !")
                else:
                    df_p = pd.DataFrame.from_dict(pl, orient='index')
                    df_p.to_csv("last.csv")
                    st.success("Planning généré !")
                    st.dataframe(df_p)
                    
                    res = []
                    for m in MDS.keys():
                        moy = round((stt[m]/22)+(7.68*MDS[m]["e"]), 2)
                        res.append({"Médecin":m, "H":stt[m], "Moy":moy, "Total":sq[m]["T"], "WE+Fé":sq[m]["S"]+sq[m]["D"]+sq[m]["F"]})
                    st.table(pd.DataFrame(res))
            except Exception as e:
                st.error(f"Erreur technique : {e}")

    elif sel == "📅 OFF / Agenda":
        st.header("Mes Indisponibilités")
        # Suite du code... (identique au précédent pour les OFF)
        mo = st.selectbox("Mois", [4,5,6,7,8])
        df_o = gd(OF)
        # (Copiez ici le reste de votre logique calendrier habituelle)
        st.info("Sélectionnez vos jours OFF ci-dessous")

    elif sel == "🔐 Code":
        st.header("Changer mon code")
        new_p = st.text_input("Nouveau code", type="password")
        if st.button("Enregistrer"):
            u_df = gd(DB)
            u_df.loc[u_df["Medecin"]==st.session_state.u, "MDP"] = new_p
            sd(u_df, DB)
            st.success("Code modifié !")

    elif sel == "Sortie":
        del st.session_state.u
        st.rerun()