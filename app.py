import streamlit as st
import pandas as pd
import os, calendar, random, io
from datetime import date, datetime, timedelta
import holidays

st.set_page_config(page_title="Plan 2026", layout="wide")
V = {"GW": 24, "GM": 24, "JK": 9, "JM": 7}
DB, OF = "users_db.csv", "desiderata_db.csv"
BH = holidays.BE(years=2026)

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

def get_s(n, stt):
    return stt[n] / MDS[n]["e"]

# Interface
if 'u' not in st.session_state:
    st.title("🏥 Login")
    if not os.path.exists(DB):
        df_i = pd.DataFrame({"Medecin": list(MDS.keys()), "MDP": ["Doudoudragon"]*13})
        sd(df_i, DB)
    u_df = gd(DB)
    u_s = st.selectbox("Nom", list(MDS.keys()))
    pw = st.text_input("Code", type="password")
    if st.button("OK"):
        v = str(u_df.loc[u_df["Medecin"]==u_s, "MDP"].values[0])
        if pw == v:
            st.session_state.u = u_s
            st.rerun()
else:
    mn = ["📅 OFF", "🔐 Code", "Sortie"]
    if st.session_state.u == "Christophe Angelo": mn.insert(1, "🚀 Go")
    sel = st.sidebar.radio("Menu", mn)

    if sel == "📅 OFF":
        st.subheader("Indispos")
        mo = st.selectbox("Mois", [4,5,6,7,8])
        df = gd(OF)
        c_o = set(df[df["Medecin"]==st.session_state.u]["Date_OFF"].tolist())
        cl = calendar.monthcalendar(2026, mo)
        for s in cl:
            cols = st.columns(7)
            for i, j in enumerate(s):
                if j != 0:
                    ds = f"2026-{mo:02d}-{j:02d}"
                    t = f"{j} {'X' if ds in c_o else 'V'}"
                    if cols[i].button(t, key=ds):
                        if ds in c_o: df = df[~((df["Medecin"]==st.session_state.u)&(df["Date_OFF"]==ds))]
                        else: df = pd.concat([df, pd.DataFrame([{"Medecin":st.session_state.u,"Date_OFF":ds}])])
                        sd(df, OF); st.rerun()

    elif sel == "🚀 Go":
        if st.button("Générer"):
            vo = gd(OF).groupby("Medecin")["Date_OFF"].apply(list).to_dict()
            pl, stt = {}, {m: 0 for m in MDS.keys()}
            sq = {m: {"S":0,"D":0,"F":0} for m in MDS.keys()}
            ads = []
            for m_i in range(4, 9):
                l_j = calendar.monthrange(2026, m_i)[1]
                for j in range(1, l_j+1): ads.append(date(2026, m_i, j))
            
            res_ok = True
            for d in ads:
                jp = {}
                ml = list(MDS.keys())
                ml.sort(key=lambda x: get_s(x, stt))
                f, s, di = (d in BH), (d.weekday()==5), (d.weekday()==6)
                for p in ["GW", "GM", "JK", "JM"]:
                    if (f or s or di) and p in ["JK", "JM"]: continue
                    if not (f or s or di) and p == "JK" and d.weekday() == 3: continue
                    try:
                        c = next(m for m in ml if m not in jp.values() and ok(m,d,p,pl,vo))
                        jp[p] = c
                        stt[c] += V[p]
                        if s: sq[c]["S"] += 1
                        if di: sq[c]["D"] += 1
                        if f: sq[c]["F"] += 1
                    except StopIteration: res_ok = False; break
                if not res_ok: break
                pl[d] = jp
            
            if not res_ok: st.error("Trop de OFF")
            else:
                st.dataframe(pd.DataFrame.from_dict(pl, orient='index'))
                res = []
                for m in MDS.keys():
                    res.append({"Nom": m, "H": stt[m], "S": sq[m]["S"], "D": sq[m]["D"]})
                st.table(pd.DataFrame(res))

    elif sel == "🔐 Code":
        np = st.text_input("New", type="password")
        if st.button("Save"):
            u_df = gd(DB)
            u_df.loc[u_df["Medecin"]==st.session_state.u, "MDP"] = np
            sd(u_df, DB); st.success("OK")

    elif sel == "Sortie":
        del st.session_state.u
        st.rerun()
