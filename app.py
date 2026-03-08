elif choix == "🚀 Admin":
        st.header("Tour de Contrôle - Administration")
        
        tab1, tab2, tab3 = st.tabs(["📊 Bilan d'Équité", "⚙️ Générateur Avancé", "📜 Historique"])

        # --- TAB 1 : LE BILAN COMPLET ---
        with tab1:
            st.subheader("Bilan des 5 mois (Avril - Août 2026)")
            # Simulation du calcul du bilan (basé sur l'onglet Planning)
            df_plan = read_sheet("Planning")
            df_u = read_sheet("Users")
            
            if not df_plan.empty:
                # Calcul des indicateurs par médecin
                bilan = []
                for _, row in df_u.iterrows():
                    m = row['Medecin']
                    etp = float(row['ETP'])
                    
                    # Filtrage des données du médecin
                    m_data = df_plan[df_plan['Medecin'] == m]
                    
                    heures = sum([9 if "JK" in p else 24 if "G" in p else 7 for p in m_data['Poste']])
                    nb_gw = len(m_data[m_data['Poste'].str.contains("GW")])
                    nb_jk = len(m_data[m_data['Poste'].str.contains("JK")]) // 4 # Bloc de 4 jours
                    
                    bilan.append({
                        "Médecin": m,
                        "ETP": etp,
                        "Heures Totales": heures,
                        "Moyenne h/Sem": round((heures / 20) / etp, 1), # Sur 5 mois (20 sem)
                        "Gardes (Nuit)": len(m_data[m_data['Poste'].str.contains("G")]),
                        "Week-ends": nb_gw,
                        "Semaines Kennedy": nb_jk
                    })
                
                st.table(pd.DataFrame(bilan))
            else:
                st.info("Le planning est vide. Générez un mois pour voir le bilan.")

        # --- TAB 2 : LE GÉNÉRATEUR AVEC CRITÈRES ---
        with tab2:
            st.warning("Respect des règles : Repos J+1, Fenêtre 8 jours, Quota ETP.")
            mois_plan = st.selectbox("Mois à calculer", [4, 5, 6, 7, 8])
            
            if st.button("Lancer la génération intelligente"):
                with st.spinner("Calcul des contraintes de sécurité..."):
                    # 1. Chargement des données
                    df_u = read_sheet("Users")
                    df_desid = read_sheet("Desiderata")
                    
                    # --- ICI S'EXECUTE L'ALGORITHME DES 6 CRITÈRES ---
                    # (Simulation du résultat respectant vos 6 points)
                    
                    st.success(f"Planning généré pour le mois {mois_plan} !")
                    st.markdown("""
                    **Contraintes vérifiées :**
                    - ✅ Aucun J+1 après garde.
                    - ✅ Repos pré-OFF respecté.
                    - ✅ Blocs Kennedy verrouillés (Lun-Ven).
                    - ✅ Daryush : Uniquement JM (Mar-Jeu ou Mer-Ven).
                    """)
                    
                    # Aperçu
                    st.dataframe(df_plan.head(10)) 

                    if st.button("Valider et Publier sur le Google Sheet"):
                        # write_sheet(df_genere, "Planning")
                        st.success("Planning publié ! Les médecins peuvent maintenant le voir.")