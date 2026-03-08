import streamlit as st
import pandas as pd
import os, calendar
from datetime import date, timedelta
import holidays

# --- CONFIGURATION ---
st.set_page_config(page_title="Planning Médical 2026", layout="wide")
V = {"GW": 24, "GM": 24, "JK": 9, "JM": 7}
DB, OF, LP, ECH = "users_db.csv", "desiderata_db.csv", "last_plan.csv", "echanges_db.csv"
BH = holidays.BE(years=2026)
FR_D = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

MDS = {
    "Alexandra Warnant": {"e": 0.8, "j": 1, "t": 0}, "Alfredo Vieira": {"e": 0.8, "j": 1, "t": 0},
    "Camie Dupuis": {"e": 0.8, "j": 1, "t": 0}, "Christian Davin": {"e": 0.8, "j": 0, "t": 1},
    "Christophe Angelo": {"e": 0.6, "j": 1, "t": 0}, "Daryush Valadi": {"e": 0.4, "j": 0, "t": 0},
    "Elisa Mastrodiscasa": {"e": 0.8, "j": 0, "t": 1}, "Gauthier Nendumba": {"e": 0.8, "j": 1, "t": 0},
    "Julie Henrie": {"e": 0.6, "j": 1, "t": 0}, "Martin Hachez": {"e": 0.8, "j": 1, "t": 0},
    "PF Laterre": {"e": 0.8, "j": 0, "t": 0}, "Raouf Sheta": {"e": 0.8, "j": 0, "t": 1},
    "Simon Van Migem": {"e": 0.8, "j": 1, "t": 0}
}

# --- INITIALISATION DES FICHIERS (Anti-KeyError) ---
def init_files():
    if not os.path.exists(DB):
        pd.DataFrame({"Medecin": list(MDS.keys()), "MDP": ["Doudoudragon"]*13}).to_csv(DB, index=False)
    if not os.path.exists(OF):
        pd.DataFrame(columns=["Medecin", "Date_OFF"]).to_csv(OF, index=False)
    if not os.path.exists(ECH):
        pd.DataFrame(columns=["Emetteur", "Destinataire", "Date", "Poste", "Statut"]).to_csv(ECH, index=False)

init_files()

def gd(f): return pd.read_csv(f)
def sd(df, f): df.to_csv(f, index=False)

def check_conflit(name, date_str, pl_df):
    target_dt = pd.to_datetime(date_str).date()
    if name in pl_df.loc[date_str].values: return "Déjà de poste ce jour."
    hier = (target_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    if hier in pl_df.index and name in pl_df.loc[hier].values: return "Repos 24h (était de garde la veille)."
    demain = (target_dt + timedelta(days=1)).strftime("%Y-%m-%d")
    if demain in pl_df.index and name in pl_df.loc[demain].values: return "Repos 24h (garde le lendemain)."
    return None

# --- MOTEUR DE GÉNÉRATION ---
def run_gen(vo):
    pl, stt = {}, {m: 0 for m in MDS.keys()}
    sq = {m: {"T":0, "WE":0, "JK":0, "G":0} for m in MDS.keys()}
    jk_cand = [m for m in MDS.keys() if MDS[m]["j"] == 1 and m not in ["PF Laterre", "Christian Davin", "Elisa Mastrodiscasa", "Raouf Sheta"]]
    jk_hist, jk_owner = [], None
    ads = [date(2026, m, j) for m in range(4,9) for j in range(1, calendar.monthrange(2026,m)[1]+1)]
    
    for d in ads:
        if d.weekday() == 0: jk_owner = None
        jp = {}
        ds = d.strftime("%Y-%m-%d")
        f, s, di = (d in BH), (d.weekday()==5), (d.weekday()==6)
        is_we = (f or s or di)

        # Kennedy (JK)
        if not is_we and d.weekday() != 3:
            if jk_owner is None:
                pool = [m for m in jk_cand if m not in jk_hist]
                if not pool: jk_hist = []; pool = jk_cand
                pool = sorted(pool, key=lambda x: stt[x]/MDS[x]["e"])
                try:
                    jk_owner = next(m for m in pool if ds not in vo.get(m, []))
                    jk_hist.append(jk_owner)
                except StopIteration: pass
            if jk_owner:
                jp["JK"] = jk_owner
                stt[jk_owner] += V["JK"]
                sq[jk_owner]["JK"] += 1

        # Gardes (GW, GM, JM)
        postes = ["GW", "GM"] + (["JM"] if not is_we else [])
        for p in postes:
            if p in jp: continue
            ml = sorted(list(MDS.keys()), key=lambda x: (stt[x]/MDS[x]["e"]) + (sq[x]["WE"] * 5))
            try:
                c = next(m for m in ml if m not in jp.values() and ds not in vo.get(m, []))
                jp[p], stt[c] = c, stt[c] + V[p]
                if p in ["GW", "GM"]: sq[c]["G"] += 1
                if is_we: sq[c]["WE"] += 1
            except StopIteration: pass
        pl[ds] = jp
    return pl

# --- INTERFACE ---
if 'u' not in st.session_state:
    st.title("🏥 Planning Médical 2026")
    u_s = st.selectbox("Médecin", list(MDS.keys()))
    pw = st.text_input("Code", type="password")
    if st.button("Connexion"):
        u_df = gd(DB)
        if pw == str(u_df.loc[u_df["Medecin"]==u_s, "MDP"].values[0]):
            st.session_state.u = u_s
            st.rerun()
else:
    df_e = gd(ECH)
    # Filtrage sécurisé des demandes
    mes_demandes = df_e[(df_e["Destinataire"] == st.session_state.u) & (df_e["Statut"] == "ATTENTE")]
    nb_notif = len(mes_demandes)
    
    label_echange = f"🔄 Échanges ({nb_notif})" if nb_notif > 0 else "🔄 Échanges"
    mn = ["📅 Mes OFF", label_echange, "🚀 Admin", "🔐 Code", "Sortie"]
    if st.session_state.u != "Christophe Angelo": mn.remove("🚀 Admin")
    sel = st.sidebar.radio("Menu", mn)

    if sel == "📅 Mes OFF":
        st.header("Mes jours OFF")
        mo = st.selectbox("Mois", [4,5,6,7,8], format_func=lambda x: calendar.month_name[x])
        df_o = gd(OF)
        c_o = set(df_o[df_o["Medecin"]==st.session_state.u]["Date_OFF"].tolist())
        for s in calendar.monthcalendar(2026, mo):
            cols = st.columns(7)
            for i, j in enumerate(s):
                if j != 0:
                    ds = f"2026-{str(mo).zfill(2)}-{str(j).zfill(2)}"
                    if cols[i].button(str(j) + (" ❌" if ds in c_o else " ✅"), key=ds):
                        if ds in c_o: df_o = df_o[~((df_o["Medecin"]==st.session_state.u)&(df_o["Date_OFF"]==ds))]
                        else: df_o = pd.concat([df_o, pd.DataFrame([{"Medecin":st.session_state.u,"Date_OFF":ds}])])
                        sd(df_o, OF); st.rerun()

    elif label_echange in sel:
        st.header("Centre d'échanges")
        if nb_notif > 0:
            st.subheader("📬 Demandes à valider")
            for idx, row in mes_demandes.iterrows():
                with st.expander(f"De {row['Emetteur']} : Garde du {row['Date']}"):
                    st.write(f"Poste : **{row['Poste']}**")
                    if st.button("✅ Accepter", key=f"acc_{idx}"):
                        df_p = gd(LP).set_index("Unnamed: 0")
                        df_p.at[row['Date'], row['Poste']] = st.session_state.u
                        df_p.reset_index().to_csv(LP, index=False)
                        df_e.at[idx, "Statut"] = "VALIDE"
                        sd(df_e, ECH)
                        st.success("Planning mis à jour !")
                        st.rerun()
                    if st.button("❌ Refuser", key=f"ref_{idx}"):
                        df_e.at[idx, "Statut"] = "REFUSE"
                        sd(df_e, ECH); st.rerun()

        st.divider()
        st.subheader("📤 Envoyer une demande")
        if os.path.exists(LP):
            df_p = gd(LP).set_index("Unnamed: 0")
            mes_g = [f"{d} | {p}" for d in df_p.index for p in df_p.columns if df_p.at[d, p] == st.session_state.u]
            g_sel = st.selectbox("Ma garde à donner", mes_g)
            dest = st.selectbox("Remplaçant", [m for m in MDS.keys() if m != st.session_state.u])
            if st.button("Proposer l'échange"):
                dt_s, p_s = g_sel.split(" | ")
                conflit = check_conflit(dest, dt_s, df_p)
                if conflit: st.error(conflit)
                else:
                    new_r = pd.DataFrame([{"Emetteur": st.session_state.u, "Destinataire": dest, "Date": dt_s, "Poste": p_s, "Statut": "ATTENTE"}])
                    sd(pd.concat([df_e, new_r]), ECH)
                    st.info("Demande envoyée !")
        else: st.info("Planning non publié.")

    elif sel == "🚀 Admin":
        st.header("Gestion Christophe")
        if st.button("🚀 Générer/Publier le Planning"):
            vo = gd(OF).groupby("Medecin")["Date_OFF"].apply(list).to_dict()
            res = run_gen(vo)
            pd.DataFrame.from_dict(res, orient='index').to_csv(LP)
            st.rerun()
        
        if os.path.exists(LP):
            df_p = gd(LP).set_index("Unnamed: 0")
            st.dataframe(df_p)
            st.subheader("Équité")
            stats = []
            for m in MDS.keys():
                h = sum(V[p] for d, r in df_p.iterrows() for p, med in r.items() if med == m and p in V)
                stats.append({"Médecin": m, "Heures": h, "Moy/Sem": round((h/22)+(7.68*MDS[m]["e"]), 2)})
            st.table(pd.DataFrame(stats).sort_values("Heures"))

    elif sel == "Sortie":
        del st.session_state.u
        st.rerun()