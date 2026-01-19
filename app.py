import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from github import Github
from datetime import date
import os
# ... (imports) ...

try:
    TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    
    # Test de connexion immédiat
    g = Github(TOKEN)
    repo = g.get_repo(REPO_NAME) 
    st.sidebar.success(f"✅ Connecté à : {repo.full_name}")
except Exception as e:
    st.error(f"❌ Erreur de connexion GitHub : {e}")
    st.info("Vérifiez que REPO_NAME est bien 'pseudo/depot' et que le Token est valide.")
    st.stop()
# 1. CONFIGURATION & SECRETS
try:
    TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
except Exception:
    st.error("⚠️ Configurer GITHUB_TOKEN et REPO_NAME dans les Secrets de Streamlit.")
    st.stop()

# 2. FONCTIONS DE GESTION GITHUB
def save_to_github(file_path, df_to_save):
    g = Github(TOKEN)
    repo = g.get_repo(REPO_NAME)
    csv_content = df_to_save.to_csv(index=False)
    try:
        contents = repo.get_contents(file_path)
        repo.update_file(contents.path, f"MAJ {file_path}", csv_content, contents.sha)
    except:
        repo.create_file(file_path, f"Création {file_path}", csv_content)

def load_from_github(file_path):
    try:
        g = Github(TOKEN)
        repo = g.get_repo(REPO_NAME)
        contents = repo.get_contents(file_path)
        return pd.read_csv(contents.download_url)
    except:
        # Retourne un tableau vide avec les bonnes colonnes si le fichier n'existe pas
        return pd.DataFrame(columns=["date", "poids", "calories"])

# 3. INTERFACE
st.set_page_config(page_title="Fitness GitHub", layout="wide")
st.sidebar.title("🔐 Accès Profil")

user_name = st.sidebar.text_input("Nom d'utilisateur", "Mateo").strip().lower()

if user_name:
    USER_FILE = f"user_data/{user_name}.csv"
    
    # Chargement initial des données
    if 'df_user' not in st.session_state:
        st.session_state.df_user = load_from_github(USER_FILE)
    
    df = st.session_state.df_user

    st.title(f"🏃‍♂️ Dashboard de {user_name.capitalize()}")

    # FORMULAIRE DE SAISIE
    with st.sidebar.form("mon_formulaire"):
        st.subheader("Saisie du jour")
        date_j = st.date_input("Date", date.today())
        poids_j = st.number_input("Poids (kg)", 70.0, step=0.1)
        marche_j = st.number_input("Marche (min)", 0)
        course_j = st.number_input("Course (min)", 0)
        
        submit = st.form_submit_button("💾 Enregistrer sur GitHub")
        
        if submit:
            # Calcul des calories (MET)
            cal = (marche_j/60 * 3.5 * poids_j) + (course_j/60 * 9.8 * poids_j)
            
            # Création de la nouvelle ligne
            new_line = pd.DataFrame([{"date": str(date_j), "poids": poids_j, "calories": cal}])
            
            # Mise à jour du tableau (on évite les doublons de date)
            df = pd.concat([df[df['date'] != str(date_j)], new_line], ignore_index=True)
            df = df.sort_values("date")
            
            # Sauvegarde Cloud
            save_to_github(USER_FILE, df)
            st.session_state.df_user = df
            st.sidebar.success("✅ Synchronisé avec GitHub !")
            st.rerun()

    # AFFICHAGE DES GRAPHIQUES
    if not df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Évolution du poids")
            fig1, ax1 = plt.subplots()
            ax1.plot(df["date"], df["poids"], marker='o', color='#3498db')
            plt.xticks(rotation=45)
            st.pyplot(fig1)
            
        with col2:
            st.subheader("Historique des calories")
            st.bar_chart(df.set_index("date")["calories"])
            
        with st.expander("Voir les données brutes"):
            st.write(df)
    else:
        st.info("👋 Bienvenue ! Saisissez vos premières données dans la barre latérale.")

