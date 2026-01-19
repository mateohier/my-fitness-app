import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta
import os

# ===============================
# Configuration & Constantes
# ===============================
st.set_page_config(page_title="Fitness Mobile", layout="wide")

MET = {"natation": 8.0, "marche": 3.5, "course": 9.8, "renforcement": 6.0}
KCAL_PAR_KG_GRAISSE = 7700
DATA_FILE = "data.csv"

# ===============================
# Fonctions de calcul
# ===============================
def recalculer_ensemble_donnees(df):
    if df.empty: return df
    df = df.sort_values("date").reset_index(drop=True)
    mg_estimee_list, cal_perte_list, calories_cumulees = [], [], 0
    
    for i, row in df.iterrows():
        poids, cal_depense = row['poids'], row['calories_depensees']
        if i == 0:
            mg_actuelle = 0.20 * poids # Estimation par défaut
        else:
            mg_veille = mg_estimee_list[i-1]
            perte_kg = cal_depense / KCAL_PAR_KG_GRAISSE
            mg_actuelle = min(mg_veille, max(mg_veille - perte_kg, 0.05 * poids))
        
        mg_estimee_list.append(mg_actuelle)
        delta_mg = (mg_estimee_list[i-1] - mg_actuelle) if i > 0 else 0
        calories_cumulees += (delta_mg * KCAL_PAR_KG_GRAISSE)
        cal_perte_list.append(calories_cumulees)
        
    df["mg_kg"] = mg_estimee_list
    df["cumul_kcal"] = cal_perte_list
    return df

# ===============================
# Chargement des données
# ===============================
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["date", "poids", "natation_min", "marche_min", "course_min", "renforcement_min", "calories_depensees"])
else:
    df = pd.read_csv(DATA_FILE)
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

# ===============================
# SIDEBAR : SAISIE & GESTION
# ===============================
st.sidebar.header("📥 Saisie du jour")
date_saisie = st.sidebar.date_input("Date", date.today())
poids_saisie = st.sidebar.number_input("Poids (kg)", value=70.0, step=0.1)

st.sidebar.subheader("Activités (min)")
n_min = st.sidebar.number_input("🏊 Natation", 0)
m_min = st.sidebar.number_input("🚶 Marche", 0)
c_min = st.sidebar.number_input("🏃 Course", 0)
r_min = st.sidebar.number_input("💪 Muscu", 0)

obj_poids = st.sidebar.number_input("🎯 Objectif (kg)", value=65.0, step=0.5)

if st.sidebar.button("💾 Enregistrer"):
    cal_dep = (n_min/60*MET["natation"]*poids_saisie + m_min/60*MET["marche"]*poids_saisie + 
               c_min/60*MET["course"]*poids_saisie + r_min/60*MET["renforcement"]*poids_saisie)
    
    new_entry = pd.DataFrame([{
        "date": str(date_saisie), "poids": poids_saisie, 
        "natation_min": n_min, "marche_min": m_min, "course_min": c_min, "renforcement_min": r_min,
        "calories_depensees": cal_dep
    }])
    
    # Mise à jour
    df = pd.concat([df[df['date'] != str(date_saisie)], new_entry], ignore_index=True)
    df = recalculer_ensemble_donnees(df)
    df.to_csv(DATA_FILE, index=False)
    st.sidebar.success("Données sauvegardées !")
    st.rerun()

# --- OPTION SUPPRESSION ---
st.sidebar.markdown("---")
if not df.empty:
    st.sidebar.subheader("🗑️ Administration")
    ligne_a_suppr = st.sidebar.selectbox("Ligne à supprimer", df.sort_values("date", ascending=False)["date"])
    if st.sidebar.button("Supprimer cette date"):
        df = df[df['date'] != ligne_a_suppr]
        df = recalculer_ensemble_donnees(df)
        df.to_csv(DATA_FILE, index=False)
        st.sidebar.warning(f"Date {ligne_a_suppr} supprimée")
        st.rerun()

# ===============================
# DASHBOARD PRINCIPAL
# ===============================
st.title("🏃‍♂️ My Fitness Journey")

if not df.empty:
    df = recalculer_ensemble_donnees(df)
    df_sorted = df.sort_values("date")
    
    # 1. KPI
    last_p = df_sorted["poids"].iloc[-1]
    total_g = round(df_sorted["cumul_kcal"].iloc[-1] / 7700, 2)
    
    col1, col2 = st.columns(2)
    col1.metric("Poids Actuel", f"{last_p} kg")
    col2.metric("Graisse Brûlée", f"{total_g} kg")

    # 2. Prédiction
    diff = last_p - obj_poids
    if diff > 0 and len(df) >= 2:
        df_rec = df_sorted.tail(7)
        perte = df_rec["poids"].iloc[0] - df_rec["poids"].iloc[-1]
        jours = (pd.to_datetime(df_rec["date"].iloc[-1]) - pd.to_datetime(df_rec["date"].iloc[0])).days
        if perte > 0 and jours > 0:
            vitesse = perte / jours
            est_jours = int(diff / vitesse)
            st.info(f"📅 Objectif dans environ **{est_jours} jours** (le {(date.today() + timedelta(days=est_jours)).strftime('%d/%m/%Y')})")

    # 3. Graphiques
    tab1, tab2 = st.tabs(["📉 Évolution Poids", "🔥 Cumul Graisse"])
    with tab1:
        fig1, ax1 = plt.subplots(figsize=(10, 4))
        ax1.plot(df_sorted["date"], df_sorted["poids"], marker='o', color='#3498db', linewidth=2)
        ax1.axhline(y=obj_poids, color='r', linestyle='--', label="Objectif")
        plt.xticks(rotation=45)
        st.pyplot(fig1)
        
    with tab2:
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        perte_kg_plot = df_sorted["cumul_kcal"] / 7700
        ax2.fill_between(df_sorted["date"], perte_kg_plot, color="#2ecc71", alpha=0.3)
        ax2.plot(df_sorted["date"], perte_kg_plot, color="#27ae60", linewidth=2)
        ax2.set_ylabel("Kilogrammes")
        plt.xticks(rotation=45)
        st.pyplot(fig2)

    # 4. Historique détaillé
    with st.expander("📄 Historique des données"):
        st.dataframe(df_sorted.sort_values("date", ascending=False), use_container_width=True)
else:
    st.info("Utilisez le menu à gauche pour entrer votre premier poids !")