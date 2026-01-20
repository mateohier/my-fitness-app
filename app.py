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
import numpy as np
import requests
from streamlit_lottie import st_lottie

# --- 1. CONFIGURATION & CONSTANTES ---
st.set_page_config(page_title="Fitness Gamified Pro", page_icon="🔥", layout="wide")

# URLs Animations
LOTTIE_SUCCESS = "https://assets5.lottiefiles.com/packages/lf20_u4yrau.json"
LOTTIE_GYM = "https://lottie.host/5a88c7f9-2819-4592-9654-20b18fa2409f/18qFh7lXyR.json"

# Image de fond
BACKGROUND_URL = "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=1470&auto=format&fit=crop"

# --- MAPPING ADN (Compétences Globales) ---
# Force, Endurance, Agilité, Mental (Score arbitraire sur 10 par heure de pratique)
DNA_MAP = {
    "Musculation": {"Force": 9, "Endurance": 2, "Agilité": 2, "Mental": 7},
    "Crossfit":    {"Force": 8, "Endurance": 7, "Agilité": 6, "Mental": 9},
    "Course":      {"Force": 2, "Endurance": 10, "Agilité": 3, "Mental": 8},
    "Vélo":        {"Force": 4, "Endurance": 9, "Agilité": 3, "Mental": 6},
    "Natation":    {"Force": 5, "Endurance": 9, "Agilité": 5, "Mental": 7},
    "Yoga":        {"Force": 3, "Endurance": 3, "Agilité": 10, "Mental": 8},
    "Boxe":        {"Force": 6, "Endurance": 8, "Agilité": 8, "Mental": 9},
    "Escalade":    {"Force": 7, "Endurance": 5, "Agilité": 9, "Mental": 9},
    "Tennis":      {"Force": 4, "Endurance": 7, "Agilité": 9, "Mental": 6},
    "Football":    {"Force": 4, "Endurance": 8, "Agilité": 7, "Mental": 6},
    "Basket":      {"Force": 4, "Endurance": 8, "Agilité": 8, "Mental": 6},
    "Marche":      {"Force": 1, "Endurance": 4, "Agilité": 1, "Mental": 3},
    "Danse":       {"Force": 3, "Endurance": 6, "Agilité": 10, "Mental": 5},
    "Pilates":     {"Force": 4, "Endurance": 3, "Agilité": 8, "Mental": 6},
    "Ski":         {"Force": 6, "Endurance": 7, "Agilité": 6, "Mental": 5},
    "Rugby":       {"Force": 8, "Endurance": 7, "Agilité": 6, "Mental": 9}
}

# --- MAPPING MUSCLES (Pour l'Anatomie) ---
MUSCLE_MAP = {
    "Musculation": {"Bras": 8, "Pecs": 8, "Dos": 8, "Jambes": 6, "Cardio": 2},
    "Course": {"Jambes": 10, "Cardio": 9, "Dos": 2, "Bras": 1},
    "Vélo": {"Jambes": 9, "Cardio": 8, "Mollets": 9, "Dos": 3},
    "Natation": {"Dos": 10, "Bras": 9, "Cardio": 8, "Jambes": 6, "Pecs": 5},
    "Crossfit": {"Bras": 8, "Jambes": 8, "Cardio": 9, "Pecs": 7, "Dos": 7},
    "Fitness": {"Cardio": 8, "Jambes": 6, "Bras": 5, "Abdos": 7},
    "Boxe": {"Bras": 9, "Cardio": 10, "Dos": 6, "Jambes": 7, "Abdos": 8},
    "Yoga": {"Souplesse": 10, "Dos": 7, "Abdos": 6, "Jambes": 5},
    "Escalade": {"Bras": 10, "Dos": 9, "Jambes": 7, "Abdos": 8},
    "Tennis": {"Bras": 7, "Jambes": 8, "Cardio": 8},
    "Football": {"Jambes": 9, "Cardio": 9, "Abdos": 5},
    "Basket": {"Jambes": 8, "Cardio": 9, "Bras": 5},
    "Marche": {"Cardio": 4, "Jambes": 5},
    "Pilates": {"Abdos": 10, "Dos": 7, "Jambes": 5},
    "Danse": {"Jambes": 8, "Cardio": 7, "Abdos": 6},
    "Rugby": {"Jambes": 9, "Bras": 8, "Pecs": 7, "Dos": 7, "Cardio": 8}
}
SPORTS_LIST = sorted(list(DNA_MAP.keys()))

# Coordonnées corporelles pour le graphique (X, Y)
BODY_COORDS = {
    "Cardio": (0, 5.5),     # Tête/Cœur
    "Pecs": (0, 4),       # Torse
    "Dos": (0, 3.8),      # (Superposé au torse mais on gère par couleur)
    "Bras": (2.5, 3.5),   # Bras Droit (Symétrie gérée plus bas)
    "Abdos": (0, 2.5),    # Ventre
    "Jambes": (1.2, 0.5), # Jambe Droite
    "Mollets": (1.3, -1.5),
    "Souplesse": (0, 1)   # Centre de gravité
}

# --- 2. UTILITAIRES ---
def hash_pin(pin):
    return hashlib.sha256(str(pin).encode()).hexdigest()

def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200: return None
        return r.json()
    except: return None

def calculate_age(dob_str):
    try:
        dob = datetime.strptime(str(dob_str), "%Y-%m-%d").date()
        return date.today().year - dob.year
    except: return 25

def calculate_bmr(weight, height, age, sex):
    val = (10 * weight) + (6.25 * height) - (5 * age)
    return val + 5 if sex == "Homme" else val - 161

def get_level_progress(total_cal):
    factor = 100 
    if total_cal == 0: return 1, 0.0, 100
    level = int((total_cal / factor) ** 0.5)
    if level == 0: level = 1
    cal_current = factor * (level ** 2)
    cal_next = factor * ((level + 1) ** 2)
    percent = min(max((total_cal - cal_current) / (cal_next - cal_current), 0.0), 1.0)
    return level, percent, int(cal_next - total_cal)

def get_food_equivalent(calories):
    if calories < 100: return "une Pomme 🍎"
    if calories < 250: return "une Barre chocolatée 🍫"
    if calories < 500: return "un Cheeseburger 🍔"
    if calories < 1000: return "une Pizza 🍕"
    return "un Festin 🍗"

def get_motivational_quote():
    return random.choice(["Chaque goutte de sueur compte ! 💦", "Tu es une machine ! 🤖", "La douleur est temporaire. 🔥", "Pas d'excuses. 🚀"])

def predict_success(df, current_weight, target_weight):
    if len(df) < 5: return None, "Données insuffisantes"
    df = df.sort_values('date').dropna(subset=['poids'])
    df['date_ord'] = df['date'].map(pd.Timestamp.toordinal)
    if len(df) < 2: return None, "Pas assez de points"
    slope, intercept = np.polyfit(df['date_ord'].values, df['poids'].values, 1)
    if slope >= 0: return None, "Tendance stable ou hausse"
    target_date = date.fromordinal(int((target_weight - intercept) / slope))
    days = (target_date - date.today()).days
    if days < 0: return None, "Objectif atteint !"
    return target_date, f"Prévu dans **{days} jours**"

# --- 3. GESTION DONNÉES ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        df_users = conn.read(worksheet="Profils", ttl=600)
        df_acts = conn.read(worksheet="Activites", ttl=600)
        if df_users.empty: df_users = pd.DataFrame(columns=["user", "pin", "json_data"])
        if df_acts.empty: df_acts = pd.DataFrame(columns=["date", "user", "sport", "minutes", "calories", "poids"])
        df_acts['date'] = pd.to_datetime(df_acts['date'], errors='coerce')
        df_acts = df_acts.dropna(subset=['date'])
        return df_users, df_acts
    except: return pd.DataFrame(), pd.DataFrame()

def save_activity(new_row):
    try:
        df_acts = conn.read(worksheet="Activites", ttl=0)
        updated_df = pd.concat([df_acts, new_row], ignore_index=True)
        updated_df['date'] = pd.to_datetime(updated_df['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
        conn.update(worksheet="Activites", data=updated_df)
        st.cache_data.clear()
        return True
    except: return False

def save_user(u, p, data):
    try:
        df_users = conn.read(worksheet="Profils", ttl=0)
        json_str = json.dumps(data)
        if not df_users.empty and u in df_users['user'].values:
            df_users.loc[df_users['user'] == u, 'json_data'] = json_str
        else:
            df_users = pd.concat([df_users, pd.DataFrame([{"user": u, "pin": p, "json_data": json_str}])], ignore_index=True)
        conn.update(worksheet="Profils", data=df_users)
        st.cache_data.clear()
        return True
    except: return False

def update_history(df_edited):
    try:
        df_all = conn.read(worksheet="Activites", ttl=0)
        df_others = df_all[df_all['user'] != st.session_state.user]
        df_edited['user'] = st.session_state.user
        df_edited['date'] = pd.to_datetime(df_edited['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
        conn.update(worksheet="Activites", data=pd.concat([df_others, df_edited], ignore_index=True))
        st.cache_data.clear()
        return True
    except: return False

# --- 4. CSS ---
if 'user' not in st.session_state: st.session_state.user = None

st.markdown(f"""
    <style>
    .stApp {{ background-image: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("{BACKGROUND_URL}"); background-size: cover; background-attachment: fixed; }}
    .stMetricValue {{ font-size: 1.8rem !important; color: white !important; }}
    div[data-testid="stSidebar"] {{ background-color: rgba(20, 20, 20, 0.95); }}
    .quote-box {{ padding: 15px; background: linear-gradient(45deg, #FF4B4B, #FF9068); border-radius: 10px; color: white; text-align: center; font-weight: bold; margin-bottom: 20px; }}
    .glass-box {{ background-color:rgba(255,255,255,0.08); padding:15px; border-radius:10px; border:1px solid #444; backdrop-filter: blur(5px); }}
    </style>
""", unsafe_allow_html=True)

# --- 5. LOGIQUE PRINCIPALE ---
df_users, df_acts = get_data()

# SIDEBAR
st.sidebar.title("🔐 Accès Fitness")
ACT_OPTS = ["Sédentaire", "Actif", "Sportif"]
ACT_VALS = [1.2, 1.55, 1.725]

if not st.session_state.user:
    menu = st.sidebar.selectbox("Menu", ["Connexion", "Inscription"])
    u_in = st.sidebar.text_input("Pseudo").strip().lower()
    p_in = st.sidebar.text_input("PIN", type="password")
    if st.sidebar.button("Valider"):
        if menu == "Connexion":
            if not df_users.empty and u_in in df_users['user'].values:
                if df_users[df_users['user']==u_in].iloc[0]['pin'] == hash_pin(p_in):
                    st.session_state.user = u_in; st.rerun()
                else: st.sidebar.error("Erreur PIN")
            else: st.sidebar.error("Inconnu")
        else:
            if not df_users.empty and u_in in df_users['user'].values: st.sidebar.error("Pris")
            elif len(p_in)==4:
                prof = {"dob":"1990-01-01", "sex":"Homme", "h":175, "act":"Actif", "w_init":70, "w_obj":65}
                if save_user(u_in, hash_pin(p_in), prof): st.session_state.user = u_in; st.rerun()
else:
    user = st.session_state.user
    if st.sidebar.button("Déconnexion"): st.session_state.user = None; st.rerun()
    
    user_row = df_users[df_users['user'] == user].iloc[0]
    prof = json.loads(user_row['json_data'])
    my_df = df_acts[df_acts['user'] == user].copy()
    
    w_curr = float(my_df.iloc[-1]['poids']) if not my_df.empty else float(prof.get('w_init', 70))
    total_cal = my_df['calories'].sum() if not my_df.empty else 0
    
    # CALCULS DNA GLOBAL
    dna_scores = {"Force": 0, "Endurance": 0, "Agilité": 0, "Mental": 0}
    if not my_df.empty:
        for _, row in my_df.iterrows():
            sport_dna = DNA_MAP.get(row['sport'], {"Force":1, "Endurance":1, "Agilité":1, "Mental":1})
            hours = row['minutes'] / 60
            for k in dna_scores: dna_scores[k] += sport_dna.get(k, 0) * hours
    
    # CALCULS ANATOMIE (7 JOURS)
    muscle_scores_7d = {}
    if not my_df.empty:
        seven_days_ago = pd.Timestamp.now() - pd.Timedelta(days=7)
        recent_df = my_df[my_df['date'] >= seven_days_ago]
        for _, row in recent_df.iterrows():
            impacts = MUSCLE_MAP.get(row['sport'], {"Cardio": 5})
            hours = row['minutes'] / 60
            for m, s in impacts.items():
                muscle_scores_7d[m] = muscle_scores_7d.get(m, 0) + (s * hours)

    # --- TABS ---
    t1, t2, t3, t4, t5, t6 = st.tabs(["🏠 Dashboard", "🩻 Anatomie", "📈 Graphiques", "➕ Séance", "⚙️ Gestion", "🏆 Classement"])

    with t1:
        st.markdown(f"<div class='quote-box'>✨ {get_motivational_quote()}</div>", unsafe_allow_html=True)
        
        # XP Bar
        lvl, pct, rem = get_level_progress(total_cal)
        st.markdown(f"### ⚡ Niveau {lvl}")
        st.progress(pct)
        st.caption(f"Plus que **{rem} kcal** pour le niveau suivant !")
        
        # KPIs
        cal_today = my_df[my_df['date'].dt.date == date.today()]['calories'].sum() if not my_df.empty else 0
        streak = 0 # (Code streak simplifié pour brièveté, reprendre l'ancien si besoin)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Aujourd'hui", f"{int(cal_today)} kcal")
        c2.metric("Total", f"{int(total_cal/1000)}k kcal")
        c3.metric("Poids", f"{w_curr} kg")
        c4.metric("Brûlé", f"{total_cal/7700:.1f} kg")

        st.divider()
        
        # DNA CHART
        col_dna, col_info = st.columns([1, 1])
        with col_dna:
            st.subheader("🧬 Ton ADN Sportif")
            if sum(dna_scores.values()) > 0:
                # Normalisation pour affichage (Max 100)
                max_val = max(dna_scores.values()) if max(dna_scores.values()) > 0 else 1
                data_dna = pd.DataFrame({
                    'Attribut': list(dna_scores.keys()),
                    'Valeur': [v/max_val*100 for v in dna_scores.values()]
                })
                fig_dna = px.line_polar(data_dna, r='Valeur', theta='Attribut', line_close=True)
                fig_dna.update_traces(fill='toself', line_color='#FF4B4B')
                fig_dna.update_layout(polar=dict(radialaxis=dict(visible=False)), paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
                st.plotly_chart(fig_dna, use_container_width=True)
            else:
                lottie_gym = load_lottieurl(LOTTIE_GYM)
                if lottie_gym: st_lottie(lottie_gym, height=200)
                else: st.info("Fais du sport pour révéler ton ADN !")

        with col_info:
            st.subheader("🌍 Voyage")
            km = total_cal / 60
            st.markdown(f"<div class='glass-box'><h3>🏃‍♂️ {int(km)} km</h3><p>Direction Marseille</p></div>", unsafe_allow_html=True)
            st.progress(min(km/1000, 1.0))
            st.info(f"Équivalent : **{get_food_equivalent(total_cal)}**")

    with t2: # --- ONGLE ANATOMIE (NOUVEAU) ---
        st.header("🩻 Anatomie (7 derniers jours)")
        st.caption("Ce schéma montre les muscles sollicités récemment. Il se met à jour automatiquement.")
        
        if muscle_scores_7d:
            # Création des données pour le Plotly Scatter
            x_vals, y_vals, sizes, colors, labels = [], [], [], [], []
            
            for muscle, score in muscle_scores_7d.items():
                if muscle in BODY_COORDS:
                    base_x, base_y = BODY_COORDS[muscle]
                    # Gestion de la symétrie (Bras/Jambes -> Gauche et Droite)
                    if muscle in ["Bras", "Jambes", "Mollets"]:
                        # Côté Droit
                        x_vals.append(base_x); y_vals.append(base_y)
                        sizes.append(score * 5 + 10); colors.append(score)
                        labels.append(f"{muscle} D")
                        # Côté Gauche (X inversé)
                        x_vals.append(-base_x); y_vals.append(base_y)
                        sizes.append(score * 5 + 10); colors.append(score)
                        labels.append(f"{muscle} G")
                    else:
                        x_vals.append(base_x); y_vals.append(base_y)
                        sizes.append(score * 5 + 15); colors.append(score)
                        labels.append(muscle)

            fig_body = go.Figure()
            
            # 1. Silhouette abstraite (Lignes)
            fig_body.add_trace(go.Scatter(
                x=[0, 0, 0, 0, -2.5, 2.5, 0, -1.2, 1.2],
                y=[6, 4, 2.5, 1, 3.5, 3.5, 1, 0.5, 0.5],
                mode='markers', marker=dict(size=1, color='rgba(255,255,255,0.2)'),
                hoverinfo='skip'
            ))
            
            # 2. Bulles musculaires
            fig_body.add_trace(go.Scatter(
                x=x_vals, y=y_vals,
                mode='markers+text',
                text=labels, textposition="middle center",
                marker=dict(
                    size=sizes,
                    color=colors,
                    colorscale='Reds',
                    showscale=True,
                    opacity=0.9,
                    line=dict(color='white', width=1)
                ),
                hovertemplate='%{text}: Score %{marker.color:.1f}<extra></extra>'
            ))
            
            fig_body.update_layout(
                height=500,
                xaxis=dict(range=[-4, 4], showgrid=False, zeroline=False, visible=False),
                yaxis=dict(range=[-2, 7], showgrid=False, zeroline=False, visible=False),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                showlegend=False
            )
            st.plotly_chart(fig_body, use_container_width=True)
            
            # Liste détaillée en dessous
            st.divider()
            cols = st.columns(3)
            sorted_m = sorted(muscle_scores_7d.items(), key=lambda x: x[1], reverse=True)
            for i, (m, s) in enumerate(sorted_m[:6]):
                cols[i%3].metric(m, f"{int(s)} pts")
                
        else:
            st.info("Aucune activité sur les 7 derniers jours. Fais une séance pour voir ton anatomie s'illuminer !")

    with t3:
        if not my_df.empty:
            c1, c2 = st.columns(2)
            c1.plotly_chart(px.line(my_df, x='date', y='poids', title="Poids"), use_container_width=True)
            c2.plotly_chart(px.bar(my_df, x='date', y='calories', title="Calories"), use_container_width=True)
            
            # Prédiction
            date_obj, msg = predict_success(my_df, w_curr, float(prof.get('w_obj', 65)))
            if date_obj: st.success(f"🎯 Objectif : {msg}")
            else: st.warning(msg)

    with t4:
        st.subheader("Ajouter une séance")
        with st.form("add_act"):
            c1, c2 = st.columns(2)
            d = c1.date_input("Date", date.today())
            t = c2.time_input("Heure", datetime.now().time())
            s = c1.selectbox("Sport", SPORTS_LIST)
            m = c2.number_input("Durée (min)", 1, 300, 45)
            w = st.number_input("Poids du jour", 0.0, 200.0, float(w_curr))
            
            if st.form_submit_button("Valider"):
                full_dt = datetime.combine(d, t)
                # Calcul simple MET basé sur DNA Force+Endurance pour approximation
                dna = DNA_MAP.get(s, {})
                intensity = (dna.get("Force", 5) + dna.get("Endurance", 5)) / 2
                kcal = (calculate_bmr(w, prof['h'], calculate_age(prof['dob']), prof['sex']) / 24) * (intensity/1.5) * (m/60)
                
                new_row = pd.DataFrame([{
                    "date": full_dt, "user": user, "sport": s, 
                    "minutes": m, "calories": round(kcal), "poids": float(w)
                }])
                
                if save_activity(new_row):
                    st.success(f"+{int(kcal)} kcal !")
                    anim = load_lottieurl(LOTTIE_SUCCESS)
                    if anim: st_lottie(anim, height=150)
                    time.sleep(1.5); st.rerun()

    with t5:
        st.subheader("Profil")
        with st.form("prof"):
            new_w_obj = st.number_input("Objectif Poids", 0.0, 200.0, float(prof.get('w_obj', 65)))
            if st.form_submit_button("MAJ"):
                prof['w_obj'] = new_w_obj
                save_user(user, user_row['pin'], prof)
                st.rerun()
        
        st.subheader("Historique")
        if not my_df.empty:
            edited = st.data_editor(my_df, use_container_width=True, num_rows="dynamic")
            if st.button("Sauvegarder Modifs"):
                update_history(edited)
                st.rerun()

    with t6:
        st.header("Classement Hebdo")
        if not df_acts.empty:
            now = pd.Timestamp.now()
            week_df = df_acts[df_acts['date'] >= (now - pd.Timedelta(days=7))]
            if not week_df.empty:
                top = week_df.groupby("user")['calories'].sum().sort_values(ascending=False)
                for i, (u, c) in enumerate(top.items()):
                    st.markdown(f"### {['🥇','🥈','🥉'][i] if i<3 else str(i+1)+'.'} {u} : {int(c)} kcal")
            else: st.info("Calme plat cette semaine.")
