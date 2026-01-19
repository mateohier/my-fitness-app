import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from github import Github
from datetime import date, datetime, timedelta
from io import StringIO

# --- CONFIGURATION GITHUB ---
try:
    TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    g = Github(TOKEN)
    repo = g.get_repo(REPO_NAME)
except:
    st.error("Erreur de configuration GITHUB_TOKEN ou REPO_NAME dans les Secrets.")
    st.stop()

# --- FONCTIONS CLOUD ---
def save_file(path, content):
    try:
        f = repo.get_contents(path)
        repo.update_file(f.path, f"Update {path}", content, f.sha)
    except:
        repo.create_file(path, f"Create {path}", content)

def load_file(path):
    try:
        return repo.get_contents(path).decoded_content.decode()
    except:
        return None

# --- INTERFACE ---
st.set_page_config(page_title="Fitness Pro", layout="wide")
st.sidebar.title("🔐 Accès Profil")

menu = st.sidebar.radio("Menu", ["Connexion", "Créer un compte"])
user = None

if menu == "Créer un compte":
    new_u = st.sidebar.text_input("Nom").strip().lower()
    new_p = st.sidebar.text_input("PIN (4 chiffres)", type="password")
    new_obj = st.sidebar.number_input("Objectif de poids (kg)", 50.0, 150.0, 70.0)
    if st.sidebar.button("Enregistrer le profil"):
        if new_u and len(new_p) == 4:
            save_file(f"user_data/{new_u}.pin", new_p)
            save_file(f"user_data/{new_u}.obj", str(new_obj))
            save_file(f"user_data/{new_u}.csv", "date,poids,sport,minutes,calories")
            st.sidebar.success("Profil créé !")
else:
    u = st.sidebar.text_input("Nom").strip().lower()
    p = st.sidebar.text_input("PIN", type="password")
    if u:
        stored_pin = load_file(f"user_data/{u}.pin")
        if stored_pin and p == stored_pin:
            user = u
        elif stored_pin:
            st.sidebar.error("PIN incorrect.")

if user:
    # Chargement des données et de l'objectif
    csv_str = load_file(f"user_data/{user}.csv")
    obj_val = float(load_file(f"user_data/{user}.obj") or 70.0)
    
    if csv_str:
        df = pd.read_csv(StringIO(csv_str))
        df['date'] = pd.to_datetime(df['date'])
    else:
        df = pd.DataFrame(columns=["date", "poids", "sport", "minutes", "calories"])

    # --- CALCULS STATISTIQUES ---
    total_cal = df["calories"].sum() if not df.empty else 0
    kg_perdus_theo = total_cal / 7700
    
    # Meilleure performance de la semaine
    last_7_days = datetime.now() - timedelta(days=7)
    df_week = df[df['date'] >= last_7_days]
    best_perf = df_week["calories"].max() if not df_week.empty else 0

    tab1, tab2, tab3 = st.tabs(["📊 Tableau de Bord", "➕ Ajouter", "⚙️ Gestion"])

    with tab1:
        # Compteurs en haut
        c1, c2, c3 = st.columns(3)
        c1.metric("🔥 Calories Totales", f"{int(total_cal)} kcal")
        c2.metric("⚖️ Perte Théorique", f"{kg_perdus_theo:.2f} kg", delta_color="normal")
        c3.metric("🏆 Record Semaine", f"{int(best_perf)} kcal")

        if not df.empty:
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("Suivi du Poids vs Objectif")
                fig, ax = plt.subplots()
                ax.plot(df["date"], df["poids"], marker='o', label="Poids actuel")
                ax.axhline(y=obj_val, color='r', linestyle='--', label="Objectif")
                plt.xticks(rotation=45)
                ax.legend()
                st.pyplot(fig)
            
            with col_b:
                st.subheader("Répartition des activités")
                sport_counts = df.groupby("sport")["minutes"].sum()
                fig2, ax2 = plt.subplots()
                ax2.pie(sport_counts, labels=sport_counts.index, autopct='%1.1f%%', colors=['#ff9999','#66b3ff','#99ff99','#ffcc99'])
                st.pyplot(fig2)

            # --- PRÉVISION ---
            st.divider()
            if len(df) > 1:
                poids_actuel = df.iloc[-1]["poids"]
                if poids_actuel > obj_val:
                    perte_moyenne_semaine = (df.iloc[0]["poids"] - poids_actuel) / ((df.iloc[-1]["date"] - df.iloc[0]["date"]).days / 7 or 1)
                    if perte_moyenne_semaine > 0:
                        semaines_restantes = (poids_actuel - obj_val) / perte_moyenne_semaine
                        date_estimee = date.today() + timedelta(weeks=semaines_restantes)
                        st.success(f"🎯 À ce rythme, vous atteindrez votre objectif de **{obj_val}kg** vers le **{date_estimee.strftime('%d/%m/%Y')}**.")
                    else:
                        st.warning("Stagnation : Augmentez l'activité pour estimer une date d'atteinte d'objectif.")

    with tab2:
        st.header("Nouvelle séance")
        with st.form("add_form"):
            d = st.date_input("Date", date.today())
            p = st.number_input("Poids actuel (kg)", 40.0, 160.0, df.iloc[-1]["poids"] if not df.empty else 75.0)
            s = st.selectbox("Sport", ["Natation", "Marche", "Course", "Vélo", "Fitness"])
            m = st.number_input("Minutes", 5, 300, 30)
            
            met = {"Natation": 8, "Marche": 3.5, "Course": 10, "Vélo": 6, "Fitness": 5}
            
            if st.form_submit_button("Enregistrer"):
                cal = (m/60) * met[s] * p
                new_row = pd.DataFrame([{"date": str(d), "poids": p, "sport": s, "minutes": m, "calories": cal}])
                df = pd.concat([df, new_row], ignore_index=True)
                save_file(f"user_data/{user}.csv", df.to_csv(index=False))
                st.success("Données synchronisées !")
                st.rerun()

    with tab3:
        st.header("Paramètres")
        new_obj = st.number_input("Modifier l'objectif (kg)", 40.0, 150.0, obj_val)
        if st.button("Mettre à jour l'objectif"):
            save_file(f"user_data/{user}.obj", str(new_obj))
            st.success("Objectif mis à jour !")
            st.rerun()
            
        st.divider()
        if not df.empty:
            st.write("Historique des saisies :")
            st.dataframe(df)
            idx = st.selectbox("Ligne à supprimer", df.index)
            if st.button("❌ Supprimer définitivement"):
                df = df.drop(idx)
                save_file(f"user_data/{user}.csv", df.to_csv(index=False))
                st.rerun()
