import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import date, datetime
import hashlib
import time
import json

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

# --- 3. GESTION DONNÉES (GOOGLE SHEETS) ---
# Connexion unique et optimisée
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    """Charge les deux tables : Profils et Activités"""
    try:
        df_users = conn.read(worksheet="Profils", ttl=0)
        df_acts = conn.read(worksheet="Activites", ttl=0)
        
        if df_users.empty: 
            df_users = pd.DataFrame(columns=["user", "pin", "json_data"])
        if df_acts.empty: 
            df_acts = pd.DataFrame(columns=["date", "user", "sport", "minutes", "calories", "poids"])
            
        df_acts['date'] = pd.to_datetime(df_acts['date'], errors='coerce')
        df_acts = df_acts.dropna(subset=['date'])
        
        return df_users, df_acts
    except Exception as e:
        st.error(f"Erreur connexion Google Sheets: {e}")
        return pd.DataFrame(), pd.DataFrame()

def save_activity(new_row):
    """Ajoute une ligne dans l'onglet Activites"""
    try:
        _, df_acts = get_data()
        updated_df = pd.concat([df_acts, new_row], ignore_index=True)
        updated_df['date'] = updated_df['date'].dt.strftime('%Y-%m-%d')
        conn.update(worksheet="Activites", data=updated_df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erreur sauvegarde: {e}")
        return False

def save_user(username, pin_hash, profile_data):
    """Crée ou met à jour un utilisateur dans l'onglet Profils"""
    try:
        df_users, _ = get_data()
        json_str = json.dumps(profile_data)
        
        if username in df_users['user'].values:
            df_users.loc[df_users['user'] == username, 'json_data'] = json_str
        else:
            new_user = pd.DataFrame([{"user": username, "pin": pin_hash, "json_data": json_str}])
            df_users = pd.concat([df_users, new_user], ignore_index=True)
            
        conn.update(worksheet="Profils", data=df_users)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erreur profil: {e}")
        return False

def update_history(df_edited):
    """Met à jour tout l'historique"""
    try:
        _, df_all_acts = get_data()
        current_user = st.session_state.user
        df_others = df_all_acts[df_all_acts['user'] != current_user]
        df_edited['user'] = current_user
        
        df_final = pd.concat([df_others, df_edited], ignore_index=True)
        df_final['date'] = pd.to_datetime(df_final['date']).dt.strftime('%Y-%m-%d')
        
        conn.update(worksheet="Activites", data=df_final)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erreur update historique: {e}")
        return False

# --- 4. CSS & STATE ---
if 'user' not in st.session_state: st.session_state.user = None

st.markdown("""
    <style>
    .stMetricValue { font-size: 2rem !important; }
    div[data-testid="stSidebar"] { background-color: rgba(20, 20, 20, 0.95); }
    .podium-box { background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #444; }
    </style>
""", unsafe_allow_html=True)

# --- 5. LOGIQUE PRINCIPALE ---
df_users, df_acts = get_data()

# --- SIDEBAR ---
st.sidebar.title("🔐 Accès Fitness")
ACTIVITY_OPTS = ["Sédentaire (1.2)", "Légèrement actif (1.375)", "Actif (1.55)", "Très actif (1.725)"]
ACT_MAP = {k: v for k, v in zip(ACTIVITY_OPTS, [1.2, 1.375, 1.55, 1.725])}

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
        # CORRECTION 1 : Bornes explicites pour l'inscription
        dob = st.sidebar.date_input(
            "Naissance", 
            value=date(1990,1,1), 
            min_value=date(1900,1,1), 
            max_value=date.today()
        )
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
        
    # Chargement Données Utilisateur
    user_row = df_users[df_users['user'] == user].iloc[0]
    prof = json.loads(user_row['json_data'])
    
    # Filtrage des activités
    my_df = df_acts[df_acts['user'] == user].copy()
    if not my_df.empty:
        my_df = my_df.sort_values('date')
        last_w = my_df.iloc[-1]['poids']
    else:
        last_w = prof.get('w_init', 70.0)

    # Calculs KPI
    age = calculate_age(prof.get('dob', '1990-01-01'))
    total_cal = my_df['calories'].sum() if not my_df.empty else 0
    rank, next_lvl, _ = get_rank(total_cal)
    
    # Calcul Streak
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

    # Onglets
    t1, t2, t3, t4, t5 = st.tabs(["🏠 Dashboard", "📈 Graphiques", "➕ Séance", "⚙️ Gestion", "🏆 Leaderboard"])
    
    with t1:
        st.title(f"Bonjour {user.capitalize()}")
        st.caption(f"{prof['sex']} | {age} ans | {prof['h']}cm | {prof['act']}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔥 Série", f"{streak} Jours")
        loss = prof['w_init'] - last_w
        c2.metric("⚖️ Perte", f"{loss:.1f} kg", delta_color="normal" if loss > 0 else "off")
        c3.metric("⚡ Total", f"{int(total_cal):,} kcal")
        c4.metric("🏅 Rang", rank)
        st.progress(min(total_cal / next_lvl, 1.0))

    with t2:
        if not my_df.empty:
            c1, c2 = st.columns(2)
            fig1 = px.line(my_df, x='date', y='poids', title="Poids")
            fig1.add_hline(y=prof['w_obj'], line_dash="dash", line_color="green")
            c1.plotly_chart(fig1, use_container_width=True)
            
            fig2 = px.bar(my_df, x='date', y='calories', title="Calories")
            c2.plotly_chart(fig2, use_container_width=True)
            
            fig3 = px.pie(my_df, values='minutes', names='sport', hole=0.4, title="Sports")
            st.plotly_chart(fig3, use_container_width=True)
        else: st.info("Pas encore de données.")

    with t3:
        bmr = calculate_bmr(last_w, prof['h'], age, prof['sex'])
        tdee = bmr * ACT_MAP.get(prof['act'], 1.2)
        st.info(f"💡 Calories journalières (Maintenance) : **{int(tdee)} kcal**")
        
        with st.form("add"):
            c1, c2 = st.columns(2)
            d = c1.date_input("Date", date.today())
            s = c2.selectbox("Sport", ["Musculation", "Course", "Vélo", "Natation", "Crossfit", "Marche", "Fitness"])
            w = c1.number_input("Poids (kg)", 0.0, 200.0, float(last_w))
            m = c2.number_input("Durée (min)", 1, 300, 45)
            
            if st.form_submit_button("Sauvegarder"):
                met = {"Course": 10, "Vélo": 7, "Natation": 8, "Musculation": 4, "Crossfit": 8, "Marche": 3.5, "Fitness": 6}
                cal_sport = (calculate_bmr(w, prof['h'], age, prof['sex']) / 24) * met.get(s, 5) * (m/60)
                
                new_act = pd.DataFrame([{
                    "date": pd.to_datetime(d), "user": user, "sport": s, 
                    "minutes": m, "calories": round(cal_sport), "poids": w
                }])
                
                with st.spinner("Sauvegarde..."):
                    if save_activity(new_act):
                        st.success(f"+{int(cal_sport)} kcal !")
                        time.sleep(1)
                        st.rerun()

    with t4:
        st.subheader("Profil")
        with st.form("edit_prof"):
            col1, col2 = st.columns(2)
            # CORRECTION 2 : Bornes explicites pour la modification aussi !
            new_dob = col1.date_input(
                "Naissance", 
                value=datetime.strptime(prof['dob'], "%Y-%m-%d"),
                min_value=date(1900,1,1),
                max_value=date.today()
            )
            new_act = col2.selectbox("Activité", ACTIVITY_OPTS, index=ACTIVITY_OPTS.index(prof['act']))
            new_obj = st.number_input("Objectif", value=float(prof['w_obj']))
            
            if st.form_submit_button("Mettre à jour"):
                prof.update({"dob": str(new_dob), "act": new_act, "w_obj": new_obj})
                if save_user(user, user_row['pin'], prof):
                    st.success("Profil mis à jour")
                    st.rerun()

        st.subheader("Historique")
        if not my_df.empty:
            edited = st.data_editor(
                my_df[['date', 'sport', 'minutes', 'calories', 'poids']], 
                num_rows="dynamic", use_container_width=True
            )
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
