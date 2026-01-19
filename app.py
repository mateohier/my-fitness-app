import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from github import Github
from datetime import date

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

# --- GESTION PROFIL ---
st.set_page_config(page_title="Fitness App", layout="wide")
st.sidebar.title("🔐 Accès Profil")

menu = st.sidebar.radio("Menu", ["Connexion", "Créer un compte"])

user = None
if menu == "Créer un compte":
    new_u = st.sidebar.text_input("Nom").strip().lower()
    new_p = st.sidebar.text_input("PIN (4 chiffres)", type="password")
    if st.sidebar.button("Enregistrer le nouveau profil"):
        if new_u and len(new_p) == 4:
            save_file(f"user_data/{new_u}.pin", new_p)
            save_file(f"user_data/{new_u}.csv", "date,poids,sport,minutes,calories")
            st.sidebar.success("Profil créé ! Connectez-vous.")
        else:
            st.sidebar.error("Nom invalide ou PIN trop court.")

else: # Connexion
    u = st.sidebar.text_input("Nom").strip().lower()
    p = st.sidebar.text_input("PIN", type="password")
    if u:
        stored_pin = load_file(f"user_data/{u}.pin")
        if stored_pin and p == stored_pin:
            user = u
            st.sidebar.success(f"Connecté : {u.capitalize()}")
        elif stored_pin:
            st.sidebar.error("PIN incorrect.")

# --- INTERFACE PRINCIPALE ---
if user:
    # Chargement des données
    csv_str = load_file(f"user_data/{user}.csv")
    if csv_str:
        from io import StringIO
        df = pd.read_csv(StringIO(csv_str))
    else:
        df = pd.DataFrame(columns=["date", "poids", "sport", "minutes", "calories"])

    tab1, tab2, tab3 = st.tabs(["📊 Suivi", "➕ Ajouter", "⚙️ Gestion"])

    with tab1:
        st.header(f"Progression de {user.capitalize()}")
        if not df.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Poids (kg)")
                st.line_chart(df.set_index("date")["poids"])
            with col2:
                st.subheader("Répartition des sports")
                # Diagramme Camembert
                sport_counts = df.groupby("sport")["minutes"].sum()
                fig, ax = plt.subplots()
                ax.pie(sport_counts, labels=sport_counts.index, autopct='%1.1f%%', startangle=90)
                st.pyplot(fig)
        else:
            st.info("Aucune donnée enregistrée.")

    with tab2:
        st.header("Nouvelle séance")
        with st.form("add_form"):
            d = st.date_input("Date", date.today())
            p = st.number_input("Poids (kg)", 50.0, 150.0, 70.0)
            s = st.selectbox("Sport", ["Natation", "Marche", "Course", "Vélo"])
            m = st.number_input("Minutes", 0, 300, 30)
            
            # Calcul calories simplifié (MET)
            met = {"Natation": 8, "Marche": 3.5, "Course": 10, "Vélo": 6}
            cal = (m/60) * met[s] * p
            
            if st.form_submit_button("Enregistrer"):
                new_row = pd.DataFrame([{"date": str(d), "poids": p, "sport": s, "minutes": m, "calories": cal}])
                df = pd.concat([df, new_row], ignore_index=True)
                save_file(f"user_data/{user}.csv", df.to_csv(index=False))
                st.success("Données envoyées sur GitHub !")
                st.rerun()

    with tab3:
        st.header("Historique et Suppression")
        if not df.empty:
            st.write(df)
            row_to_del = st.selectbox("Sélectionner une ligne à supprimer", df.index)
            if st.button("❌ Supprimer la ligne"):
                df = df.drop(row_to_del)
                save_file(f"user_data/{user}.csv", df.to_csv(index=False))
                st.success("Ligne supprimée !")
                st.rerun()
