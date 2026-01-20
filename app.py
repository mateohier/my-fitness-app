import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import hashlib
import time
import json
import random

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Fitness Gamified Pro", page_icon="🔥", layout="wide")

# --- 2. UTILITAIRES ---
def hash_pin(pin):
    return hashlib.sha256(str(pin).encode()).hexdigest()

def calculate_age(dob_str):
    try:
        dob = datetime.strptime(str(dob_str), "%Y-%m-%d").date()
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except: return 25

def calculate_bmr(weight, height, age, sex):
    # Mifflin-St Jeor
    val = (10 * weight) + (6.25 * height) - (5 * age)
    return val + 5 if sex == "Homme" else val - 161

def get_rank(total_cal):
    levels = [(5000, "Débutant 🥚", "Bronze"), (15000, "Actif 🐣", "Argent"), 
              (30000, "Sportif 🏃", "Or"), (60000, "Athlète 🏆", "Platine")]
    for limit, name, medal in levels:
        if total_cal < limit: return name, limit, medal
    return "Légende 🔥", 1000000, "Diamant"

def get_food_equivalent(calories):
    if calories < 100: return "une Pomme 🍎"
    if calories < 250: return "une Barre chocolatée 🍫"
    if calories < 400: return "un Cheeseburger 🍔"
    if calories < 600: return "un paquet de Frites 🍟"
    if calories < 900: return "une Pizza entière 🍕"
    if calories < 1500: return "un Menu Fast-Food XL 🥤"
    return "un Festin de Roi 🍗"

def get_motivational_quote():
    quotes = [
        "Chaque goutte de sueur est une victoire ! 💦",
        "Tu es plus fort(e) que tu ne le penses ! 💪",
        "N'abandonne jamais, les miracles prennent du temps. ✨",
        "Ton seul ennemi, c'est toi-même d'hier. 🚀",
        "La douleur d'aujourd'hui est la force de demain. 🔥",
        "Petit progrès deviendra grand ! 🌱",
        "Tu es une machine de guerre ! 🤖"
    ]
    return random.choice(quotes)

# --- 3. GESTION DONNÉES (GOOGLE SHEETS) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        df_users = conn.read(worksheet="Profils", ttl=5)
        df_acts = conn.read(worksheet="Activites", ttl=5)
        
        if df_users.empty: 
            df_users = pd.DataFrame(columns=["user", "pin", "json_data"])
        if df_acts.empty: 
            df_acts = pd.DataFrame(columns=["date", "user", "sport", "minutes", "calories", "poids"])
            
        df_acts['date'] = pd.to_datetime(df_acts['date'], errors='coerce')
        df_acts['poids'] = pd.to_numeric(df_acts['poids'], errors='coerce')
        df_acts['calories'] = pd.to_numeric(df_acts['calories'], errors='coerce')
        df_acts = df_acts.dropna(subset=['date'])
        
        return df_users, df_acts
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()

def save_activity(new_row):
    try:
        df_acts = conn.read(worksheet="Activites", ttl=0)
        updated_df = pd.concat([df_acts, new_row], ignore_index=True)
        updated_df['date'] = pd.to_datetime(updated_df['date'], errors='coerce')
        updated_df['date'] = updated_df['date'].dt.strftime('%Y-%m-%d')
        updated_df['poids'] = updated_df['poids'].astype(float)
        conn.update(worksheet="Activites", data=updated_df)
        st.cache_data.clear()
        return True
    except: return False

def save_user(username, pin_hash, profile_data):
    try:
        df_users = conn.read(worksheet="Profils", ttl=0)
        json_str = json.dumps(profile_data)
        if not df_users.empty and username in df_users['user'].values:
            df_users.loc[df_users['user'] == username, 'json_data'] = json_str
        else:
            new_user = pd.DataFrame([{"user": username, "pin": pin_hash, "json_data": json_str}])
            df_users = pd.concat([df_users, new_user], ignore_index=True)
        conn.update(worksheet="Profils", data=df_users)
        st.cache_data.clear()
        return True
    except: return False

def update_history(df_edited):
    try:
        df_all_acts = conn.read(worksheet="Activites", ttl=0)
        current_user = st.session_state.user
        df_others = df_all_acts[df_all_acts['user'] != current_user]
        df_edited['user'] = current_user
        df_final = pd.concat([df_others, df_edited], ignore_index=True)
        df_final['date'] = pd.to_datetime(df_final['date'], errors='coerce')
        df_final['date'] = df_final['date'].dt.strftime('%Y-%m-%d')
        df_final['poids'] = pd.to_numeric(df_final['poids'], errors='coerce')
        conn.update(worksheet="Activites", data=df_final)
        st.cache_data.clear()
        return True
    except: return False

# --- 4. CSS & STATE ---
if 'user' not in st.session_state: st.session_state.user = None

st.markdown("""
    <style>
    .stMetricValue { font-size: 2rem !important; }
    div[data-testid="stSidebar"] { background-color: rgba(20, 20, 20, 0.95); }
    .quote-box {
        padding: 15px; background: linear-gradient(45deg, #FF4B4B, #FF9068);
        border-radius: 10px; color: white; text-align: center;
        font-size: 1.2rem; font-weight: bold; margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4);
    }
    .journey-box { background-color:rgba(255,255,255,0.05); padding:15px; border-radius:10px; border:1px solid #444; }
    </style>
""", unsafe_allow_html=True)

# --- 5. LOGIQUE PRINCIPALE ---
df_users, df_acts = get_data()

# --- SIDEBAR ---
st.sidebar.title("🔐 Accès Fitness")
ACTIVITY_OPTS = ["Sédentaire (1.2)", "Légèrement actif (1.375)", "Actif (1.55)", "Très actif (1.725)"]
ACT_MAP = {k: v for k, v in zip(ACTIVITY_OPTS, [1.2, 1.375, 1.55, 1.725])}

# Liste des sports
SPORTS_LIST = [
    "Musculation", "Course", "Vélo", "Natation", "Crossfit", "Fitness", "Marche",
    "Tennis", "Football", "Basket", "Boxe", "Yoga", "Pilates", "Escalade", 
    "Randonnée", "Danse", "Badminton", "Ski", "Rugby", "Volley"
]

if not st.session_state.user:
    menu = st.sidebar.selectbox("Menu", ["Connexion", "Créer un compte"])
    u_input = st.sidebar.text_input("Pseudo").strip().lower()
    p_input = st.sidebar.text_input("PIN (4 chiffres)", type="password")
    
    if menu == "Connexion":
        if st.sidebar.button("Se connecter"):
            if not df_users.empty and u_input in df_users['user'].values:
                stored_pin = df_users[df_users['user'] == u_input].iloc[0]['pin']
                if stored_pin == hash_pin(p_input):
                    st.session_state.user = u_input
                    st.rerun()
                else: st.sidebar.error("Mauvais PIN")
            else: st.sidebar.error("Utilisateur inconnu")
            
    elif menu == "Créer un compte":
        st.sidebar.markdown("### Profil")
        dob = st.sidebar.date_input("Naissance", value=date(1990,1,1), min_value=date(1900,1,1), max_value=date.today())
        sex = st.sidebar.selectbox("Sexe", ["Homme", "Femme"])
        h = st.sidebar.number_input("Taille (cm)", 100, 250, 175)
        act = st.sidebar.selectbox("Activité", ACTIVITY_OPTS)
        w_init = st.sidebar.number_input("Poids actuel (kg)", 30.0, 200.0, 70.0)
        w_obj = st.sidebar.number_input("Objectif (kg)", 30.0, 200.0, 65.0)
        
        if st.sidebar.button("S'inscrire"):
            if not df_users.empty and u_input in df_users['user'].values:
                st.sidebar.error("Pseudo pris")
            elif len(p_input) == 4:
                prof = {"dob": str(dob), "sex": sex, "h": h, "act": act, "w_init": w_init, "w_obj": w_obj}
                if save_user(u_input, hash_pin(p_input), prof):
                    st.sidebar.success("Compte créé ! Connecte-toi.")
                    time.sleep(1)
                    st.rerun()

else:
    user = st.session_state.user
    st.sidebar.markdown(f"👤 **{user.capitalize()}**")
    if st.sidebar.button("Déconnexion"):
        st.session_state.user = None
        st.rerun()
        
    user_row = df_users[df_users['user'] == user].iloc[0]
    prof = json.loads(user_row['json_data'])
    
    my_df = df_acts[df_acts['user'] == user].copy()
    start_weight = float(prof.get('w_init', 70.0))
    target_weight = float(prof.get('w_obj', 65.0))
    
    if not my_df.empty:
        my_df = my_df.sort_values('date')
        last_weight = float(my_df.iloc[-1]['poids'])
    else:
        last_weight = start_weight

    age = calculate_age(prof.get('dob', '1990-01-01'))
    total_cal = my_df['calories'].sum() if not my_df.empty else 0
    rank, next_lvl, _ = get_rank(total_cal)
    
    streak = 0
    if not my_df.empty:
        dates = pd.to_datetime(my_df['date']).dt.date.unique()
        dates.sort()
        if len(dates) > 0:
            today = date.today()
            if (today - dates[-1]).days <= 1:
                streak = 1
                for i in range(len(dates)-1, 0, -1):
                    if (dates[i] - dates[i-1]).days == 1: streak += 1
                    else: break
            else: streak = 0

    t1, t2, t3, t4, t5 = st.tabs(["🏠 Dashboard", "📈 Graphiques", "➕ Séance", "⚙️ Gestion", "🏆 Leaderboard"])
    
    with t1:
        # 1. CITATION
        quote = get_motivational_quote()
        st.markdown(f"<div class='quote-box'>✨ {quote}</div>", unsafe_allow_html=True)
        st.title(f"Bonjour {user.capitalize()}")

        # 2. KPI
        height_m = prof['h'] / 100
        imc = last_weight / (height_m ** 2)
        if imc < 18.5: imc_status = "Maigreur"
        elif 18.5 <= imc < 25: imc_status = "Normal ✅"
        elif 25 <= imc < 30: imc_status = "Surpoids ⚠️"
        else: imc_status = "Obésité 🚨"
        
        gras_brule_kg = total_cal / 7700

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔥 Série", f"{streak} Jours")
        c2.metric("⚖️ Gras Brûlé", f"{gras_brule_kg:.2f} kg", f"Basé sur {int(total_cal)} kcal")
        c3.metric("⚡ Total Burn", f"{int(total_cal):,} kcal")
        c4.metric("🩺 IMC", f"{imc:.1f}", imc_status)

        # 3. VISUELS
        st.divider()
        col_gauche, col_droite = st.columns([1, 1])

        with col_gauche:
            st.subheader("🧬 ADN Sportif")
            stats = {"Force": 10, "Endurance": 10, "Agilité": 10, "Mental": 10}
            if not my_df.empty:
                # Catégorisation des sports
                stats["Force"] += my_df[my_df['sport'].isin(["Musculation", "Crossfit", "Escalade", "Boxe", "Rugby"])]['minutes'].sum()
                stats["Endurance"] += my_df[my_df['sport'].isin(["Course", "Vélo", "Marche", "Natation", "Tennis", "Football", "Basket", "Badminton", "Ski", "Randonnée"])]['minutes'].sum()
                stats["Agilité"] += my_df[my_df['sport'].isin(["Fitness", "Yoga", "Pilates", "Danse", "Volley"])]['minutes'].sum()
                stats["Mental"] += len(my_df) * 15

            data_rpg = pd.DataFrame({'Stat': list(stats.keys()), 'Valeur': [min(v, 300) for v in stats.values()]})
            fig_rpg = px.line_polar(data_rpg, r='Valeur', theta='Stat', line_close=True)
            fig_rpg.update_traces(fill='toself', line_color='#FF4B4B')
            fig_rpg.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, max(data_rpg['Valeur'])+20])), 
                                  margin=dict(t=20, b=20, l=20, r=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_rpg, use_container_width=True)

        with col_droite:
            st.subheader("🌍 Voyage Virtuel")
            km_virtuels = total_cal / 60
            villes = [("Lille", 0), ("Paris", 225), ("Lyon", 690), ("Valence", 790), ("Marseille", 1000)]
            prochaine_ville, km_restant = "Marseille ☀️", 0
            for v, dist in villes:
                if km_virtuels < dist:
                    prochaine_ville = v
                    km_restant = dist - km_virtuels
                    break
            
            st.markdown(f"""
            <div class='journey-box'>
                <h3>🏃‍♂️ {int(km_virtuels)} km parcourus</h3>
                <p>Direction <b>{prochaine_ville}</b> (encore {int(km_restant)} km)</p>
            </div>
            """, unsafe_allow_html=True)
            st.progress(min(km_virtuels / 1000, 1.0))
            
            st.subheader("🍔 Équivalence")
            st.info(f"Tu as brûlé : **{get_food_equivalent(total_cal)}**")

        # 4. CALENDRIER
        st.divider()
        st.subheader("📅 Calendrier de régularité")
        
        today = date.today()
        start_year = date(today.year, 1, 1)
        all_dates = pd.date_range(start_year, today)
        df_cal = pd.DataFrame({"date": all_dates})
        df_cal['date'] = df_cal['date'].dt.date
        
        if not my_df.empty:
            my_df['date_only'] = my_df['date'].dt.date
            daily_activity = my_df.groupby('date_only')['minutes'].sum().reset_index()
            df_cal = pd.merge(df_cal, daily_activity, left_on='date', right_on='date_only', how='left').fillna(0)
        else:
            df_cal['minutes'] = 0
            
        df_cal['week'] = pd.to_datetime(df_cal['date']).dt.isocalendar().week
        df_cal['day_of_week'] = pd.to_datetime(df_cal['date']).dt.dayofweek
        days = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
        
        fig_cal = go.Figure(data=go.Heatmap(
            x=df_cal['week'], y=df_cal['day_of_week'], z=df_cal['minutes'],
            colorscale=[[0, '#2d2d2d'], [0.1, '#0e4429'], [1, '#39d353']],
            showscale=False, xgap=3, ygap=3, hoverongaps=False,
            hovertemplate='Semaine %{x}, %{y}: %{z} min<extra></extra>'
        ))
        fig_cal.update_layout(
            height=200, yaxis=dict(tickmode='array', tickvals=[0,1,2,3,4,5,6], ticktext=days, showgrid=False, zeroline=False),
            xaxis=dict(showgrid=False, zeroline=False, title="Semaines de l'année"),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_cal, use_container_width=True)


    with t2:
        if not my_df.empty:
            c1, c2 = st.columns(2)
            fig1 = px.line(my_df, x='date', y='poids', title="📉 Évolution Poids")
            fig1.add_hline(y=prof['w_obj'], line_dash="dash", line_color="green", annotation_text="Objectif")
            c1.plotly_chart(fig1, use_container_width=True)
            
            fig2 = px.bar(my_df, x='date', y='calories', title="🔥 Calories Brûlées")
            c2.plotly_chart(fig2, use_container_width=True)
            
            fig3 = px.pie(my_df, values='minutes', names='sport', hole=0.4, title="⏳ Répartition Temps")
            st.plotly_chart(fig3, use_container_width=True)
        else: st.info("Pas encore de données. Ajoute une séance !")

    with t3:
        bmr = calculate_bmr(last_weight, prof['h'], age, prof['sex'])
        tdee = bmr * ACT_MAP.get(prof['act'], 1.2)
        st.info(f"💡 Calories journalières (Maintenance) : **{int(tdee)} kcal**")
        
        with st.form("add"):
            c1, c2 = st.columns(2)
            d = c1.date_input("Date", date.today())
            s = c2.selectbox("Sport", SPORTS_LIST) # Liste complète
            w = c1.number_input("Poids (kg)", 0.0, 200.0, float(last_weight))
            m = c2.number_input("Durée (min)", 1, 300, 45)
            
            if st.form_submit_button("Sauvegarder"):
                # Dictionnaire MET complet
                met = {
                    "Course": 10, "Vélo": 7, "Natation": 8, "Musculation": 4, "Crossfit": 8,
                    "Marche": 3.5, "Fitness": 6, "Tennis": 7, "Football": 8, "Basket": 8,
                    "Boxe": 10, "Yoga": 3, "Pilates": 3, "Escalade": 8, "Randonnée": 6,
                    "Danse": 5, "Badminton": 6, "Ski": 7, "Rugby": 9, "Volley": 4
                }
                cal_sport = (calculate_bmr(w, prof['h'], age, prof['sex']) / 24) * met.get(s, 5) * (m/60)
                
                new_act = pd.DataFrame([{
                    "date": pd.to_datetime(d), "user": user, "sport": s, 
                    "minutes": m, "calories": round(cal_sport), "poids": float(w)
                }])
                
                with st.spinner("Sauvegarde..."):
                    if save_activity(new_act):
                        st.success(f"+{int(cal_sport)} kcal !")
                        time.sleep(1)
                        st.rerun()

    with t4:
        st.subheader("👤 Modifier mon profil")
        with st.form("edit_prof"):
            col1, col2 = st.columns(2)
            new_dob = col1.date_input("Date de naissance", value=datetime.strptime(prof.get('dob', '1990-01-01'), "%Y-%m-%d"), min_value=date(1900,1,1), max_value=date.today())
            
            sex_opts = ["Homme", "Femme"]
            curr_sex = prof.get('sex', 'Homme')
            idx_sex = sex_opts.index(curr_sex) if curr_sex in sex_opts else 0
            new_sex = col2.selectbox("Sexe", sex_opts, index=idx_sex)
            
            col3, col4 = st.columns(2)
            new_h = col3.number_input("Taille (cm)", 100, 250, int(prof.get('h', 175)))
            
            curr_act = prof.get('act', ACTIVITY_OPTS[0])
            idx_act = ACTIVITY_OPTS.index(curr_act) if curr_act in ACTIVITY_OPTS else 0
            new_act = col4.selectbox("Niveau d'activité", ACTIVITY_OPTS, index=idx_act)
            
            col5, col6 = st.columns(2)
            new_w_init = col5.number_input("Poids de départ (kg)", 30.0, 200.0, float(prof.get('w_init', 70.0)))
            new_obj = col6.number_input("Objectif Poids (kg)", 30.0, 200.0, float(prof.get('w_obj', 65.0)))
            
            if st.form_submit_button("💾 Enregistrer"):
                prof.update({"dob": str(new_dob), "sex": new_sex, "h": new_h, "act": new_act, "w_init": new_w_init, "w_obj": new_obj})
                if save_user(user, user_row['pin'], prof):
                    st.success("✅ Profil mis à jour !")
                    time.sleep(1)
                    st.rerun()

        st.subheader("📝 Modifier l'historique")
        if not my_df.empty:
            col_config = {
                "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD", step=1),
                "poids": st.column_config.NumberColumn("Poids (kg)", format="%.1f"),
                "calories": st.column_config.NumberColumn("Calories", format="%.1f")
            }
            edited = st.data_editor(my_df[['date', 'sport', 'minutes', 'calories', 'poids']], num_rows="dynamic", use_container_width=True, column_config=col_config)
            if st.button("Sauvegarder historique"):
                if update_history(edited):
                    st.success("Historique corrigé")
                    time.sleep(1)
                    st.rerun()

    with t5:
        st.header("🏆 Classement (7 jours)")
        if not df_acts.empty:
            now = pd.Timestamp.now()
            week_df = df_acts[df_acts['date'] >= (now - pd.Timedelta(days=7))]
            if not week_df.empty:
                top = week_df.groupby("user")['calories'].sum().sort_values(ascending=False).head(3)
                cols = st.columns(3)
                medals = ["🥇", "🥈", "🥉"]
                for i, (u, c) in enumerate(top.items()):
                    cols[i].markdown(f"<div class='podium-box'><h1>{medals[i]}</h1><h3>{u}</h3><p>{int(c)} kcal</p></div>", unsafe_allow_html=True)
                st.divider()
                st.subheader("Rois du sport")
                best = week_df.groupby(['sport', 'user'])['minutes'].sum().reset_index()
                best = best.loc[best.groupby('sport')['minutes'].idxmax()]
                grid = st.columns(3)
                for i, row in best.reset_index().iterrows():
                    grid[i%3].info(f"**{row['sport']}**: {row['user']} ({row['minutes']} min)")
            else: st.warning("Pas de sport cette semaine.")
