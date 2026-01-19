import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from github import Github
from datetime import date, datetime, timedelta
from io import StringIO
import random

# --- 1. CONFIGURATION DE LA PAGE (Doit être en haut) ---
st.set_page_config(page_title="Fitness Gamified Pro", layout="wide")

# --- 2. CONFIGURATION DU FOND D'ÉCRAN ---
def add_bg_from_github():
    img_url = "https://raw.githubusercontent.com/mateohier/my-fitness-app/main/AAAAAAAAAAAAAAAA.png"
    st.markdown(
         f"""
         <style>
         .stApp {{
             background-image: url("{img_url}");
             background-attachment: fixed;
             background-size: cover;
             background-position: center;
         }}
         [data-testid="stSidebar"], .stTabs {{
             background-color: rgba(0, 0, 0, 0.65) !important;
             padding: 20px;
             border-radius: 15px;
             backdrop-filter: blur(8px);
         }}
         h1, h2, h3, p, label, .stMarkdown {{
             color: white !important;
         }}
         .stButton>button {{
             background-color: #1E88E5;
             color: white;
             border-radius: 10px;
             border: none;
         }}
         </style>
         """,
         unsafe_allow_html=True
     )

add_bg_from_github()

# --- 3. CONFIGURATION GITHUB ---
try:
    TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    g = Github(TOKEN)
    repo = g.get_repo(REPO_NAME)
except Exception:
    st.error("⚠️ Erreur de configuration : Vérifiez GITHUB_TOKEN et REPO_NAME dans les Secrets Streamlit.")
    st.stop()

# --- 4. FONCTIONS DE GESTION CLOUD ---
def save_file(path, content):
    try:
        f = repo.get_contents(path)
        repo.update_file(f.path, f"MAJ {path}", content, f.sha)
    except:
        repo.create_file(path, f"Création {path}", content)

def load_file(path):
    try:
        return repo.get_contents(path).decoded_content.decode()
    except:
        return None

def get_rank(total_cal):
    if total_cal < 5000: return "Débutant 🥚", 5000, "Bronze", "Continue comme ça, chaque effort compte !"
    if total_cal < 15000: return "Actif 🐣", 15000, "Argent", "Tu commences à prendre le rythme, bravo !"
    if total_cal < 30000: return "Sportif 🏃", 30000, "Or", "Impressionnant ! Tu es une machine !"
    if total_cal < 60000: return "Athlète 🏆", 60000, "Platine", "Niveau Elite. Tu inspires le respect !"
    return "Légende 🔥", 1000000, "Diamant", "Inarrêtable. Tu es au sommet !"

# --- 5. GESTION DU PROFIL (SIDEBAR) ---
st.sidebar.title("🔐 Accès Profil")
menu = st.sidebar.radio("Menu", ["Connexion", "Créer un compte"])
user = None

if menu == "Créer un compte":
    new_u = st.sidebar.text_input("Nom").strip().lower()
    new_p = st.sidebar.text_input("PIN (4 chiffres)", type="password")
    new_obj = st.sidebar.number_input("Objectif de poids (kg)", 40.0, 150.0, 70.0)
    if st.sidebar.button("Enregistrer le profil"):
        if new_u and len(new_p) == 4:
            save_file(f"user_data/{new_u}.pin", new_p)
            save_file(f"user_data/{new_u}.obj", str(new_obj))
            save_file(f"user_data/{new_u}.csv", "date,poids,sport,minutes,calories")
            st.sidebar.success("Profil créé ! Connectez-vous.")
else:
    u = st.sidebar.text_input("Nom").strip().lower()
    p = st.sidebar.text_input("PIN", type="password")
    if u:
        stored_pin = load_file(f"user_data/{u}.pin")
        if stored_pin and p == stored_pin:
            user = u
        elif stored_pin:
            st.sidebar.error("PIN incorrect.")

# --- 6. LOGIQUE D'AFFICHAGE (ACCUEIL OU INTERFACE) ---
if not user:
    st.markdown(
        """
        <div style="text-align: center; padding: 50px; background-color: rgba(0,0,0,0.5); border-radius: 20px;">
            <h1 style="color: white; font-size: 40px;">Bienvenue  👋</h1>
            <p style="color: #FFD700; font-size: 24px; font-weight: bold;">
                👉 Pour commencer, cliquez en haut à gauche sur les deux flèches ( >> )
            </p>
            <p style="color: white; font-size: 18px;">
                Connectez-vous ou créez un compte pour suivre vos performances.
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    #st.image("https://raw.githubusercontent.com/mateohier/my-fitness-app/main/AAAAAAAAAAAAAAAA.jpg", use_container_width=True)

else:
    # --- INTERFACE PRINCIPALE UNE FOIS CONNECTÉ ---
    csv_str = load_file(f"user_data/{user}.csv")
    obj_val = float(load_file(f"user_data/{user}.obj") or 70.0)
    
    if csv_str:
        df = pd.read_csv(StringIO(csv_str))
        df['date'] = pd.to_datetime(df['date'])
    else:
        df = pd.DataFrame(columns=["date", "poids", "sport", "minutes", "calories"])

    total_cal = df["calories"].sum() if not df.empty else 0
    kg_perdus_theo = total_cal / 7700
    rank_name, next_level, medal, coach_msg = get_rank(total_cal)
    
    last_7 = datetime.now() - timedelta(days=7)
    df_week = df[df['date'] >= last_7] if not df.empty else pd.DataFrame()
    
    tab1, tab2, tab3, tab4 = st.tabs(["🏆 Rang & Stats", "📊 Graphiques", "➕ Ajouter", "⚙️ Gestion"])

    with tab1:
        st.header(f"Bienvenue, {user.capitalize()} !")
        st.info(f"💡 **Le mot du coach :** {coach_msg}")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("Rang Actuel", rank_name)
            st.write(f"Médaille : **{medal}**")
        with c2:
            prog = min(total_cal / next_level, 1.0)
            st.write(f"Progression vers le prochain niveau ({int(total_cal)} / {next_level} kcal)")
            st.progress(prog)

        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("🔥 Total Brûlé", f"{int(total_cal)} kcal")
        m2.metric("⚖️ Perte Théorique", f"{kg_perdus_theo:.2f} kg")
        
        if not df_week.empty:
            day_perf = df_week.groupby('date')['calories'].sum()
            m3.metric("🏆 Record Semaine", f"{int(day_perf.max())} kcal")
            best_sport = df_week.groupby('sport')['calories'].sum().idxmax()
            st.write(f"🌟 **Performance :** Ton sport n°1 est le **{best_sport}** et ton meilleur jour était le **{day_perf.idxmax().strftime('%d/%m')}**.")
        else:
            m3.metric("🏆 Record Semaine", "0 kcal")

    with tab2:
        if not df.empty:
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("Évolution du Poids")
                fig, ax = plt.subplots()
                ax.plot(df["date"], df["poids"], color='#1E88E5', marker='o', label="Poids")
                ax.axhline(y=obj_val, color='r', linestyle='--', label=f"Objectif ({obj_val}kg)")
                plt.xticks(rotation=45)
                ax.legend()
                st.pyplot(fig)
            with col_b:
                st.subheader("Répartition par Sport")
                sport_data = df.groupby("sport")["minutes"].sum()
                fig2, ax2 = plt.subplots()
                ax2.pie(sport_data, labels=sport_data.index, autopct='%1.1f%%', colors=plt.cm.Paired.colors)
                st.pyplot(fig2)
        else:
            st.warning("Ajoute des données pour voir les graphiques !")

    with tab3:
        st.header("Enregistrer une activité")
        with st.form("seance_form"):
            d_input = st.date_input("Date", date.today())
            p_input = st.number_input("Poids actuel (kg)", 40.0, 160.0, df.iloc[-1]["poids"] if not df.empty else 75.0)
            s_input = st.selectbox("Sport", ["Natation", "Marche", "Course", "Vélo", "Fitness", "Musculation"])
            m_input = st.number_input("Durée (minutes)", 5, 300, 30)
            met_values = {"Natation": 8, "Marche": 3.5, "Course": 10, "Vélo": 6, "Fitness": 5, "Musculation": 4}
            
            if st.form_submit_button("🚀 Sauvegarder sur GitHub"):
                cal_calc = (m_input/60) * met_values[s_input] * p_input
                new_data = pd.DataFrame([{"date": str(d_input), "poids": p_input, "sport": s_input, "minutes": m_input, "calories": cal_calc}])
                df = pd.concat([df, new_data], ignore_index=True)
                save_file(f"user_data/{user}.csv", df.to_csv(index=False))
                st.success("Données synchronisées !")
                st.rerun()

    with tab4:
        st.header("Paramètres du profil")
        new_obj = st.number_input("Changer mon objectif (kg)", 40.0, 150.0, obj_val)
        if st.button("Mettre à jour l'objectif"):
            save_file(f"user_data/{user}.obj", str(new_obj))
            st.rerun()
        st.divider()
        if not df.empty:
            st.dataframe(df.sort_values('date', ascending=False))
            del_idx = st.selectbox("Sélectionner l'index à supprimer", df.index)
            if st.button("❌ Supprimer définitivement cette ligne"):
                df = df.drop(del_idx)
                save_file(f"user_data/{user}.csv", df.to_csv(index=False))
                st.rerun()



