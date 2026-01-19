import streamlit as st
import pandas as pd
import plotly.express as px  # Plus joli et interactif que Matplotlib
from github import Github, GithubException
from datetime import date, datetime, timedelta
from io import StringIO
import hashlib
import time

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Fitness Gamified Pro", 
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. SÉCURITÉ & UTILITAIRES ---
def hash_pin(pin):
    """Hache le PIN pour ne pas le stocker en clair (SHA-256)."""
    return hashlib.sha256(str(pin).encode()).hexdigest()

def init_session_state():
    """Initialise les variables de session pour la persistance."""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'data_changed' not in st.session_state:
        st.session_state.data_changed = False

init_session_state()

# --- 3. GESTION GITHUB (AVEC CACHE) ---
# On utilise le cache pour ne pas requêter GitHub à chaque interaction
@st.cache_resource
def get_github_repo():
    try:
        # Vérification sécurisée des secrets
        if "GITHUB_TOKEN" not in st.secrets or "REPO_NAME" not in st.secrets:
            st.error("⚠️ Secrets manquants. Ajoutez GITHUB_TOKEN et REPO_NAME.")
            st.stop()
        
        g = Github(st.secrets["GITHUB_TOKEN"])
        return g.get_repo(st.secrets["REPO_NAME"])
    except Exception as e:
        st.error(f"⚠️ Erreur de connexion GitHub : {e}")
        st.stop()

repo = get_github_repo()

def save_file_to_github(path, content, message):
    """Sauvegarde ou met à jour un fichier sur GitHub."""
    try:
        try:
            contents = repo.get_contents(path)
            repo.update_file(contents.path, message, content, contents.sha)
        except GithubException:
            repo.create_file(path, message, content)
        
        # Invalider le cache de lecture pour forcer le rechargement
        get_file_content.clear()
        return True
    except Exception as e:
        st.error(f"Erreur de sauvegarde : {e}")
        return False

@st.cache_data(ttl=300) # Cache les données pendant 5 min ou jusqu'à effacement
def get_file_content(path):
    """Récupère le contenu d'un fichier."""
    try:
        return repo.get_contents(path).decoded_content.decode()
    except:
        return None

# --- 4. LOGIQUE MÉTIER ---
def get_rank(total_cal):
    levels = [
        (5000, "Débutant 🥚", "Bronze", "Chaque effort compte !"),
        (15000, "Actif 🐣", "Argent", "Tu prends le rythme !"),
        (30000, "Sportif 🏃", "Or", "Quelle machine !"),
        (60000, "Athlète 🏆", "Platine", "Niveau Élite."),
        (1000000, "Légende 🔥", "Diamant", "Tu es au sommet !")
    ]
    
    for limit, name, medal, msg in levels:
        if total_cal < limit:
            return name, limit, medal, msg
    return levels[-1]

# --- 5. INTERFACE UTILISATEUR (CSS) ---
def apply_style():
    # Image de fond (assure-toi que le lien est valide)
    img_url = "https://raw.githubusercontent.com/mateohier/my-fitness-app/main/AAAAAAAAAAAAAAAA.png"
    
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url("{img_url}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        div[data-testid="stSidebar"] {{
            background-color: rgba(20, 20, 20, 0.9);
            border-right: 1px solid #333;
        }}
        h1, h2, h3, .stMetricLabel {{ color: #ffffff !important; }}
        .stMetricValue {{ color: #4CAF50 !important; }}
        div.stButton > button {{
            background-color: #1E88E5;
            color: white;
            border-radius: 8px;
            padding: 10px 20px;
            border: none;
            width: 100%;
        }}
        div.stButton > button:hover {{ background-color: #1565C0; }}
        </style>
    """, unsafe_allow_html=True)

apply_style()

# --- 6. SIDEBAR - AUTHENTIFICATION ---
st.sidebar.title("🔐 Accès Profil")

if not st.session_state.user:
    menu = st.sidebar.selectbox("Action", ["Connexion", "Créer un compte"])
    
    username = st.sidebar.text_input("Nom d'utilisateur").strip().lower()
    pin = st.sidebar.text_input("PIN (4 chiffres)", type="password")

    if menu == "Connexion":
        if st.sidebar.button("Se connecter"):
            if username and pin:
                stored_hash = get_file_content(f"user_data/{username}.pin")
                if stored_hash and stored_hash == hash_pin(pin):
                    st.session_state.user = username
                    st.success("Connexion réussie !")
                    st.rerun()
                else:
                    st.sidebar.error("Nom ou PIN incorrect.")
            else:
                st.sidebar.warning("Remplissez tous les champs.")

    elif menu == "Créer un compte":
        obj_weight = st.sidebar.number_input("Objectif Poids (kg)", 40.0, 150.0, 70.0)
        if st.sidebar.button("S'inscrire"):
            if username and len(pin) == 4:
                # Vérifier si l'user existe déjà
                if get_file_content(f"user_data/{username}.pin"):
                    st.sidebar.error("Ce nom existe déjà.")
                else:
                    save_file_to_github(f"user_data/{username}.pin", hash_pin(pin), "New User PIN")
                    save_file_to_github(f"user_data/{username}.obj", str(obj_weight), "New User Obj")
                    save_file_to_github(f"user_data/{username}.csv", "date,poids,sport,minutes,calories", "Init CSV")
                    st.sidebar.success("Compte créé ! Connectez-vous.")
            else:
                st.sidebar.error("Nom requis et PIN de 4 chiffres.")

else:
    st.sidebar.success(f"Connecté en tant que : **{st.session_state.user.capitalize()}**")
    if st.sidebar.button("Déconnexion"):
        st.session_state.user = None
        st.rerun()

# --- 7. APPLICATION PRINCIPALE ---
if st.session_state.user:
    user = st.session_state.user
    
    # Chargement des données
    csv_content = get_file_content(f"user_data/{user}.csv")
    obj_content = get_file_content(f"user_data/{user}.obj")
    
    target_weight = float(obj_content) if obj_content else 70.0
    
    if csv_content:
        df = pd.read_csv(StringIO(csv_content))
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
    else:
        df = pd.DataFrame(columns=["date", "poids", "sport", "minutes", "calories"])

    # Calculs
    total_cal = df["calories"].sum() if not df.empty else 0
    rank_name, next_level, medal, coach_msg = get_rank(total_cal)
    
    # Onglets
    tab1, tab2, tab3, tab4 = st.tabs(["🏆 Dashboard", "📈 Analyse", "➕ Nouveau", "⚙️ Données"])

    with tab1:
        st.title(f"Bonjour {user.capitalize()} !")
        st.markdown(f"### {coach_msg}")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🔥 Calories Totales", f"{int(total_cal):,} kcal")
        col1.metric("🏅 Rang", rank_name)
        
        # Barre de progression
        progression = min(total_cal / next_level, 1.0)
        col2.write(f"**Prochain niveau :** {int(total_cal)} / {next_level} kcal")
        col2.progress(progression)
        
        # Poids actuel vs Objectif
        last_weight = df.iloc[-1]['poids'] if not df.empty else 0
        delta_weight = last_weight - target_weight
        col3.metric("⚖️ Poids Actuel", f"{last_weight} kg", f"{delta_weight:.1f} kg vs Obj", delta_color="inverse")

    with tab2:
        if not df.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Évolution du Poids")
                fig_weight = px.line(df, x='date', y='poids', markers=True, title="Suivi Poids")
                fig_weight.add_hline(y=target_weight, line_dash="dash", line_color="red", annotation_text="Objectif")
                st.plotly_chart(fig_weight, use_container_width=True)
            
            with c2:
                st.subheader("Répartition Sports")
                fig_pie = px.pie(df, values='minutes', names='sport', title="Temps par Sport", hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Aucune donnée à afficher pour le moment.")

    with tab3:
        st.subheader("Ajouter une séance")
        with st.form("add_sport"):
            c_date, c_sport = st.columns(2)
            d_input = c_date.date_input("Date", date.today())
            s_input = c_sport.selectbox("Sport", ["Natation", "Marche", "Course", "Vélo", "Fitness", "Musculation", "Crossfit"])
            
            c_poids, c_duree = st.columns(2)
            current_w = df.iloc[-1]['poids'] if not df.empty else 70.0
            p_input = c_poids.number_input("Poids du jour (kg)", 40.0, 160.0, float(current_w))
            m_input = c_duree.number_input("Durée (min)", 10, 300, 45)
            
            met_values = {"Natation": 8, "Marche": 3.5, "Course": 10, "Vélo": 6, "Fitness": 5, "Musculation": 4, "Crossfit": 8}
            
            if st.form_submit_button("Sauvegarder l'activité"):
                cal_calc = (m_input/60) * met_values.get(s_input, 5) * p_input
                new_entry = pd.DataFrame([{
                    "date": d_input, 
                    "poids": p_input, 
                    "sport": s_input, 
                    "minutes": m_input, 
                    "calories": round(cal_calc, 2)
                }])
                
                df_updated = pd.concat([df, new_entry], ignore_index=True)
                # Sauvegarde CSV
                save_file_to_github(f"user_data/{user}.csv", df_updated.to_csv(index=False), "Add activity")
                st.success(f"Séance ajoutée : {int(cal_calc)} calories brûlées !")
                time.sleep(1)
                st.rerun()

    with tab4:
        st.subheader("Historique des données")
        if not df.empty:
            # Éditeur de données interactif
            edited_df = st.data_editor(df, num_rows="dynamic")
            
            if st.button("💾 Sauvegarder les modifications manuelles"):
                save_file_to_github(f"user_data/{user}.csv", edited_df.to_csv(index=False), "Manual Edit")
                st.success("Données mises à jour !")
                time.sleep(1)
                st.rerun()
        else:
            st.write("Le journal est vide.")

else:
    # Page d'accueil pour visiteur non connecté
    st.markdown("""
    <div style="text-align: center; padding: 4rem; background: rgba(0,0,0,0.6); border-radius: 20px; margin-top: 50px;">
        <h1>🚀 Fitness Gamified Pro</h1>
        <p style="font-size: 1.2rem;">Connectez-vous via le menu à gauche pour suivre vos performances.</p>
    </div>
    """, unsafe_allow_html=True)
