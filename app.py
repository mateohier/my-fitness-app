import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from github import Github
from datetime import date, datetime, timedelta
from io import StringIO
import os

# --- 1. CONFIGURATION DE LA PAGE ---
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
    st.error("⚠️ Erreur de configuration GitHub.")
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
    if total_cal < 5000: return "Débutant 🥚", 5000, "Bronze", "Continue comme ça !"
    if total_cal < 15000: return "Actif 🐣", 15000, "Argent", "Tu prends le rythme !"
    if total_cal < 30000: return "Sportif 🏃", 30000, "Or", "Quelle machine !"
    return "Légende 🔥", 1000000, "Diamant", "Inarrêtable !"

# --- 5. LOGIQUE DE CLASSEMENT GLOBAL ---
def get_global_stats():
    all_data = []
    try:
        contents = repo.get_contents("user_data")
        for content_file in contents:
            if content_file.name.endswith(".csv"):
                user_name = content_file.name.replace(".csv", "")
                data = repo.get_contents(content_file.path).decoded_content.decode()
                temp_df = pd.read_csv(StringIO(data))
                temp_df['user'] = user_name
                all_data.append(temp_df)
    except:
        return None

    if not all_data: return None
    
    full_df = pd.concat(all_data, ignore_index=True)
    full_df['date'] = pd.to_datetime(full_df['date'])
    return full_df

# --- 6. GESTION DU PROFIL (SIDEBAR) ---
st.sidebar.title("🔐 Accès Profil")
menu = st.sidebar.radio("Menu", ["Connexion", "Créer un compte"])
user = None

if menu == "Créer un compte":
    new_u = st.sidebar.text_input("Nom").strip().lower()
    new_p = st.sidebar.text_input("PIN", type="password")
    new_obj = st.sidebar.number_input("Objectif (kg)", 40.0, 150.0, 70.0)
    if st.sidebar.button("Enregistrer"):
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

# --- 7. LOGIQUE D'AFFICHAGE ---
if not user:
    st.markdown("""
        <div style="text-align: center; padding: 50px; background-color: rgba(0,0,0,0.5); border-radius: 20px;">
            <h1 style="color: white; font-size: 40px;">Bienvenue ! 👋</h1>
            <p style="color: #FFD700; font-size: 24px; font-weight: bold;">👉 Pour commencer, cliquez en haut à gauche ( > )</p>
        </div>
    """, unsafe_allow_html=True)
else:
    # Récupération des données utilisateur et globales
    csv_str = load_file(f"user_data/{user}.csv")
    obj_val = float(load_file(f"user_data/{user}.obj") or 70.0)
    df = pd.read_csv(StringIO(csv_str)) if csv_str else pd.DataFrame()
    if not df.empty: df['date'] = pd.to_datetime(df['date'])

    full_df = get_global_stats()
    
    tab1, tab2, tab3, tab4 = st.tabs(["🏆 Rang & Records", "📊 Graphiques", "➕ Ajouter", "⚙️ Gestion"])

    with tab1:
        # --- SECTION RECORDS GLOBAUX ---
        st.subheader("🌟 Tableau d'Honneur (Global)")
        if full_df is not None:
            c1, c2, c3 = st.columns(3)
            
            # 1. Record par sport (Calories max en 1 séance)
            with c1:
                st.write("**💪 Records par Sport**")
                records_sport = full_df.loc[full_df.groupby('sport')['calories'].idxmax()]
                for _, row in records_sport.iterrows():
                    st.write(f"- {row['sport']}: **{row['user'].capitalize()}** ({int(row['calories'])} kcal)")
            
            # 2. Champion de la semaine (7 derniers jours)
            with c2:
                st.write("**📅 Champion de la Semaine**")
                last_7 = datetime.now() - timedelta(days=7)
                week_df = full_df[full_df['date'] >= last_7]
                if not week_df.empty:
                    week_winner = week_df.groupby('user')['calories'].sum().idxmax()
                    week_cal = week_df.groupby('user')['calories'].sum().max()
                    st.success(f"🔥 **{week_winner.capitalize()}**")
                    st.write(f"Total: {int(week_cal)} kcal")
            
            # 3. Le plus régulier (Nombre de séances total)
            with c3:
                st.write("**⏱️ Le plus Régulier**")
                reg_winner = full_df['user'].value_counts().idxmax()
                reg_count = full_df['user'].value_counts().max()
                st.warning(f"👑 **{reg_winner.capitalize()}**")
                st.write(f"{reg_count} séances enregistrées")
            
            st.write("---")
            st.write("🏃💨 *Félicitations aux champions, et pour les autres : **bougez-vous les fesses !** On lâche rien !*")
            st.divider()

        # --- SECTION STATS PERSO ---
        total_cal = df["calories"].sum() if not df.empty else 0
        rank_name, next_level, medal, coach_msg = get_rank(total_cal)
        st.header(f"Ton profil : {user.capitalize()}")
        st.info(f"💡 {coach_msg}")
        p_col1, p_col2 = st.columns(2)
        p_col1.metric("Ton Rang", rank_name)
        p_col2.metric("Perte Théorique", f"{total_cal/7700:.2f} kg")
        st.progress(min(total_cal / next_level, 1.0))

    with tab2:
        if not df.empty:
            fig, ax = plt.subplots(); ax.plot(df["date"], df["poids"], marker='o'); ax.axhline(y=obj_val, color='r', linestyle='--'); st.pyplot(fig)
        else: st.warning("Ajoute des données !")

    with tab3:
        with st.form("seance"):
            d_i = st.date_input("Date"); p_i = st.number_input("Poids", 40.0, 160.0, 75.0)
            s_i = st.selectbox("Sport", ["Natation", "Marche", "Course", "Vélo", "Fitness", "Musculation"])
            m_i = st.number_input("Durée (min)", 5, 300, 30)
            if st.form_submit_button("🚀 Sauvegarder"):
                met = {"Natation": 8, "Marche": 3.5, "Course": 10, "Vélo": 6, "Fitness": 5, "Musculation": 4}
                cal = (m_i/60) * met[s_i] * p_i
                new_d = pd.DataFrame([{"date": str(d_i), "poids": p_i, "sport": s_i, "minutes": m_i, "calories": cal}])
                df = pd.concat([df, new_d], ignore_index=True)
                save_file(f"user_data/{user}.csv", df.to_csv(index=False))
                st.success("Synchronisé !"); st.rerun()

    with tab4:
        st.header("Gestion")
        if not df.empty:
            st.dataframe(df.sort_values('date', ascending=False))
            if st.button("❌ Supprimer la dernière ligne"):
                df = df[:-1]; save_file(f"user_data/{user}.csv", df.to_csv(index=False)); st.rerun()
