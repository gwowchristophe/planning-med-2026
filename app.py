import streamlit as st
import pandas as pd
import os, calendar
from datetime import date, timedelta
import holidays

# --- CONFIGURATION ---
st.set_page_config(page_title="Planning Médical 2026", layout="wide")
V = {"GW": 24, "GM": 24, "JK": 9, "JM": 7}
DB, OF, LP = "users_db.csv", "desiderata_db.csv", "last_plan.csv"
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

# --- LOGIQUE ---
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
    ads = [date(2026, m, j) for m in range(4,9) for j in range(1, calendar.monthrange(2026, m)[1]+1)]
    for d in ads:
        jp, ml = {}, sorted(list(MDS.keys()), key=lambda x: get_s(x, stt))
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
            except StopIteration: return None, d, p
        pl[d] = jp
    return pl, stt, sq

def make_ics(name, df_p):
    ics = ["BEGIN:VCALENDAR", "VERSION:2.0"]
    for d_str, row in df_p.iterrows():
        d_dt = pd.to_datetime(d_str)
        for p, m in row.items():
            if m == name:
                ics.append("BEGIN:VEVENT")
                ics.append("DTSTART;VALUE=DATE:" + d_dt.strftime("%Y%m%d"))
                ics.append("SUMMARY:Garde " + str(p))
                ics.append("END:VEVENT")
    ics.append("END:VCALENDAR")
    return "\n".join(ics)

# --- INTERFACE ---
if 'u' not in st.session_state:
    st.title("🏥 Connexion Planning")
    if not os.path.exists(DB): sd(pd.DataFrame({"Medecin":list(MDS.keys()),"MDP":["Doudoudragon"]*13}), DB)
    u_s = st.selectbox("Nom", list(MDS.keys()))
    pw = st.text_input("Code", type="password")
    if st.button("Valider"):
        u_df = gd(DB)
        if pw == str(u_df.loc[u_df["Medecin"]==u_s, "MDP"].values[0]):
            st.session_state.u = u_s
            st.rerun()
else:
    mn = ["📅 OFF & Agenda", "🚀 Générateur", "🔐 Code", "Sortie"]
    if st.session_state.u != "Christophe Angelo": mn.remove("🚀 Générateur")
    sel = st.sidebar.radio("Menu", mn)

    if sel == "📅 OFF & Agenda":
        st.header("Mes Indisponibilités & Calendrier")
        # Section ICS
        if os.path.exists(LP):
            df_full = pd.read_csv(LP, index_col=0)
            st.download_button("📥 Télécharger mon .ics", make_ics(st.session_state.u, df_full), st.session_state.u+".ics")
        
        st.divider()
        mo = st.selectbox("Mois à encoder", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
        df_o = gd(OF)
        c_o = set(df_o[df_o["Medecin"]==st.session_state.u]["Date_OFF"].tolist())
        
        h_cols = st.columns(7)
        for i, d_n in enumerate(FR_D): h_cols[i].info(d_n)
        
        for s in calendar.monthcalendar(2026, mo):
            cols = st.columns(7)
            for i, j in enumerate(s):
                if j != 0:
                    ds = "2026-" + str(mo).zfill(2) + "-" + str(j).zfill(2)
                    t = str(j) + (" ❌" if ds in c_o else " ✅")
                    if cols[i].button(t, key=ds, use_container_width=True):
                        if ds in c_o: df_o = df_o[~((df_o["Medecin"]==st.session_state.u)&(df_o["Date_OFF"]==ds))]
                        else: df_o = pd.concat([df_o, pd.DataFrame([{"Medecin":st.session_state.u,"Date_OFF":ds}])])
                        sd(df_o, OF); st.rerun()

    elif sel == "🚀 Générateur":
        st.header("Générateur Global")
        if st.button("Lancer la création"):
            vo = gd(OF).groupby("Medecin")["Date_OFF"].apply(list).to_dict()
            pl, stt, sq = run_gen(vo)
            if pl is None: st.error("Bloqué le " + str(stt) + " (" + str(sq) + ")")
            else:
                df_p = pd.DataFrame.from_dict(pl, orient='index')
                df_p.to_csv(LP)
                st.success("Planning OK")
                st.dataframe(df_p)
                res = [{"M":m, "H":stt[m], "Moy":round((stt[m]/22)+(7.68*MDS[m]["e"]),2), "Tot":sq[m]["T"], "WE":sq[m]["S"]+sq[m]["D"]+sq[m]["F"]} for m in MDS.keys()]
                st.table(pd.DataFrame(res))

    elif sel == "🔐 Code":
        st.header("Sécurité")
        np = st.text_input("Nouveau code", type="password")
        if st.button("Sauver"):
            u_df = gd(DB)
            u_df.loc[u_df["Medecin"]==st.session_state.u, "MDP"] = np
            sd(u_df, DB); st.success("Fait")

    elif sel == "Sortie":
        del st.session_state.u
        st.rerun()