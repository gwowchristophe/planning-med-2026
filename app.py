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

# --- FONCTIONS ---
def gd(f): return pd.read_csv(f) if os.path.exists(f) else pd.DataFrame()
def sd(df, f): df.to_csv(f, index=False)

def ok(n, d, p, pl, vo):
    ds = d.strftime("%Y-%m-%d")
    demain = (d + timedelta(days=1)).strftime("%Y-%m-%d")
    if ds in vo.get(n, []) or demain in vo.get(n, []): return False
    hier = d - timedelta(days=1)
    if hier in pl and n in pl[hier].values(): return False
    f8 = [d - timedelta(days=i) for i in range(2, 9)]
    nb_p = sum(1 for fd in f8 if fd in pl and n in pl[fd].values())
    if nb_p >= 2:
        avanthier = d - timedelta(days=2)
        if avanthier in pl and n in pl[avanthier].values(): return False
    if n == "Daryush Valadi":
        if p != "JM": return False
        is_week_a = (d.isocalendar()[1] % 2 == 0)
        valid = [1,2,3] if is_week_a else [2,3,4]
        return d.weekday() in valid
    if MDS[n]["t"] and p not in ["GW", "GM"]: return False
    if p == "JK" and (not MDS[n]["j"] or n == "PF Laterre"): return False
    return True

def run_gen(vo):
    pl, stt = {}, {m: 0 for m in MDS.keys()}
    sq = {m: {"T":0, "WE":0, "JK":0} for m in MDS.keys()}
    jk_cand = [m for m in MDS.keys() if MDS[m]["j"] == 1 and m not in ["PF Laterre", "Christian Davin", "Elisa Mastrodiscasa", "Raouf Sheta"]]
    jk_hist, jk_owner = [], None
    ads = [date(2026, m, j) for m in range(4,9) for j in range(1, calendar.monthrange(2026,m)[1]+1)]
    for d in ads:
        if d.weekday() == 0: jk_owner = None
        jp = {}
        f, s, di = (d in BH), (d.weekday()==5), (d.weekday()==6)
        is_we = (f or s or di)
        if not is_we and d.weekday() != 3:
            if jk_owner is None:
                pool = [m for m in jk_cand if m not in jk_hist]
                if not pool: jk_hist = []; pool = jk_cand
                pool = sorted(pool, key=lambda x: stt[x]/MDS[x]["e"])
                try:
                    jk_owner = next(m for m in pool if ok(m, d, "JK", pl, vo))
                    jk_hist.append(jk_owner)
                    sq[jk_owner]["JK"] += 1
                except StopIteration: pass
            if jk_owner:
                jp["JK"] = jk_owner
                stt[jk_owner] += V["JK"]
        postes = ["GW", "GM"]
        if not is_we: postes.append("JM")
        for p in postes:
            if p in jp: continue
            ml = sorted(list(MDS.keys()), key=lambda x: (stt[x]/MDS[x]["e"]) + (sq[x]["WE"] * 5))
            try:
                c = next(m for m in ml if m not in jp.values() and ok(m, d, p, pl, vo))
                jp[p], stt[c] = c, stt[c] + V[p]
                sq[c]["T"] += 1
                if is_we: sq[c]["WE"] += 1
            except StopIteration: return None, d, p
        pl[d] = jp
    return pl, stt, sq

def generate_ics_content(name, df_plan):
    ics = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//PlanningMed//2026//FR"]
    for d_str, row in df_plan.iterrows():
        for poste, med in row.items():
            if med == name:
                dt = d_str.replace("-", "")
                ics.append("BEGIN:VEVENT")
                ics.append(f"DTSTART;VALUE=DATE:{dt}")
                ics.append(f"SUMMARY:Garde {poste}")
                ics.append("END:VEVENT")
    ics.append("END:VCALENDAR")
    return "\n".join(ics)

# --- INTERFACE ---
if 'u' not in st.session_state:
    st.title("🏥 Planning Médical 2026")
    if not os.path.exists(DB): sd(pd.DataFrame({"Medecin":list(MDS.keys()),"MDP":["Doudoudragon"]*13}), DB)
    u_s = st.selectbox("Médecin", list(MDS.keys()))
    pw = st.text_input("Code", type="password")
    if st.button("Connexion"):
        u_df = gd(DB)
        if pw == str(u_df.loc[u_df["Medecin"]==u_s, "MDP"].values[0]):
            st.session_state.u = u_s
            st.rerun()
else:
    mn = ["📅 Mes OFF", "🚀 Générateur & ICS", "🔐 Code", "Sortie"]
    if st.session_state.u != "Christophe Angelo": mn.remove("🚀 Générateur & ICS")
    sel = st.sidebar.radio("Navigation", mn)

    if sel == "📅 Mes OFF":
        st.header("Encoder mes jours OFF")
        mo = st.selectbox("Mois", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
        df_o = gd(OF)
        c_o = set(df_o[df_o["Medecin"]==st.session_state.u]["Date_OFF"].tolist())
        cols_h = st.columns(7)
        for i, d_n in enumerate(FR_D): cols_h[i].info(d_n)
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

    elif sel == "🚀 Générateur & ICS":
        st.header("Administration du Planning")
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🔄 Lancer la simulation globale"):
                vo = gd(OF).groupby("Medecin")["Date_OFF"].apply(list).to_dict()
                pl, stt, sq = run_gen(vo)
                if pl is None: st.error(f"Bloqué le {stt} ({sq})")
                else:
                    df_p = pd.DataFrame.from_dict(pl, orient='index')
                    df_p.to_csv(LP)
                    st.success("Planning enregistré !")
                    st.dataframe(df_p)
        
        with col2:
            st.subheader("Exporter les agendas")
            if os.path.exists(LP):
                df_p = pd.read_csv(LP, index_col=0)
                target = st.selectbox("Choisir un collègue", list(MDS.keys()))
                ics_text = generate_ics_content(target, df_p)
                st.download_button(f"📥 Télécharger l'ICS de {target}", ics_text, f"{target}.ics")
            else:
                st.info("Générez d'abord un planning pour exporter les ICS.")

        if os.path.exists(LP):
            st.divider()
            st.subheader("Bilan d'équité")
            # Recalcul des stats pour affichage
            df_p = pd.read_csv(LP, index_col=0)
            stats = []
            for m in MDS.keys():
                h = sum(V[p] for d, r in df_p.iterrows() for p, med in r.items() if med == m)
                stats.append({"Médecin": m, "Heures": h, "Moy/Sem": round((h/22)+(7.68*MDS[m]["e"]), 2)})
            st.table(pd.DataFrame(stats).sort_values("Heures"))

    elif sel == "🔐 Code":
        np = st.text_input("Nouveau code", type="password")
        if st.button("Enregistrer"):
            u_df = gd(DB); u_df.loc[u_df["Medecin"]==st.session_state.u, "MDP"] = np
            sd(u_df, DB); st.success("OK")

    elif sel == "Sortie":
        if 'u' in st.session_state: del st.session_state.u
        st.rerun()