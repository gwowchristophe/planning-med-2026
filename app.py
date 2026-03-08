import streamlit as st
import pandas as pd
import os, calendar, random, io
from datetime import date, datetime, timedelta
import holidays

st.set_page_config(page_title="Planning Médical 2026", layout="wide")
V = {"GW": 24, "GM": 24, "JK": 9, "JM": 7}
DB, OF = "users_db.csv", "desiderata_db.csv"
BH = holidays.BE(years=2026)
FR_D = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

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

def get_s(n, stt): return stt[n] / MDS[n]["e"]

def color_we(row):
    d = row.name
    if d.weekday() >= 5 or d in BH:
        return ['background-color: #f0f2f6'] * len(row)
    return [''] * len(row)

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
else:
    mn = ["📅 Mes OFF", "🚀 Générateur Global", "🔐 Mon Code", "Sortie"]
    if st.session_state.u != "Christophe Angelo": mn.remove("🚀 Générateur Global")
    sel = st.sidebar.radio("Navigation", mn)

    if sel == "📅 Mes OFF":
        st.header("Gestion des Indisponibilités")
        mo = st.selectbox("Choisir le mois", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
        df = gd(OF)
        c_o = set(df[df["Medecin"]==st.session_state.u]["Date_OFF"].tolist())
        
        # Affichage du calendrier avec jours de la semaine
        cols_h = st.columns(7)
        for i, d_n in enumerate(FR_D): cols_h[i].write(f"**{d_n}**")
        
        cl = calendar.monthcalendar(2026, mo)
        for s in cl:
            cols = st.columns(7)
            for i, j in enumerate(s):
                if j != 0:
                    ds = f"2026-{mo:02d}-{j:02d}"
                    t = f"{j}\n{'❌' if ds in c_o else '✅'}"
                    if cols[i].button(t, key=ds, use_container_width=True):
                        if ds in c_o: df = df[~((df["Medecin"]==st.session_state.u)&(df["Date_OFF"]==ds))]
                        else: df = pd.concat([df, pd.DataFrame([{"Medecin":st.session_state.u,"Date_OFF":ds}])])
                        sd(df, OF); st.rerun()

    elif sel == "🚀 Générateur Global":
        st.header("Génération 5 mois (Avril-Août)")
        if st.button("Lancer la simulation équilibrée"):
            vo = gd(OF).groupby("Medecin")["Date_OFF"].apply(list).to_dict()
            pl, stt = {}, {m: 0 for m in MDS.keys()}
            sq = {m: {"S":0,"D":0,"F":0,"TotG":0} for m in MDS.keys()}
            ads = [date(2026, m, d) for m in range(4, 9) for d in range(1, calendar.monthrange(2026, m)[1]+1)]
            
            res_ok = True
            for d in ads:
                jp = {}
                ml = sorted(list(MDS.keys()), key=lambda x: get_s(x, stt))
                f, s, di = (d in BH), (d.weekday()==5), (d.weekday()==6)
                for p in ["GW", "GM", "JK", "JM"]:
                    if (f or s or di) and p in ["JK", "JM"]: continue
                    if not (f or s or di) and p == "JK" and d.weekday() == 3: continue
                    try:
                        c = next(m for m in ml if m not in jp.values() and ok(m,d,p,pl,vo))
                        jp[p] = c
                        stt[c] += V[p]
                        sq[c]["TotG"] += 1
                        if s: sq[c]["S"] += 1
                        if di: sq[c]["D"] += 1
                        if f: sq[c]["F"] += 1
                    except StopIteration: res_ok = False; break
                if not res_ok: break
                pl[d] = jp
            
            if not res_ok: st.error("Impossible : Conflit de contraintes (OFF trop nombreux)")
            else:
                df_p = pd.DataFrame.from_dict(pl, orient='index')
                st.dataframe(df_p.style.apply(color_we, axis=1), height=500)
                
                # Tableau récapitulatif enrichi
                res = []
                for m in MDS.keys():
                    penible = sq[m]["S"] + sq[m]["D"] + sq[m]["F"]
                    res.append({
                        "Médecin": m, "Heures": stt[m], "Moy/Sem": round(stt[m]/22, 1),
                        "Total Gardes": sq[m]["TotG"], "Gardes WE/Fé": penible,
                        "Sam": sq[m]["S"], "Dim": sq[m]["D"], "Fé": sq[m]["F"]
                    })
                st.subheader("Bilan d'équité détaillé")
                st.table(pd.DataFrame(res))

    elif sel == "🔐 Mon Code":
        np = st.text_input("Nouveau code", type="password")
        if st.button("Enregistrer"):
            u_df = gd(DB); u_df.loc[u_df["Medecin"]==st.session_state.u, "MDP"] = np
            sd(u_df, DB); st.success("Code mis à jour avec succès")

    elif sel == "Sortie":
        del
