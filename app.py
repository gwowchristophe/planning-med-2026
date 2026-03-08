with t2:
            st.subheader("Génération Dynamique via Google Sheets")
            if st.button("🚀 Lancer la génération (Lecture des règles...)"):
                with st.spinner("Synchronisation des règles et calcul..."):
                    # --- 1. CHARGEMENT DES DONNÉES ---
                    df_u = read_sheet("Users")
                    df_d = read_sheet("Desiderata")
                    df_r = read_sheet("Regles")
                    
                    if df_r.empty:
                        st.error("L'onglet 'Regles' est introuvable.")
                        st.stop()

                    df_u['ETP'] = df_u['ETP'].apply(lambda x: float(str(x).replace(',','.')) if x else 1.0)
                    meds = df_u.to_dict('records')
                    absences = set(df_d['Medecin'] + "_" + df_d['Date_OFF']) if not df_d.empty else set()
                    feries = ["2026-04-06", "2026-05-01", "2026-05-14", "2026-05-25", "2026-07-21", "2026-08-15"]
                    regles = df_r.set_index('Medecin').to_dict('index')
                    
                    dettes, planning_final = {m['Medecin']: 0.0 for m in meds}, []

                    # --- 2. BOUCLE DE GÉNÉRATION (Avril à Août) ---
                    for mois in range(4, 9):
                        jours = calendar.monthrange(2026, mois)[1]
                        for j in range(1, jours + 1):
                            date_c = datetime(2026, mois, j)
                            d_str = date_c.strftime("%Y-%m-%d")
                            is_we = date_c.weekday() >= 5
                            
                            # --- A. KENNEDY (Attribution par bloc le lundi) ---
                            if date_c.weekday() == 0:
                                j_jk = [0, 1, 2, 4] # Lun, Mar, Mer, Ven
                                bloc_ferie = any((date_c + timedelta(days=d)).strftime("%Y-%m-%d") in feries for d in j_jk)
                                
                                if not bloc_ferie:
                                    c_jk = [m for m in meds if regles.get(m['Medecin'], {}).get('Autorise_Kennedy') == 'OUI']
                                    dispos_jk = [m for m in c_jk if all(f"{m['Medecin']}_{(date_c + timedelta(days=d)).strftime('%Y-%m-%d')}" not in absences for d in j_jk)]
                                    
                                    if dispos_jk:
                                        elu_jk = min(dispos_jk, key=lambda x: dettes[x['Medecin']])
                                        for d in j_jk:
                                            d_str_jk = (date_c + timedelta(days=d)).strftime("%Y-%m-%d")
                                            planning_final.append([d_str_jk, "JK (Kennedy)", elu_jk['Medecin'], 8])
                                            dettes[elu_jk['Medecin']] += (8 / elu_jk['ETP'])

                            # --- B. POSTE JOUR (JM) - Uniquement en semaine hors férié ---
                            if not is_we and d_str not in feries:
                                # On exclut ceux déjà pris en JK aujourd'hui
                                deja_pris = [p[2] for p in planning_final if p[0] == d_str]
                                c_jm = [m for m in meds if m['Medecin'] not in deja_pris and f"{m['Medecin']}_{d_str}" not in absences]
                                
                                if c_jm:
                                    elu_jm = min(c_jm, key=lambda x: dettes[x['Medecin']])
                                    planning_final.append([d_str, "JM", elu_jm['Medecin'], 8])
                                    dettes[elu_jm['Medecin']] += (8 / elu_jm['ETP'])

                            # --- C. GARDE (GM ou GW) - Toujours quelqu'un ---
                            p_type, h_p = ("GW", 24) if (is_we or d_str in feries) else ("GM", 24)
                            cands_g = []
                            for m in meds:
                                nom = m['Medecin']
                                r = regles.get(nom, {})
                                
                                if (is_we or d_str in feries) and r.get('Autorise_Garde_WE') != 'OUI': continue
                                if (not is_we and d_str not in feries) and r.get('Autorise_Garde_Semaine') != 'OUI': continue
                                
                                # Sécurités : Pas déjà en JK ou JM, pas en OFF, Repos J+1
                                if any(p[0] == d_str and p[2] == nom for p in planning_final): continue
                                if f"{nom}_{d_str}" in absences: continue
                                h_hier = (date_c - timedelta(days=1)).strftime("%Y-%m-%d")
                                if any(p[0] == h_hier and p[2] == nom and "G" in p[1] for p in planning_final): continue
                                
                                cands_g.append(m)

                            if cands_g:
                                elu_g = min(cands_g, key=lambda x: dettes[x['Medecin']])
                                planning_final.append([d_str, p_type, elu_g['Medecin'], h_p])
                                dettes[elu_g['Medecin']] += (h_p / elu_g['ETP'])
                            else:
                                planning_final.append([d_str, p_type, "⚠️ VIDE", 0])

                    # --- 3. ENREGISTREMENT ---
                    df_res = pd.DataFrame(planning_final, columns=["Date", "Poste", "Medecin", "Heures"])
                    ws_p = get_gsheet().worksheet("Planning")
                    ws_p.clear()
                    ws_p.append_row(["Date", "Poste", "Medecin", "Heures"])
                    ws_p.append_rows(df_res.values.tolist())
                    st.success("Planning généré avec succès !")
                    st.balloons()
