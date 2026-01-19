import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from github import Github
from datetime import date, datetime, timedelta
from io import StringIO
import random

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
    st.error("⚠️ Erreur de configuration : Vérifiez GITHUB_TOKEN et REPO_NAME.")
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
                if not temp_df.empty:
                    temp_df['user'] = user_name
                    all_data.append(temp_df)
    except: return None
    return pd.concat(all_data, ignore_index=True) if all_data else None

# --- 6. GESTION DU PROFIL (SIDEBAR) ---
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
    u_in = st.sidebar.text_input("Nom").strip().lower()
    p_in = st.sidebar.text_input("PIN", type="password")
    if u_in:
        stored_pin = load_file(f"user_data/{u_in}.pin")
        if stored_pin and p_in == stored_pin:
            user = u_in
        elif stored_pin:
            st.sidebar.error("PIN incorrect.")

# --- 7. LOGIQUE D'AFFICHAGE ---
if not user:
    st.markdown("""
        <div style="text-align: center; padding: 50px; background-color: rgba(0,0,0,0.5); border-radius: 20px;">
            <h1 style="color: white; font-size: 40px;">Bienvenue ! 👋</h1>
            <p style="color: #FFD700; font-size: 24px; font-weight: bold;">👉 Pour commencer, cliquez en haut à gauche sur les deux flèches ( > )</p>
            <p style="color: white; font-size: 18px;">Connectez-vous ou créez un compte pour suivre vos performances.</p>
        </div>
    """, unsafe_allow_html=True)
else:
    # Chargement des données persos
    csv_str = load_file(f"user_data/{user}.csv")
    obj_val = float(load_file(f"user_data/{user}.obj") or 70.0)
    df = pd.read_csv(StringIO(csv_str)) if csv_str else pd.DataFrame(columns=["date", "poids", "sport", "minutes", "calories"])
    if not df.empty: df['date'] = pd.to_datetime(df['date'])

    # Chargement données globales
    full_df = get_global_stats()
    if full_df is not None: full_df['date'] = pd.to_datetime(full_df['date'])
    
    tab1, tab2, tab3, tab4 = st.tabs(["🏆 Rang & Stats", "📊 Graphiques", "➕ Ajouter", "⚙️ Gestion"])

    with tab1:
        # --- TABLEAU D'HONNEUR GLOBAL ---
        st.subheader("🌟 Tableau d'Honneur (Global)")
        if full_df is not None and not full_df.empty:
            c_g1, c_g2, c_g3 = st.columns(3)
            with c_g1:
                st.write("**💪 Records par Sport**")
                idx = full_df.groupby('sport')['calories'].idxmax()
                for _, r in full_df.loc[idx].iterrows():
                    st.write(f"- {r['sport']}: {r['user'].capitalize()} ({int(r['calories'])} kcal)")
            with c_g2:
                st.write("**📅 Champion 7 jours**")
                last_7 = datetime.now() - timedelta(days=7)
                w_df = full_df[full_df['date'] >= last_7]
                if not w_df.empty:
                    w_win = w_df.groupby('user')['calories'].sum().idxmax()
                    st.success(f"🔥 {w_win.capitalize()}")
            with c_g3:
                st.write("**⏱️ Le plus Régulier**")
                reg_win = full_df['user'].value_counts().idxmax()
                st.warning(f"👑 {reg_win.capitalize()}")
            st.write("🏃💨 *Félicitations aux champions, et pour les autres : **bougez-vous les fesses !***")
            st.divider()

        # --- STATS PERSONNELLES ---
        st.header(f"Bienvenue, {user.capitalize()} !")
        total_cal = df["calories"].sum() if not df.empty else 0
        rank_name, next_level, medal, coach_msg = get_rank(total_cal)
        st.info(f"💡 **Le mot du coach :** {coach_msg}")
        
        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("Rang Actuel", rank_name)
            st.write(f"Médaille : **{medal}**")
        with c2:
            prog = min(total_cal / next_level, 1.0)
            st.write(f"Progression ({int(total_cal)} / {next_level} kcal)")
            st.progress(prog)

        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("🔥 Total Brûlé", f"{int(total_cal)} kcal")
        m2.metric("⚖️ Perte Théorique", f"{total_cal / 7700:.2f} kg")
        
        last_7_perso = datetime.now() - timedelta(days=7)
        df_week = df[df['date'] >= last_7_perso] if not df.empty else pd.DataFrame()
        if not df_week.empty:
            day_perf = df_week.groupby('date')['calories'].sum()
            m3.metric("🏆 Record Semaine", f"{int(day_perf.max())} kcal")
            best_s = df_week.groupby('sport')['calories'].sum().idxmax()
            st.write(f"🌟 **Performance de la semaine :** Ton sport n°1 est le **{best_s}** et ton meilleur jour était le **{day_perf.idxmax().strftime('%d/%m')}**.")
        else:
            m3.metric("🏆 Record Semaine", "0 kcal")

    with tab2:
        if not df.empty:
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("Évolution du Poids")
                fig, ax = plt.subplots(); ax.plot(df["date"], df["poids"], marker='o', color='#1E88E5'); ax.axhline(y=obj_val, color='r', linestyle='--'); st.pyplot(fig)
            with col_b:
                st.subheader("Répartition par Sport")
                sport_data = df.groupby("sport")["minutes"].sum()
                fig2, ax2 = plt.subplots(); ax2.pie(sport_data, labels=sport_data.index, autopct='%1.1f%%'); st.pyplot(fig2)
        else: st.warning("Ajoute des données !")

    with tab3:
        st.header("Enregistrer une activité")
        with st.form("seance"):
            d_i = st.date_input("Date", date.today())
            p_i = st.number_input("Poids actuel (kg)", 40.0, 160.0, df.iloc[-1]["poids"] if not df.empty else 75.0)
            s_i = st.selectbox("Sport", ["Natation", "Marche", "Course", "Vélo", "Fitness", "Musculation"])
            m_i = st.number_input("Durée (minutes)", 5, 300, 30)
            if st.form_submit_button("🚀 Sauvegarder sur GitHub"):
                mets = {"Natation": 8, "Marche": 3.5, "Course": 10, "Vélo": 6, "Fitness": 5, "Musculation": 4}
                cal = (m_i/60) * mets[s_i] * p_i
                new_l = pd.DataFrame([{"date": str(d_i), "poids": p_i, "sport": s_i, "minutes": m_i, "calories": cal}])
                df = pd.concat([df, new_l], ignore_index=True)
                save_file(f"user_data/{user}.csv", df.to_csv(index=False))
                st.success("Données synchronisées !"); st.rerun()

    with tab4:
        # --- SECTION GESTION COMPLÈTE RÉTABLIE ---
        st.header("Paramètres du profil")
        new_o = st.number_input("Changer mon objectif (kg)", 40.0, 150.0, obj_val)
        if st.button("Mettre à jour l'objectif"):
            save_file(f"user_data/{user}.obj", str(new_o))
            st.rerun()
            
        st.divider()
        st.subheader("Historique et Suppression")
        if not df.empty:
            st.dataframe(df.sort_values('date', ascending=False))
            del_idx = st.selectbox("Sélectionner l'index à supprimer", df.index)
            if st.button("❌ Supprimer définitivement cette ligne"):
                df = df.drop(del_idx)
                save_file(f"user_data/{user}.csv", df.to_csv(index=False))
                st.success("Supprimé !")
                st.rerun()
        else:
            st.info("Aucune donnée à gérer pour le moment.")
