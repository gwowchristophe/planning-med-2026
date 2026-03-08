import streamlit as st
import pandas as pd
import os, calendar, random, io
from datetime import date, datetime, timedelta
import holidays

# --- CONFIG & DATA ---
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

# --- FONCTIONS LOGIQUES ---
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
    ads = [date(2026,m,d) for m in range(4,9) for d in range(1,calendar.monthrange(2026,m)[1]+1)]
    for d in ads:
        jp = {}
        ml = sorted(list(MDS.keys()), key=lambda x: get_s(x, stt))
        f, s, di = (d in BH), (d.weekday()==5), (d.weekday()==6)
        is_we = (f or s or di)
        for p in ["GW", "GM", "JK", "JM"]:
            if is_we and p in ["JK", "JM"]: continue
            if not is_we and p == "JK" and d.weekday() == 3: continue
            try:
                c = next(m for m in ml if m not in jp.values() and ok(m,d,p,pl,vo))
                jp[p], stt[c] = c, stt[c] + V[p]
                sq[c]["T"] += 1
                if s: sq[c]["S"] += 1
                if di: sq[c]["D"] += 1
                if f: sq[c]["F"] += 1
            except StopIteration: return None, None, None
        pl[d] = jp
    return pl, stt, sq

def create_ics(name, df_p):
    ics = ["BEGIN:VCALENDAR", "VERSION:2.0"]
    for d, row in df_p.iterrows():
        for p, m in row.items():
            if m == name:
                ics.append(f"BEGIN:VEVENT\nDTSTART;VALUE=DATE:{d.strftime('%Y%m%d')}")
                ics.append(f"SUMMARY:Garde {p}\nEND:VEVENT")
    ics.append("END:VCALENDAR")
    return "\n".join(ics)

# --- INTERFACE ---
if 'u' not in st.session_state:
    st.title("🏥 Connexion")
    u_df = gd(DB)
    if u_df.empty:
        sd(pd.DataFrame({"Medecin":list(MDS.keys()), "MDP":["Doudoudragon"]*13}), DB)
    u_s = st.selectbox("Nom", list(MDS.keys()))
    pw = st.text_input("Code", type="password")
    if st.button("OK"):
        if pw == str(u_df.loc[u_df["Medecin"]==u_s, "MDP"].values[0]):
            st.session_state.u = u_s
            st.rerun()
else:
    mn = ["📅 OFF / Agenda", "🚀 Go", "🔐 Code", "Sortie"]
    if st.session_state.u != "Christophe Angelo": mn.remove("🚀 Go")
    sel = st.sidebar.radio("Nav", mn)

    if sel == "📅 OFF / Agenda":
        if os.path.exists("last.csv"):
            df_full = pd.read_csv("last.csv", index_col=0)
            df_full.index = pd.to_datetime(df_full.index)
            st.download_button("Télécharger mon .ics", create_ics(st.session_state.u, df_full), f"{st.session_state.u}.ics")
        
        mo = st.selectbox("Mois", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
        df_o = gd(OF)
        c_o = set(df_o[df_o["Medecin"]==st.session_state.u]["Date_OFF"].tolist())
        cols_h = st.columns(7)
        for i, d_n in enumerate(FR_D): cols_h[i].info(d_n)
        for s in calendar.monthcalendar(2026, mo):
            cols = st.columns(7)
            for i, j in enumerate(s):
                if j != 0:
                    ds = f"2026-{