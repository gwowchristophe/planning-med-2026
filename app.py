else:
    # --- BARRE LATÉRALE ---
    st.sidebar.success(f"Connecté : Dr. {st.session_state.u}")
    
    # Menu de navigation
    menu = ["📅 Mes Désiderata", "🔄 Échanges", "🚀 Admin (Planning)", "🔑 Mot de passe"]
    # Option Admin uniquement pour vous
    if st.session_state.u != "Christophe Angelo":
        menu.remove("🚀 Admin (Planning)")
        
    choix = st.sidebar.radio("Navigation", menu)

    if st.sidebar.button("Déconnexion"):
        del st.session_state.u
        st.rerun()

    # --- 1. ONGLET DÉSIDERATA ---
    if choix == "📅 Mes Désiderata":
        st.header("Vos Désiderata de congés 2026")
        st.info("Cliquez sur un jour pour basculer entre Présent ✅ et Absent ❌")

        # Sélection du mois (Avril à Août 2026 par exemple)
        mois_noms = {4: "Avril", 5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août"}
        mois_sel = st.selectbox("Mois", options=list(mois_noms.keys()), format_func=lambda x: mois_noms[x])

        # Chargement des données actuelles
        df_desid = read_sheet("Desiderata")
        
        # On filtre les jours déjà pris par l'utilisateur connecté
        # On s'assure que les dates sont comparées au format texte YYYY-MM-DD
        jours_off = set(df_desid[df_desid["Medecin"] == st.session_state.u]["Date_OFF"].astype(str).tolist())

        # Affichage du calendrier
        cal = calendar.monthcalendar(2026, mois_sel)
        semaines = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        
        # En-tête des jours
        cols_header = st.columns(7)
        for i, jour_nom in enumerate(semaines):
            cols_header[i].write(f"**{jour_nom}**")

        # Grille de boutons
        for semaine in cal:
            cols = st.columns(7)
            for i, jour in enumerate(semaine):
                if jour != 0:
                    date_str = f"2026-{str(mois_sel).zfill(2)}-{str(jour).zfill(2)}"
                    est_off = date_str in jours_off
                    
                    label = f"{jour} {'❌' if est_off else '✅'}"
                    
                    if cols[i].button(label, key=date_str):
                        sh = get_gsheet()
                        ws = sh.worksheet("Desiderata")
                        
                        if est_off:
                            # Supprimer la ligne si on repasse en présent
                            # On recharge pour trouver la bonne ligne
                            all_data = ws.get_all_values()
                            for idx, row in enumerate(all_data):
                                if row[0] == st.session_state.u and row[1] == date_str:
                                    ws.delete_rows(idx + 1)
                                    break
                        else:
                            # Ajouter une ligne si on passe en absent
                            ws.append_row([st.session_state.u, date_str])
                        
                        st.rerun()

    # --- 2. ONGLET ADMIN (Aperçu global) ---
    elif choix == "🚀 Admin (Planning)":
        st.header("Vue d'ensemble (Admin)")
        df_all = read_sheet("Desiderata")
        if not df_all.empty:
            st.write("Récapitulatif de toutes les absences :")
            st.dataframe(df_all)
        else:
            st.write("Aucun desiderata encodé pour le moment.")

    # --- 3. AUTRES ONGLETS (À remplir plus tard) ---
    else:
        st.write("Cette section est en cours de développement.")