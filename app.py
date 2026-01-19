import streamlit as st
import pandas as pd
import plotly.express as px
from github import Github, GithubException
from datetime import date, datetime, timedelta
from io import StringIO
import hashlib
import time
import json

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

# --- 4. FONCTIONS SCIENTIFIQUES ---
def calculate_age_from_dob(dob_str):
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except:
        return 25 

def calculate_bmr(weight, height_cm, age, gender):
    # Formule Mifflin-St Jeor
    bmr = (10 * weight) + (6.25 * height_cm) - (5 * age)
    if gender == "Homme":
        bmr += 5
    else:
        bmr -= 161
    return bmr

def calculate_calories_burned(bmr, met, duration_minutes):
    bmr_hourly = bmr / 24
    duration_hours = duration_minutes / 60
    return bmr_hourly * met * duration_hours

def calculate_streak(df):
    if df.empty: return 0
    dates = pd.to_datetime(df['date']).dt.date.unique()
    dates.sort()
    if len(dates) == 0: return 0
    
    today = date.today()
    last_sport_date = dates[-1]
    
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
        st.sidebar.markdown("### 📝 Votre Profil")
        
        # --- MODIFICATION : Min=1950, Max=Aujourd'hui ---
        dob = st.sidebar.date_input("Date de naissance", date(1995, 1, 1), min_value=date(1950, 1, 1), max_value=date.today())
        
        col_s1, col_s2 = st.sidebar.columns(2)
        sexe = col_s1.selectbox("Sexe", ["Homme", "Femme"])
        taille = col_s2.number_input("Taille (cm)", 100, 250, 175)
        
        poids_init = st.sidebar.number_input("Poids Initial (kg)", 20.0, 300.0, 75.0)
        obj_weight = st.sidebar.number_input("Objectif Poids (kg)", 20.0, 300.0, 70.0)
        
        if st.sidebar.button("S'inscrire"):
            if get_file_content(f"user_data/{username}.pin"):
                st.sidebar.error("Ce pseudo est déjà pris.")
            elif len(pin) == 4:
                save_file_to_github(f"user_data/{username}.pin", hash_pin(pin), "New PIN")
                
                profile_data = {
                    "birth_date": str(dob),
                    "sexe": sexe,
                    "taille": taille,
                    "initial_weight": poids_init,
                    "objectif": obj_weight
                }
                save_file_to_github(f"user_data/{username}.json", json.dumps(profile_data), "New Profile")
                
                first_row = f"date,poids,sport,minutes,calories\n{date.today()}, {poids_init},Inscription,0,0"
                save_file_to_github(f"user_data/{username}.csv", first_row, "Init CSV")
                
                st.sidebar.success("Profil créé ! Connecte-toi.")
                time.sleep(1)
else:
    st.sidebar.markdown(f"👤 **{st.session_state.user.capitalize()}**")
    if st.sidebar.button("Déconnexion"):
        st.session_state.user = None
        st.rerun()

# --- 8. APP PRINCIPALE ---
if st.session_state.user:
    user = st.session_state.user
    
    csv_content = get_file_content(f"user_data/{user}.csv")
    json_profile = get_file_content(f"user_data/{user}.json")
    
    current_age = 25
    initial_w = 75.0
    
    if json_profile:
        profile = json.loads(json_profile)
        if "birth_date" in profile:
            current_age = calculate_age_from_dob(profile["birth_date"])
        else:
            current_age = profile.get("age", 25)
        initial_w = profile.get("initial_weight", 75.0)
    else:
        old_obj = get_file_content(f"user_data/{user}.obj")
        profile = {
            "sexe": "Homme", "taille": 175, 
            "objectif": float(old_obj) if old_obj else 70.0
        }

    if csv_content:
        df = pd.read_csv(StringIO(csv_content))
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
    else:
        df = pd.DataFrame(columns=["date", "poids", "sport", "minutes", "calories"])

    total_cal = df["calories"].sum() if not df.empty else 0
    rank_name, next_level, medal = get_rank(total_cal)
    current_streak = calculate_streak(df)
    
    last_weight = df.iloc[-1]['poids'] if not df.empty else initial_w
    total_lost = initial_w - last_weight
    color_delta = "normal" if total_lost > 0 else "off"

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Accueil", "📈 Stats", "➕ Ajouter", "⚙️ Gestion", "🏆 Classement"])

    with tab1:
        st.title(f"Hello {user.capitalize()} !")
        st.caption(f"Profil : {profile['sexe']} | {current_age} ans | {profile['taille']} cm | Départ : {initial_w} kg")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔥 Série", f"{current_streak} Jours")
        c2.metric("⚖️ Perte Totale", f"{total_lost:.1f} kg", f"Depuis {initial_w}kg", delta_color=color_delta)
        c3.metric("⚡ Total Burn", f"{int(total_cal):,} kcal")
        c4.metric("🏅 Rang", rank_name)
        st.progress(min(total_cal / next_level, 1.0))

    with tab2:
        if not df.empty:
            c1, c2 = st.columns(2)
            with c1:
                fig = px.line(df, x='date', y='poids', title="📉 Évolution Poids")
                fig.add_hline(y=profile['objectif'], line_dash="dash", line_color="green", annotation_text="Objectif")
                fig.add_hline(y=initial_w, line_dash="dot", line_color="red", annotation_text="Départ")
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                fig2 = px.bar(df, x='date', y='calories', title="🔥 Calories / Jour")
                st.plotly_chart(fig2, use_container_width=True)
            
            st.divider()
            c3, c4 = st.columns([1, 2])
            with c4:
                fig_pie = px.pie(df, values='minutes', names='sport', title="🍩 Répartition par Sport (Temps)", hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Aucune donnée pour les graphiques.")

    with tab3:
        st.header("Nouvelle séance")
        current_bmr = calculate_bmr(last_weight, profile['taille'], current_age, profile['sexe'])
        st.info(f"💡 Métabolisme de base (âge {current_age} ans) : **{int(current_bmr)} kcal/jour**.")

        with st.form("add_sport"):
            col_a, col_b = st.columns(2)
            d_input = col_a.date_input("Date", date.today())
            s_input = col_b.selectbox("Sport", ["Natation", "Marche", "Course", "Vélo", "Fitness", "Musculation", "Crossfit"])
            
            p_input = col_a.number_input("Poids actuel (kg)", 20.0, 300.0, float(last_weight))
            m_input = col_b.number_input("Durée (min)", 5, 300, 45)
            met_values = {"Natation": 8, "Marche": 3.5, "Course": 10, "Vélo": 6, "Fitness": 5, "Musculation": 4, "Crossfit": 8}
            
            if st.form_submit_button("Valider"):
                bmr_day = calculate_bmr(p_input, profile['taille'], current_age, profile['sexe'])
                kcal = calculate_calories_burned(bmr_day, met_values.get(s_input, 5), m_input)
                
                new_row = pd.DataFrame([{"date": d_input, "poids": p_input, "sport": s_input, "minutes": m_input, "calories": round(kcal, 2)}])
                df = pd.concat([df, new_row], ignore_index=True)
                save_file_to_github(f"user_data/{user}.csv", df.to_csv(index=False), "Add sport")
                st.success(f"✅ Séance enregistrée : {int(kcal)} kcal")
                time.sleep(1)
                st.rerun()

    with tab4:
        st.subheader("⚙️ Mettre à jour mon profil")
        try:
            default_dob = datetime.strptime(profile.get("birth_date", "1990-01-01"), "%Y-%m-%d").date()
        except:
            default_dob = date(1990, 1, 1)

        with st.form("update_profile"):
            c_up1, c_up2 = st.columns(2)
            
            # --- MODIFICATION : Min=1950, Max=Aujourd'hui ---
            new_dob = c_up1.date_input("Date de naissance", default_dob, min_value=date(1950, 1, 1), max_value=date.today())
            
            sex_options = ["Homme", "Femme"]
            current_sex = profile.get("sexe", "Homme")
            idx_sex = sex_options.index(current_sex) if current_sex in sex_options else 0
            new_sexe = c_up2.selectbox("Sexe", sex_options, index=idx_sex)
            
            c_up3, c_up4 = st.columns(2)
            new_taille = c_up3.number_input("Taille (cm)", 100, 250, int(profile['taille']))
            new_init_w = c_up4.number_input("Poids Initial (kg)", 20.0, 300.0, float(initial_w))
            
            new_obj = st.number_input("Objectif (kg)", 20.0, 300.0, float(profile['objectif']))
            
            if st.form_submit_button("💾 Sauvegarder les modifications"):
                profile['birth_date'] = str(new_dob)
                profile['sexe'] = new_sexe
                profile['initial_weight'] = new_init_w
                profile['taille'] = new_taille
                profile['objectif'] = new_obj
                
                if 'age' in profile: del profile['age']
                
                save_file_to_github(f"user_data/{user}.json", json.dumps(profile), "Update Profile Full")
                st.success("Profil mis à jour !")
                time.sleep(1)
                st.rerun()
                
        st.divider()
        st.subheader("📝 Editer l'historique")
        if not df.empty:
            edited = st.data_editor(df, num_rows="dynamic")
            if st.button("Sauvegarder l'historique"):
                save_file_to_github(f"user_data/{user}.csv", edited.to_csv(index=False), "Edit CSV")
                st.rerun()

    with tab5:
        st.header("🏆 Hall of Fame (7 jours)")
        df_all = get_all_users_data()
        if not df_all.empty:
            last_7 = pd.Timestamp.now() - pd.Timedelta(days=7)
            df_week = df_all[df_all['date'] >= last_7]
            if not df_week.empty:
                st.subheader("🔥 Top Brûleurs")
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
            st.warning("Données indisponibles.")

else:
    st.markdown("<h1 style='text-align: center;'>Bienvenue sur Fitness Gamified</h1>", unsafe_allow_html=True)
