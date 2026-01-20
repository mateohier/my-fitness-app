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
import uuid
from streamlit_lottie import st_lottie

# --- 1. CONFIGURATION & CONSTANTES ---
st.set_page_config(page_title="Fitness Gamified Pro", page_icon="🔥", layout="wide")

# URLs
LOTTIE_SUCCESS = "https://assets5.lottiefiles.com/packages/lf20_u4yrau.json"
BACKGROUND_URL = "https://raw.githubusercontent.com/mateohier/my-fitness-app/refs/heads/main/AAAAAAAAAAAAAAAA.png"

# --- CALENDRIER DES BOSS ---
BOSS_CALENDAR = {
    1: ("Yéti des Glaces", 50000, "https://raw.githubusercontent.com/mateohier/my-fitness-app/refs/heads/main/1.jpg"),
    2: ("Golem de Pierre", 60000, "https://raw.githubusercontent.com/mateohier/my-fitness-app/refs/heads/main/2.jpg"),
    3: ("Hydre des Marais", 70000, "https://raw.githubusercontent.com/mateohier/my-fitness-app/refs/heads/main/3.jpg"),
    4: ("Titan Colossal", 80000, "https://raw.githubusercontent.com/mateohier/my-fitness-app/refs/heads/main/4.jpg"),
    5: ("Reine des Enfers", 90000, "https://raw.githubusercontent.com/mateohier/my-fitness-app/refs/heads/main/5.jpg"),
    6: ("Dragon Solaire", 100000, "https://raw.githubusercontent.com/mateohier/my-fitness-app/refs/heads/main/6.jpg"),
    7: ("Kraken des Abysses", 110000, "https://raw.githubusercontent.com/mateohier/my-fitness-app/refs/heads/main/7.jpg"),
    8: ("Seigneur Volcanique", 120000, "https://raw.githubusercontent.com/mateohier/my-fitness-app/refs/heads/main/8.jpg"),
    9: ("Chevalier Noir", 130000, "https://raw.githubusercontent.com/mateohier/my-fitness-app/refs/heads/main/9.jpg"),
    10: ("Spectre d'Halloween", 140000, "https://raw.githubusercontent.com/mateohier/my-fitness-app/refs/heads/main/10.jpg"),
    11: ("Cyborg du Futur", 150000, "https://raw.githubusercontent.com/mateohier/my-fitness-app/refs/heads/main/11.jpg"),
    12: ("Père Fouettard Géant", 160000, "https://raw.githubusercontent.com/mateohier/my-fitness-app/refs/heads/main/12.jpg")
}

# --- MAPPINGS ---
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
    "Ski":         {"Force": 5, "Endurance": 7, "Agilité": 6, "Mental": 5},
    "Randonnée":   {"Force": 3, "Endurance": 6, "Agilité": 2, "Mental": 5}
}
SPORTS_LIST = sorted(list(DNA_MAP.keys()))

SPEED_MAP = {
    "Course": 10.0, "Vélo": 20.0, "Natation": 2.5, "Marche": 5.0, 
    "Randonnée": 4.0, "Ski": 15.0, "Football": 7.0, "Tennis": 3.0,
    "Musculation": 0.0, "Crossfit": 0.0, "Yoga": 0.0, "Pilates": 0.0,
    "Boxe": 0.0, "Danse": 0.0, "Escalade": 0.1, "Basket": 4.0
}

ACTIVITY_OPTS = ["Sédentaire (1.2)", "Légèrement actif (1.375)", "Actif (1.55)", "Très actif (1.725)"]

# --- 2. UTILITAIRES ---
def hash_pin(pin): return hashlib.sha256(str(pin).encode()).hexdigest()

def load_lottieurl(url):
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
    factor = 150 
    if total_cal == 0: return 1, 0.0, 100
    level = int((total_cal / factor) ** 0.5)
    if level == 0: level = 1
    cal_curr = factor * (level ** 2)
    cal_next = factor * ((level + 1) ** 2)
    pct = min(max((total_cal - cal_curr) / (cal_next - cal_curr), 0.0), 1.0)
    return level, pct, int(cal_next - total_cal)

def get_food_equivalent(calories):
    if calories < 100: return "une Pomme 🍎"
    if calories < 250: return "une Barre chocolatée 🍫"
    if calories < 400: return "un Cheeseburger 🍔"
    if calories < 600: return "un paquet de Frites 🍟"
    if calories < 900: return "une Pizza entière 🍕"
    if calories < 1500: return "un Menu Fast-Food XL 🥤"
    return "un Festin de Roi 🍗"

def check_achievements(df):
    badges = []
    if df.empty: return badges
    df = df.copy()
    df['hour'] = df['date'].dt.hour
    df['day'] = df['date'].dt.day_name()
    if len(df[df['hour'] < 8]) >= 3: badges.append(("🌅 Lève-tôt", "3 séances avant 8h"))
    if len(df[df['day'] == 'Sunday']) >= 4: badges.append(("⛪ Messe Sportive", "4 Dimanches actifs"))
    if df['minutes'].max() >= 120: badges.append(("🥵 Titan", "Séance > 2h"))
    if df['calories'].sum() >= 10000: badges.append(("🔥 Fournaise", "10k kcal brûlées"))
    return badges

def calculate_advanced_streaks(df_all, current_user):
    user_streak = 0
    df_user = df_all[df_all['user'] == current_user].copy()
    if not df_user.empty:
        user_dates = df_user['date'].dt.date.unique()
        user_dates.sort()
        if len(user_dates) > 0:
            last_date = user_dates[-1]
            if (date.today() - last_date).days <= 1:
                user_streak = 1
                sorted_dates_desc = sorted(user_dates, reverse=True)
                for i in range(len(sorted_dates_desc) - 1):
                    if (sorted_dates_desc[i] - sorted_dates_desc[i+1]).days == 1: user_streak += 1
                    else: break
            else: user_streak = 0

    team_streak = 0
    if not df_all.empty:
        df_all['year_week'] = df_all['date'].dt.strftime('%Y-%U')
        weekly_counts = df_all.groupby('year_week').size()
        weeks = sorted(weekly_counts.index)
        current_streak = 0
        for w in weeks:
            if weekly_counts[w] >= 3: current_streak += 1
            else: current_streak = 0
        team_streak = current_streak
    return user_streak, team_streak

# --- 3. GESTION DONNÉES ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        df_u = conn.read(worksheet="Profils", ttl=600)
        df_a = conn.read(worksheet="Activites", ttl=600)
        df_d = conn.read(worksheet="Defis", ttl=600)
        
        if df_u.empty: df_u = pd.DataFrame(columns=["user", "pin", "json_data"])
        if df_a.empty: df_a = pd.DataFrame(columns=["date", "user", "sport", "minutes", "calories", "poids"])
        if df_d.empty: df_d = pd.DataFrame(columns=["id", "titre", "type", "objectif", "sport_cible", "createur", "participants", "date_fin", "statut"])
            
        df_a['date'] = pd.to_datetime(df_a['date'], errors='coerce')
        df_a = df_a.dropna(subset=['date'])
        
        return df_u, df_a, df_d
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def save_activity(new_row):
    try:
        df = conn.read(worksheet="Activites", ttl=0)
        upd = pd.concat([df, new_row], ignore_index=True)
        upd['date'] = pd.to_datetime(upd['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
        conn.update(worksheet="Activites", data=upd)
        st.cache_data.clear()
        return True
    except: return False

def save_user(u, p, data):
    try:
        df = conn.read(worksheet="Profils", ttl=0)
        j = json.dumps(data)
        if not df.empty and u in df['user'].values: 
            df.loc[df['user'] == u, 'json_data'] = j
            df.loc[df['user'] == u, 'pin'] = p # Update PIN as well
        else: 
            df = pd.concat([df, pd.DataFrame([{"user": u, "pin": p, "json_data": j}])], ignore_index=True)
        conn.update(worksheet="Profils", data=df)
        st.cache_data.clear()
        return True
    except: return False

def delete_current_user():
    try:
        user = st.session_state.user
        df_u = conn.read(worksheet="Profils", ttl=0)
        df_a = conn.read(worksheet="Activites", ttl=0)
        df_d = conn.read(worksheet="Defis", ttl=0)
        
        df_u = df_u[df_u['user'] != user]
        df_a = df_a[df_a['user'] != user]
        
        def remove_participant(participants_str):
            parts = str(participants_str).split(',')
            if user in parts: parts.remove(user)
            return ",".join(parts)
            
        df_d['participants'] = df_d['participants'].apply(remove_participant)
        
        conn.update(worksheet="Profils", data=df_u)
        conn.update(worksheet="Activites", data=df_a)
        conn.update(worksheet="Defis", data=df_d)
        st.cache_data.clear()
        return True
    except Exception as e: return False

def create_challenge(titre, type_def, obj, sport_cible, fin):
    try:
        df = conn.read(worksheet="Defis", ttl=0)
        new = pd.DataFrame([{
            "id": str(uuid.uuid4()), "titre": titre, "type": type_def, 
            "objectif": float(obj), "sport_cible": sport_cible,
            "createur": st.session_state.user, "participants": st.session_state.user, 
            "date_fin": str(fin), "statut": "Actif"
        }])
        conn.update(worksheet="Defis", data=pd.concat([df, new], ignore_index=True))
        st.cache_data.clear()
        return True
    except: return False

def join_challenge(c_id):
    try:
        df = conn.read(worksheet="Defis", ttl=0)
        idx = df[df['id'] == c_id].index[0]
        parts = df.at[idx, 'participants'].split(',')
        if st.session_state.user not in parts:
            parts.append(st.session_state.user)
            df.at[idx, 'participants'] = ",".join(parts)
            conn.update(worksheet="Defis", data=df)
            st.cache_data.clear()
        return True
    except: return False

def delete_challenge(c_id):
    try:
        df = conn.read(worksheet="Defis", ttl=0)
        df = df[df['id'] != c_id]
        conn.update(worksheet="Defis", data=df)
        st.cache_data.clear()
        return True
    except: return False

# --- 4. CSS ---
if 'user' not in st.session_state: st.session_state.user = None

st.markdown(f"""
    <style>
    .stApp {{ background-image: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("{BACKGROUND_URL}"); background-size: cover; background-attachment: fixed; }}
    .stMetricValue {{ font-size: 1.5rem !important; color: #FF4B4B !important; }}
    div[data-testid="stSidebar"] {{ background-color: rgba(10, 10, 10, 0.95); }}
    .quote-box {{ padding: 10px; background: linear-gradient(90deg, #FF4B4B, #FF9068); border-radius: 8px; color: white; text-align: center; font-weight: bold; margin-bottom: 10px; }}
    .glass {{ background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid #333; }}
    .challenge-card {{ background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.0)); border-left: 5px solid #FF4B4B; padding: 15px; margin-bottom: 10px; border-radius: 5px; }}
    .boss-bar {{ width: 100%; background-color: #333; border-radius: 10px; overflow: hidden; height: 30px; margin-bottom: 10px; border: 1px solid #555; }}
    .boss-fill {{ height: 100%; background: linear-gradient(90deg, #FF4B4B, #FF0000); transition: width 0.5s; }}
    </style>
""", unsafe_allow_html=True)

# --- 5. LOGIQUE ---
df_u, df_a, df_d = get_data()

if not st.session_state.user:
    st.sidebar.title("🔥 Connexion")
    menu = st.sidebar.selectbox("Menu", ["Se connecter", "Créer un compte"])
    u_input = st.sidebar.text_input("Pseudo").strip().lower()
    p_input = st.sidebar.text_input("PIN (4 chiffres)", type="password")
    
    if menu == "Se connecter":
        if st.sidebar.button("Se connecter"):
            if not df_u.empty and u_input in df_u['user'].values:
                if df_u[df_u['user']==u_input].iloc[0]['pin'] == hash_pin(p_input):
                    st.session_state.user = u_input; st.rerun()
                else: st.sidebar.error("Mauvais PIN")
            else: st.sidebar.error("Utilisateur inconnu")
            
    elif menu == "Créer un compte":
        st.sidebar.markdown("### Profil")
        dob = st.sidebar.date_input("Naissance", value=date(1990,1,1))
        sex = st.sidebar.selectbox("Sexe", ["Homme", "Femme"])
        h = st.sidebar.number_input("Taille (cm)", 100, 250, 175)
        act = st.sidebar.selectbox("Activité", ACTIVITY_OPTS)
        w_init = st.sidebar.number_input("Poids actuel (kg)", 30.0, 200.0, 70.0)
        w_obj = st.sidebar.number_input("Objectif (kg)", 30.0, 200.0, 65.0)
        
        if st.sidebar.button("S'inscrire"):
            if not df_u.empty and u_input in df_u['user'].values: st.sidebar.error("Pseudo pris")
            elif len(p_input) == 4:
                prof = {"dob": str(dob), "sex": sex, "h": h, "act": act, "w_init": w_init, "w_obj": w_obj}
                if save_user(u_input, hash_pin(p_input), prof):
                    st.sidebar.success("Compte créé !"); time.sleep(1); st.rerun()
else:
    user = st.session_state.user
    st.sidebar.markdown(f"👤 **{user.capitalize()}**")
    if st.sidebar.button("Déconnexion"): st.session_state.user = None; st.rerun()
    
    row = df_u[df_u['user'] == user].iloc[0]
    prof = json.loads(row['json_data'])
    my_df = df_a[df_a['user'] == user].copy()
    w_curr = float(my_df.iloc[-1]['poids']) if not my_df.empty else float(prof.get('w_init', 70))
    total_cal = my_df['calories'].sum()
    
    streak_user, streak_team = calculate_advanced_streaks(df_a, user)
    
    # DNA
    dna = {"Force": 0, "Endurance": 0, "Agilité": 0, "Mental": 0}
    for _, r in my_df.iterrows():
        s_dna = DNA_MAP.get(r['sport'], {"Force":1, "Endurance":1})
        h = r['minutes'] / 60
        for k in dna: dna[k] += s_dna.get(k, 0) * h

    tabs = st.tabs(["🏠 Dashboard", "👹 Boss", "⚔️ Défis", "📈 Stats", "➕ Séance", "⚙️ Profil", "🏆 Top"])

    with tabs[0]: # DASHBOARD
        st.markdown(f"<div class='quote-box'>{random.choice(['La douleur est temporaire.', 'Tu es une machine.', 'Go hard or go home.'])}</div>", unsafe_allow_html=True)
        
        lvl, pct, rem = get_level_progress(total_cal)
        st.markdown(f"### ⚡ Niveau {lvl}")
        st.progress(pct)
        
        c1, c2, c3, c4 = st.columns(4)
        today_val = my_df[my_df['date'].dt.date == date.today()]['calories'].sum()
        c1.metric("Aujourd'hui", f"{int(today_val)} kcal")
        c2.metric("🔥 Série Perso", f"{streak_user} Jours")
        c3.metric("🛡️ Série Équipe", f"{streak_team} Sem.", "Obj: >3 act./sem")
        badges = check_achievements(my_df)
        c4.metric("Trophées", f"{len(badges)}")

        c_l, c_r = st.columns(2)
        with c_l:
            st.subheader("🧬 ADN")
            if sum(dna.values())>0:
                mx = max(dna.values())
                fig = px.line_polar(pd.DataFrame({'K':dna.keys(), 'V':[v/mx*100 for v in dna.values()]}), r='V', theta='K', line_close=True)
                fig.update_traces(fill='toself', line_color='#FF4B4B')
                fig.update_layout(polar=dict(radialaxis=dict(visible=False)), paper_bgcolor="rgba(0,0,0,0)", font_color="white")
                st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})
            else: st.info("Pas assez de données")
            
        with c_r:
            st.subheader("🌍 Voyage")
            km = total_cal / 60
            villes = [("Lille", 0), ("Paris", 225), ("Lyon", 690), ("Marseille", 1000)]
            dest, rest = "Marseille", 0
            for v, d in villes:
                if km < d: dest = v; rest = d - km; break
            
            st.markdown(f"<div class='glass'>🏃‍♂️ <b>{int(km)} km</b> parcourus<br>Cap sur {dest} ({int(rest)} km)</div>", unsafe_allow_html=True)
            st.progress(min(km/1000, 1.0))
            st.info(f"Tu as brûlé l'équivalent de : **{get_food_equivalent(total_cal)}**")

    with tabs[1]: # BOSS
        curr_month_num = datetime.now().month
        boss_name, boss_max_hp, boss_img = BOSS_CALENDAR.get(curr_month_num, ("Monstre", 200000, ""))
        st.header(f"👹 BOSS DU MOIS : {boss_name.upper()}")
        
        curr_month_str = datetime.now().strftime("%Y-%m")
        df_a['month'] = df_a['date'].dt.strftime("%Y-%m")
        df_month = df_a[df_a['month'] == curr_month_str]
        
        dmg = df_month['calories'].sum()
        pct_hp = max(0, (boss_max_hp - dmg) / boss_max_hp)
        
        c_img, c_stat = st.columns([1, 2])
        with c_img: st.image(boss_img, use_container_width=True)
        with c_stat:
            col = "#4CAF50" if pct_hp > 0.5 else ("#FF9800" if pct_hp > 0.2 else "#F44336")
            st.markdown(f"""<div style="margin-bottom:5px;color:white;font-weight:bold;">PV Restants : {int(boss_max_hp - dmg)} / {boss_max_hp}</div><div class="boss-bar"><div class="boss-fill" style="width: {pct_hp*100}%; background-color: {col};"></div></div>""", unsafe_allow_html=True)
            if pct_hp <= 0:
                st.balloons()
                st.success("🏆 LE BOSS EST VAINCU !")
            else: st.info(f"Il reste {int(pct_hp*100)}% de vie.")
            
            st.markdown("### ⚔️ Meilleurs Attaquants")
            if not df_month.empty:
                dps = df_month.groupby("user")['calories'].sum().sort_values(ascending=False).head(5)
                for i, (u, val) in enumerate(dps.items()): st.write(f"**{i+1}. {u}** : {int(val)} dégâts")

    with tabs[2]: # DEFIS
        st.header("⚔️ Salle des Défis")
        with st.expander("➕ Lancer un nouveau défi"):
            with st.form("new_def"):
                dt = st.text_input("Nom du défi", placeholder="Ex: Objectif Bikini")
                type_def = st.selectbox("Type de Cible", ["Calories (kcal)", "Durée (min)", "Distance (km)"])
                sport_target = st.selectbox("Sport concerné", ["Tous les sports"] + SPORTS_LIST)
                obj = st.number_input("Objectif à atteindre", 10.0, 50000.0, 500.0)
                fin = st.date_input("Date limite")
                if st.form_submit_button("Créer le défi"):
                    create_challenge(dt, type_def, obj, sport_target, fin)
                    st.success("Défi lancé !"); time.sleep(1); st.rerun()
        
        st.subheader("Défis en cours")
        if not df_d.empty:
            active = df_d[df_d['statut'] == 'Actif']
            for _, r in active.iterrows():
                parts = r['participants'].split(',')
                s_txt = "tous sports confondus" if r['sport_cible'] == "Tous les sports" else f"en {r['sport_cible']}"
                unit = "kcal" if "Calories" in r['type'] else ("km" if "Distance" in r['type'] else "min")
                
                c_df = df_a[(df_a['date'] <= r['date_fin']) & (df_a['user'].isin(parts))]
                if r['sport_cible'] != "Tous les sports": c_df = c_df[c_df['sport'] == r['sport_cible']]

                prog = pd.Series(dtype=float)
                if "Calories" in r['type']: prog = c_df.groupby('user')['calories'].sum()
                elif "Durée" in r['type']: prog = c_df.groupby('user')['minutes'].sum()
                elif "Distance" in r['type']:
                    c_df['km_est'] = c_df.apply(lambda row: (row['minutes']/60) * SPEED_MAP.get(row['sport'], 0), axis=1)
                    prog = c_df.groupby('user')['km_est'].sum()
                prog = prog.reindex(parts, fill_value=0)

                st.markdown(f"<div class='challenge-card'><h3>🏆 {r['titre']}</h3><p>Cible : <b>{int(r['objectif'])} {unit}</b> ({s_txt}) avant le {r['date_fin']}</p><p style='font-size:0.9em; color:#aaa'>Créé par {r['createur']}</p></div>", unsafe_allow_html=True)
                
                col_act, col_list = st.columns([1, 2])
                with col_act:
                    if user not in parts:
                        if st.button(f"Rejoindre l'équipe", key=r['id']): join_challenge(r['id']); st.rerun()
                    else: st.write("✅ Tu participes")
                    if r['createur'] == user:
                        if st.button("🗑️ Supprimer ce défi", key=f"del_{r['id']}"): delete_challenge(r['id']); st.success("Supprimé"); time.sleep(1); st.rerun()

                with col_list:
                    st.write("**Classement :**")
                    for u, val in prog.sort_values(ascending=False).items():
                        pct = min(val/float(r['objectif']), 1.0)
                        st.write(f"**{u}** : {int(val)} {unit} ({int(pct*100)}%)")
                        st.progress(pct)
                st.divider()
        else: st.info("Aucun défi.")

    with tabs[3]: # STATS
        if not my_df.empty:
            st.subheader("🏆 Tes Records Personnels")
            max_c = my_df['calories'].max()
            max_m = my_df['minutes'].max()
            fav = my_df['sport'].mode()[0] if not my_df['sport'].mode().empty else "-"
            k1, k2, k3 = st.columns(3)
            k1.metric("Record Kcal", f"{int(max_c)}")
            k2.metric("Séance Longue", f"{int(max_m)} min")
            k3.metric("Sport Favori", fav)
            st.divider()
            
            c_filter, _ = st.columns([1, 3])
            with c_filter: period = st.selectbox("Période", ["7 Derniers Jours", "Mois en cours", "3 Derniers Mois", "Tout"])
            
            df_chart = my_df.copy()
            now = pd.Timestamp.now()
            if period == "7 Derniers Jours": df_chart = df_chart[df_chart['date'] >= (now - pd.Timedelta(days=7))]
            elif period == "Mois en cours": df_chart = df_chart[df_chart['date'].dt.month == now.month]
            elif period == "3 Derniers Mois": df_chart = df_chart[df_chart['date'] >= (now - pd.Timedelta(days=90))]
            if period in ["Tout", "3 Derniers Mois"]:
                df_chart['week'] = df_chart['date'].dt.to_period('W').apply(lambda r: r.start_time)
                df_chart = df_chart.groupby('week').agg({'poids': 'mean', 'calories': 'sum'}).reset_index().rename(columns={'week': 'date'})

            c1, c2 = st.columns(2)
            c1.plotly_chart(px.line(df_chart, x='date', y='poids', title="Évolution Poids", markers=True), use_container_width=True, config={'staticPlot': True})
            c2.plotly_chart(px.bar(df_chart, x='date', y='calories', title="Calories Brûlées"), use_container_width=True, config={'staticPlot': True})
        else: st.write("Pas de données.")

    with tabs[4]: # SEANCE
        st.subheader("Ajouter une séance")
        with st.form("add"):
            c1, c2 = st.columns(2)
            d = c1.date_input("Date", date.today())
            t = c2.time_input("Heure", datetime.now().time())
            s = c1.selectbox("Sport", SPORTS_LIST)
            m = c2.number_input("Durée (min)", 1, 300, 45)
            w = st.number_input("Poids du jour", 0.0, 200.0, float(w_curr))
            if st.form_submit_button("Sauvegarder"):
                dt = datetime.combine(d, t)
                dna = DNA_MAP.get(s, {})
                intens = (dna.get("Force", 5) + dna.get("Endurance", 5))/2
                kcal = (calculate_bmr(w, prof['h'], 25, prof['sex'])/24) * (intens/1.5) * (m/60)
                if save_activity(pd.DataFrame([{"date": dt, "user": user, "sport": s, "minutes": m, "calories": int(kcal), "poids": w}])):
                    st.success(f"+{int(kcal)} kcal !"); st_lottie(load_lottieurl(LOTTIE_SUCCESS), height=100); time.sleep(1); st.rerun()

    with tabs[5]: # PROFIL FULL EDIT
        st.subheader("📝 Modifier mes informations")
        with st.form("prof_full"):
            c1, c2 = st.columns(2)
            new_dob = c1.date_input("Date de naissance", datetime.strptime(prof.get('dob', '1990-01-01'), "%Y-%m-%d"))
            new_sex = c2.selectbox("Sexe", ["Homme", "Femme"], index=0 if prof.get('sex') == "Homme" else 1)
            new_h = c1.number_input("Taille (cm)", 100, 250, int(prof.get('h', 175)))
            new_w_obj = c2.number_input("Objectif Poids (kg)", 40.0, 150.0, float(prof.get('w_obj', 65.0)))
            curr_act_idx = ACTIVITY_OPTS.index(prof.get('act', ACTIVITY_OPTS[1])) if prof.get('act') in ACTIVITY_OPTS else 1
            new_act = st.selectbox("Niveau d'activité", ACTIVITY_OPTS, index=curr_act_idx)
            new_pin = st.text_input("Nouveau PIN (Laisser vide pour ne pas changer)", type="password", max_chars=4)

            if st.form_submit_button("💾 Enregistrer les modifications"):
                prof.update({'dob': str(new_dob), 'sex': new_sex, 'h': int(new_h), 'w_obj': float(new_w_obj), 'act': new_act})
                pin_to_save = row['pin']
                if new_pin and len(new_pin) == 4: pin_to_save = hash_pin(new_pin); st.success("PIN modifié !")
                save_user(user, pin_to_save, prof)
                st.success("Profil mis à jour !"); time.sleep(1); st.rerun()
        
        st.subheader("Historique")
        if not my_df.empty:
            edi = st.data_editor(my_df, use_container_width=True, num_rows="dynamic")
            if st.button("Sauvegarder Modifs"):
                df_others = df_a[df_a['user'] != user]
                edi['date'] = pd.to_datetime(edi['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
                edi['poids'] = pd.to_numeric(edi['poids']); edi['calories'] = pd.to_numeric(edi['calories'])
                conn.update(worksheet="Activites", data=pd.concat([df_others, edi], ignore_index=True))
                st.cache_data.clear(); st.success("OK"); st.rerun()
        
        st.divider()
        st.error("⚠️ Zone de Danger")
        if st.button("Supprimer mon compte définitivement"): st.session_state['confirm_delete'] = True
        if st.session_state.get('confirm_delete'):
            st.warning("Irréversible. Confirmer ?")
            if st.button("OUI, Supprimer"):
                if delete_current_user(): st.session_state.user = None; st.success("Compte supprimé."); time.sleep(1); st.rerun()

    with tabs[6]: # TOP
        if not df_a.empty:
            w_df = df_a[df_a['date'] >= (pd.Timestamp.now() - pd.Timedelta(days=7))]
            top = w_df.groupby("user")['calories'].sum().sort_values(ascending=False)
            for i, (u, c) in enumerate(top.items()): st.markdown(f"### {i+1}. {u} - {int(c)} kcal")
