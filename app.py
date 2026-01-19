import streamlit as st
import pandas as pd
import plotly.express as px
from github import Github, GithubException
from datetime import date, datetime, timedelta
from io import StringIO
import hashlib
import time

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Fitness Gamified Pro", 
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. SÉCURITÉ & UTILITAIRES ---
def hash_pin(pin):
    return hashlib.sha256(str(pin).encode()).hexdigest()

def init_session_state():
    if 'user' not in st.session_state:
        st.session_state.user = None

init_session_state()

# --- 3. GESTION GITHUB ---
@st.cache_resource
def get_github_repo():
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        return g.get_repo(st.secrets["REPO_NAME"])
    except Exception as e:
        st.error(f"⚠️ Erreur GitHub : {e}")
        st.stop()

repo = get_github_repo()

@st.cache_data(ttl=60)
def get_file_content(path):
    try:
        return repo.get_contents(path).decoded_content.decode()
    except:
        return None

def save_file_to_github(path, content, message):
    try:
        try:
            contents = repo.get_contents(path)
            repo.update_file(contents.path, message, content, contents.sha)
        except GithubException:
            repo.create_file(path, message, content)
        get_file_content.clear()
        get_all_users_data.clear()
        return True
    except Exception as e:
        st.error(f"Erreur de sauvegarde : {e}")
        return False

# --- 4. FONCTIONS D'ANALYSE ---
def calculate_streak(df):
    if df.empty: return 0
    dates = pd.to_datetime(df['date']).dt.date.unique()
    dates.sort()
    if len(dates) == 0: return 0
    
    today = date.today()
    last_sport_date = dates[-1]
    
    # Si pas de sport hier ni aujourd'hui, série perdue
    if (today - last_sport_date).days > 1:
        return 0

    streak = 1
    for i in range(len(dates) - 1, 0, -1):
        if (dates[i] - dates[i-1]).days == 1:
            streak += 1
        else:
            break
    return streak

@st.cache_data(ttl=300)
def get_all_users_data():
    all_data = []
    try:
        contents = repo.get_contents("user_data")
        for file in contents:
            if file.name.endswith(".csv"):
                username = file.name.replace(".csv", "")
                csv_content = file.decoded_content.decode()
                temp_df = pd.read_csv(StringIO(csv_content))
                temp_df['date'] = pd.to_datetime(temp_df['date'])
                temp_df['user'] = username
                all_data.append(temp_df)
        return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
    except:
        return pd.DataFrame()

# --- 5. LOGIQUE MÉTIER ---
def get_rank(total_cal):
    levels = [
        (5000, "Débutant 🥚", "Bronze"),
        (15000, "Actif 🐣", "Argent"),
        (30000, "Sportif 🏃", "Or"),
        (60000, "Athlète 🏆", "Platine"),
        (1000000, "Légende 🔥", "Diamant")
    ]
    for limit, name, medal in levels:
        if total_cal < limit: return name, limit, medal
    return levels[-1]

# --- 6. STYLE CSS ---
st.markdown("""
    <style>
    .stMetricValue { font-size: 2rem !important; }
    div[data-testid="stSidebar"] { background-color: rgba(20, 20, 20, 0.95); }
    .podium-box {
        background-color: rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

# --- 7. SIDEBAR ---
st.sidebar.title("🔐 Accès Fitness")
if not st.session_state.user:
    menu = st.sidebar.selectbox("Menu", ["Connexion", "Créer un compte"])
    username = st.sidebar.text_input("Pseudo").strip().lower()
    pin = st.sidebar.text_input("PIN (4 chiffres)", type="password")

    if menu == "Connexion":
        if st.sidebar.button("Se connecter"):
            stored_hash = get_file_content(f"user_data/{username}.pin")
            if stored_hash and stored_hash == hash_pin(pin):
                st.session_state.user = username
                st.rerun()
            else:
                st.sidebar.error("Erreur d'identifiants.")
    elif menu == "Créer un compte":
        obj_weight = st.sidebar.number_input("Objectif (kg)", 40.0, 150.0, 70.0)
        if st.sidebar.button("S'inscrire"):
            if get_file_content(f"user_data/{username}.pin"):
                st.sidebar.error("Pseudo pris.")
            elif len(pin) == 4:
                save_file_to_github(f"user_data/{username}.pin", hash_pin(pin), "New PIN")
                save_file_to_github(f"user_data/{username}.obj", str(obj_weight), "New Obj")
                save_file_to_github(f"user_data/{username}.csv", "date,poids,sport,minutes,calories", "Init CSV")
                st.sidebar.success("Créé ! Connecte-toi.")
else:
    st.sidebar.markdown(f"👤 **{st.session_state.user.capitalize()}**")
    if st.sidebar.button("Déconnexion"):
        st.session_state.user = None
        st.rerun()

# --- 8. APP PRINCIPALE ---
if st.session_state.user:
    user = st.session_state.user
    
    csv_content = get_file_content(f"user_data/{user}.csv")
    obj_content = get_file_content(f"user_data/{user}.obj")
    target_weight = float(obj_content) if obj_content else 70.0
    
    if csv_content:
        df = pd.read_csv(StringIO(csv_content))
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
    else:
        df = pd.DataFrame(columns=["date", "poids", "sport", "minutes", "calories"])

    total_cal = df["calories"].sum() if not df.empty else 0
    rank_name, next_level, medal = get_rank(total_cal)
    current_streak = calculate_streak(df)
    fat_lost_kg = total_cal / 7700

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Accueil", "📈 Stats", "➕ Ajouter", "⚙️ Gestion", "🏆 Classement"])

    with tab1:
        st.title(f"Hello {user.capitalize()} !")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔥 Série", f"{current_streak} Jours")
        c2.metric("🍖 Gras brûlé", f"{fat_lost_kg:.2f} kg")
        c3.metric("⚡ Total", f"{int(total_cal):,}")
        c4.metric("🏅 Rang", rank_name)
        st.progress(min(total_cal / next_level, 1.0))

    with tab2:
        if not df.empty:
            # Ligne 1 : Poids et Calories
            c1, c2 = st.columns(2)
            with c1:
                fig = px.line(df, x='date', y='poids', title="📉 Évolution Poids")
                fig.add_hline(y=target_weight, line_dash="dash", line_color="red")
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                fig2 = px.bar(df, x='date', y='calories', title="🔥 Calories / Jour")
                st.plotly_chart(fig2, use_container_width=True)
            
            # Ligne 2 : LE CAMEMBERT (De retour !)
            st.divider()
            c3, c4 = st.columns([1, 2]) # Mise en page : Camembert un peu plus petit ou centré
            with c4:
                # Camembert (Donut chart)
                fig_pie = px.pie(df, values='minutes', names='sport', title="🍩 Répartition par Sport (Temps)", hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Aucune donnée pour les graphiques.")

    with tab3:
        st.header("Nouvelle séance")
        with st.form("add_sport"):
            col_a, col_b = st.columns(2)
            d_input = col_a.date_input("Date", date.today())
            s_input = col_b.selectbox("Sport", ["Natation", "Marche", "Course", "Vélo", "Fitness", "Musculation", "Crossfit"])
            last_w = df.iloc[-1]['poids'] if not df.empty else 70.0
            p_input = col_a.number_input("Poids (kg)", 40.0, 160.0, float(last_w))
            m_input = col_b.number_input("Durée (min)", 5, 300, 45)
            met = {"Natation": 8, "Marche": 3.5, "Course": 10, "Vélo": 6, "Fitness": 5, "Musculation": 4, "Crossfit": 8}
            
            if st.form_submit_button("Valider"):
                kcal = (m_input/60) * met.get(s_input, 5) * p_input
                new_row = pd.DataFrame([{"date": d_input, "poids": p_input, "sport": s_input, "minutes": m_input, "calories": kcal}])
                df = pd.concat([df, new_row], ignore_index=True)
                save_file_to_github(f"user_data/{user}.csv", df.to_csv(index=False), "Add sport")
                st.success(f"+ {int(kcal)} kcal ajoutées !")
                time.sleep(1)
                st.rerun()

    with tab4:
        if not df.empty:
            edited = st.data_editor(df, num_rows="dynamic")
            if st.button("Sauvegarder les modifications"):
                save_file_to_github(f"user_data/{user}.csv", edited.to_csv(index=False), "Edit")
                st.rerun()

    with tab5:
        st.header("🏆 Hall of Fame (7 derniers jours)")
        df_all = get_all_users_data()
        if not df_all.empty:
            last_7 = pd.Timestamp.now() - pd.Timedelta(days=7)
            df_week = df_all[df_all['date'] >= last_7]
            if not df_week.empty:
                st.subheader("🔥 Les Brûleurs")
                leaderboard = df_week.groupby("user")["calories"].sum().sort_values(ascending=False).head(3)
                cols = st.columns(3)
                medals = ["🥇", "🥈", "🥉"]
                for i, (u, cal) in enumerate(leaderboard.items()):
                    with cols[i]:
                        st.markdown(f"<div class='podium-box'><h1>{medals[i]}</h1><h3>{u.capitalize()}</h3><p>{int(cal)} kcal</p></div>", unsafe_allow_html=True)
                st.divider()
                st.subheader("👑 Champions par Sport")
                sport_perf = df_week.groupby(['sport', 'user'])['minutes'].sum().reset_index()
                best_per_sport = sport_perf.loc[sport_perf.groupby('sport')['minutes'].idxmax()]
                grid = st.columns(3)
                for idx, row in best_per_sport.iterrows():
                    grid[idx % 3].info(f"**{row['sport']}** : {row['user'].capitalize()} ({row['minutes']} min)")
            else:
                st.warning("Pas de sport cette semaine...")
        else:
            st.warning("Données inaccessibles.")
else:
    st.markdown("<h1 style='text-align: center;'>Bienvenue sur Fitness Gamified</h1>", unsafe_allow_html=True)
