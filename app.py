import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import date, timedelta

# ===============================
# Configuration & Constantes
# ===============================
st.set_page_config(page_title="Fitness Multi-Profils", layout="wide")

MET = {"natation": 8.0, "marche": 3.5, "course": 9.8, "renforcement": 6.0}
KCAL_PAR_KG_GRAISSE = 7700
BASE_DIR = "user_data"

if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

# ===============================
# Logique de Calcul
# ===============================
def recalculer_ensemble_donnees(df):
    if df.empty: return df
    df = df.sort_values("date").reset_index(drop=True)
    mg_estimee_list, cal_perte_list, calories_cumulees = [], [], 0
    
    for i, row in df.iterrows():
        poids, cal_depense = row['poids'], row['calories_depensees']
        if i == 0:
            mg_actuelle = 0.22 * poids 
        else:
            mg_veille = mg_estimee_list[i-1]
            mg_actuelle = min(mg_veille, max(mg_veille - (cal_depense / KCAL_PAR_KG_GRAISSE), 0.05 * poids))
        
        mg_estimee_list.append(mg_actuelle)
        delta_mg = (mg_estimee_list[i-1] - mg_actuelle) if i > 0 else 0
        calories_cumulees += (delta_mg * KCAL_PAR_KG_GRAISSE)
        cal_perte_list.append(calories_cumulees)
        
    df["mg_kg"] = mg_estimee_list
    df["cumul_kcal"] = cal_perte_list
    return df

# ===============================
# GESTION DES PROFILS
# ===============================
st.sidebar.title("👥 Profils")
existing_profiles = [f.replace(".csv", "") for f in os.listdir(BASE_DIR) if f.endswith(".csv")]
if not existing_profiles: existing_profiles = ["Defaut"]

user_name = st.sidebar.selectbox("Choisir un profil :", existing_profiles)
USER_FILE = os.path.join(BASE_DIR, f"{user_name}.csv")

with st.sidebar.expander("➕ Créer un nouveau profil"):
    new_user = st.text_input("Nom de l'utilisateur")
    if st.button("Ajouter"):
        if new_user:
            pd.DataFrame(columns=["date", "poids", "natation_min", "marche_min", "course_min", "renforcement_min", "calories_depensees", "objectif"]).to_csv(os.path.join(BASE_DIR, f"{new_user}.csv"), index=False)
            st.rerun()

# Chargement des données
if os.path.exists(USER_FILE):
    df = pd.read_csv(USER_FILE)
    if not df.empty: df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
else:
    df = pd.DataFrame(columns=["date", "poids", "natation_min", "marche_min", "course_min", "renforcement_min", "calories_depensees", "objectif"])

# ===============================
# SAISIE DU JOUR
# ===============================
st.sidebar.markdown("---")
st.sidebar.subheader(f"📥 Saisie : {user_name}")
date_saisie = st.sidebar.date_input("Date", date.today())
poids_saisie = st.sidebar.number_input("Poids (kg)", value=70.0, step=0.1)
last_obj = df["objectif"].iloc[-1] if not df.empty else 65.0
obj_poids = st.sidebar.number_input("🎯 Objectif (kg)", value=float(last_obj), step=0.5)

n_min = st.sidebar.number_input("🏊 Natation (min)", 0)
m_min = st.sidebar.number_input("🚶 Marche (min)", 0)
c_min = st.sidebar.number_input("🏃 Course (min)", 0)
r_min = st.sidebar.number_input("💪 Muscu (min)", 0)

if st.sidebar.button("💾 Enregistrer"):
    cal_dep = (n_min/60*MET["natation"]*poids_saisie + m_min/60*MET["marche"]*poids_saisie + 
               c_min/60*MET["course"]*poids_saisie + r_min/60*MET["renforcement"]*poids_saisie)
    new_entry = pd.DataFrame([{"date": str(date_saisie), "poids": poids_saisie, "natation_min": n_min, "marche_min": m_min, "course_min": c_min, "renforcement_min": r_min, "calories_depensees": cal_dep, "objectif": obj_poids}])
    df = pd.concat([df[df['date'] != str(date_saisie)], new_entry], ignore_index=True)
    df = recalculer_ensemble_donnees(df)
    df.to_csv(USER_FILE, index=False)
    st.sidebar.success("Enregistré !")
    st.rerun()

# ===============================
# DASHBOARD
# ===============================
st.title(f"🏃‍♂️ Dashboard : {user_name}")

if not df.empty:
    df = recalculer_ensemble_donnees(df)
    df_sorted = df.sort_values("date")
    
    # Onglets pour mobile
    tab1, tab2, tab3 = st.tabs(["📈 Évolution", "🍕 Répartition", "📊 Historique"])
    
    with tab1:
        # KPI rapides
        c1, c2 = st.columns(2)
        c1.metric("Poids", f"{df_sorted['poids'].iloc[-1]} kg")
        c2.metric("Gras Perdu", f"{round(df_sorted['cumul_kcal'].iloc[-1]/7700, 2)} kg")
        
        # Graphe Poids
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        ax1.plot(df_sorted["date"], df_sorted["poids"], marker='o', color='#3498db', linewidth=2)
        ax1.axhline(y=obj_poids, color='r', linestyle='--', label="Objectif")
        plt.xticks(rotation=45)
        st.pyplot(fig1)

    with tab2:
        st.subheader("Analyse de l'effort")
        # Calcul des totaux pour le camembert
        labels = ["Natation", "Marche", "Course", "Muscu"]
        valeurs = [
            df["natation_min"].sum(),
            df["marche_min"].sum(),
            df["course_min"].sum(),
            df["renforcement_min"].sum()
        ]
        
        if sum(valeurs) > 0:
            
            fig2, ax2 = plt.subplots()
            colors = ['#3498db', '#2ecc71', '#e74c3c', '#f1c40f']
            ax2.pie(valeurs, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors, wedgeprops={'edgecolor': 'white'})
            ax2.axis('equal') 
            st.pyplot(fig2)
            st.write(f"Total temps d'activité : **{int(sum(valeurs))} minutes**")
        else:
            st.info("Ajoutez des séances de sport pour voir la répartition !")

    with tab3:
        st.dataframe(df_sorted.sort_values("date", ascending=False), use_container_width=True)

    if st.sidebar.button("🗑️ Supprimer Profil"):
        os.remove(USER_FILE)
        st.rerun()
else:
    st.info("Aucune donnée. Utilisez la barre latérale pour commencer.")
