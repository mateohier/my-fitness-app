import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import date

# ===============================
# Configuration
# ===============================
st.set_page_config(page_title="Fitness Secure", layout="wide")

MET = {"natation": 8.0, "marche": 3.5, "course": 9.8, "renforcement": 6.0}
KCAL_PAR_KG_GRAISSE = 7700
BASE_DIR = "user_data"

if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

# --- Initialisation de la session (Login) ---
if 'auth_user' not in st.session_state:
    st.session_state.auth_user = None

# ===============================
# GESTION DES PROFILS & PIN
# ===============================
st.sidebar.title("🔐 Accès Profil")

existing_profiles = [f.replace(".csv", "") for f in os.listdir(BASE_DIR) if f.endswith(".csv")]

# 1. Sélection du profil
user_selected = st.sidebar.selectbox("Qui êtes-vous ?", ["Choisir..."] + existing_profiles)

if user_selected != "Choisir...":
    # Vérifier si l'utilisateur est déjà authentifié
    if st.session_state.auth_user != user_selected:
        pin_input = st.sidebar.text_input(f"Entrez le code PIN pour {user_selected}", type="password")
        
        # Charger le vrai PIN sauvegardé
        pin_path = os.path.join(BASE_DIR, f"{user_selected}.pin")
        with open(pin_path, "r") as f:
            true_pin = f.read().strip()
        
        if st.sidebar.button("Se connecter"):
            if pin_input == true_pin:
                st.session_state.auth_user = user_selected
                st.rerun()
            else:
                st.sidebar.error("Code PIN incorrect")
    else:
        if st.sidebar.button("Se déconnecter"):
            st.session_state.auth_user = None
            st.rerun()

# 2. Création de profil avec PIN
with st.sidebar.expander("➕ Créer un nouveau compte"):
    new_user = st.text_input("Nom")
    new_pin = st.text_input("Définir un code PIN (4 chiffres)", type="password")
    if st.button("Créer"):
        if new_user and len(new_pin) >= 4:
            # Sauvegarde du CSV
            pd.DataFrame(columns=["date", "poids", "natation_min", "marche_min", "course_min", "renforcement_min", "calories_depensees", "objectif"]).to_csv(os.path.join(BASE_DIR, f"{new_user}.csv"), index=False)
            # Sauvegarde du PIN
            with open(os.path.join(BASE_DIR, f"{new_user}.pin"), "w") as f:
                f.write(new_pin)
            st.success("Compte créé ! Connectez-vous.")
            st.rerun()
        else:
            st.error("Le PIN doit faire au moins 4 caractères.")

# ===============================
# DASHBOARD (Affiché uniquement si connecté)
# ===============================
if st.session_state.auth_user:
    user_name = st.session_state.auth_user
    USER_FILE = os.path.join(BASE_DIR, f"{user_name}.csv")
    df = pd.read_csv(USER_FILE)
    
    st.title(f"🏃‍♂️ Session de {user_name}")

    # --- Logique de calcul ---
    def recalculer_ensemble_donnees(df_input):
        if df_input.empty: return df_input
        df_input = df_input.sort_values("date").reset_index(drop=True)
        mg_estimee_list, cal_perte_list, cum_cal = [], [], 0
        for i, row in df_input.iterrows():
            if i == 0: mg = 0.22 * row['poids']
            else: mg = min(mg_estimee_list[i-1], max(mg_estimee_list[i-1] - (row['calories_depensees']/KCAL_PAR_KG_GRAISSE), 0.05 * row['poids']))
            mg_estimee_list.append(mg)
            delta = (mg_estimee_list[i-1] - mg) if i > 0 else 0
            cum_cal += (delta * KCAL_PAR_KG_GRAISSE)
            cal_perte_list.append(cum_cal)
        df_input["mg_kg"] = mg_estimee_list
        df_input["cumul_kcal"] = cal_perte_list
        return df_input

    # --- Saisie des données (Sidebar spécifique au profil connecté) ---
    st.sidebar.markdown("---")
    st.sidebar.write(f"Saisie pour **{user_name}**")
    d_s = st.sidebar.date_input("Date", date.today())
    p_s = st.sidebar.number_input("Poids (kg)", 70.0)
    
    n = st.sidebar.number_input("Natation", 0)
    m = st.sidebar.number_input("Marche", 0)
    c = st.sidebar.number_input("Course", 0)
    r = st.sidebar.number_input("Muscu", 0)

    if st.sidebar.button("💾 Enregistrer"):
        cal = (n/60*MET["natation"]*p_s + m/60*MET["marche"]*p_s + c/60*MET["course"]*p_s + r/60*MET["renforcement"]*p_s)
        new_row = pd.DataFrame([{"date": str(d_s), "poids": p_s, "natation_min": n, "marche_min": m, "course_min": c, "renforcement_min": r, "calories_depensees": cal, "objectif": 65.0}])
        df = pd.concat([df[df['date'] != str(d_s)], new_row], ignore_index=True)
        df = recalculer_ensemble_donnees(df)
        df.to_csv(USER_FILE, index=False)
        st.rerun()

    # --- Affichage des résultats ---
    if not df.empty:
        df = recalculer_ensemble_donnees(df)
        t1, t2 = st.tabs(["📊 Évolution", "🍕 Répartition"])
        
        with t1:
            fig1, ax1 = plt.subplots(figsize=(10, 4))
            ax1.plot(df["date"], df["poids"], marker='o', color='#3498db')
            plt.xticks(rotation=45)
            st.pyplot(fig1)
            
        with t2:
            labels = ["Natation", "Marche", "Course", "Muscu"]
            valeurs = [df["natation_min"].sum(), df["marche_min"].sum(), df["course_min"].sum(), df["renforcement_min"].sum()]
            if sum(valeurs) > 0:
                
                fig2, ax2 = plt.subplots()
                ax2.pie(valeurs, labels=labels, autopct='%1.1f%%', colors=['#3498db','#2ecc71','#e74c3c','#f1c40f'])
                st.pyplot(fig2)
    else:
        st.info("Aucune donnée enregistrée pour ce profil.")

else:
    st.title("🏃‍♂️ Bienvenue sur Fitness Tracker")
    st.info("Veuillez sélectionner votre profil et entrer votre code PIN dans la barre latérale pour accéder à vos données.")
