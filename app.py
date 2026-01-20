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
from PIL import Image
import io
import base64

# --- 1. CONFIGURATION & CONSTANTES ---
st.set_page_config(page_title="FollowFit", page_icon="✨", layout="wide")

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

# --- MAPPINGS (9 COMPETENCES) ---
DNA_MAP = {
    "Musculation": {"Force": 10, "Endurance": 4, "Vitesse": 3, "Agilité": 2, "Souplesse": 3, "Explosivité": 6, "Mental": 7, "Récupération": 5, "Concentration": 8},
    "Crossfit":    {"Force": 9, "Endurance": 8, "Vitesse": 6, "Agilité": 6, "Souplesse": 5, "Explosivité": 9, "Mental": 9, "Récupération": 6, "Concentration": 7},
    "Course":      {"Force": 3, "Endurance": 10, "Vitesse": 7, "Agilité": 3, "Souplesse": 3, "Explosivité": 4, "Mental": 9, "Récupération": 8, "Concentration": 6},
    "Vélo":        {"Force": 5, "Endurance": 10, "Vitesse": 6, "Agilité": 3, "Souplesse": 2, "Explosivité": 4, "Mental": 7, "Récupération": 9, "Concentration": 5},
    "Natation":    {"Force": 6, "Endurance": 9, "Vitesse": 5, "Agilité": 5, "Souplesse": 6, "Explosivité": 5, "Mental": 8, "Récupération": 10, "Concentration": 7},
    "Yoga":        {"Force": 4, "Endurance": 5, "Vitesse": 1, "Agilité": 6, "Souplesse": 10, "Explosivité": 1, "Mental": 9, "Récupération": 10, "Concentration": 10},
    "Boxe":        {"Force": 7, "Endurance": 9, "Vitesse": 8, "Agilité": 9, "Souplesse": 6, "Explosivité": 9, "Mental": 9, "Récupération": 5, "Concentration": 9},
    "Escalade":    {"Force": 8, "Endurance": 6, "Vitesse": 3, "Agilité": 8, "Souplesse": 9, "Explosivité": 6, "Mental": 10, "Récupération": 4, "Concentration": 10},
    "Tennis":      {"Force": 5, "Endurance": 7, "Vitesse": 8, "Agilité": 9, "Souplesse": 4, "Explosivité": 7, "Mental": 7, "Récupération": 5, "Concentration": 9},
    "Football":    {"Force": 5, "Endurance": 8, "Vitesse": 8, "Agilité": 7, "Souplesse": 4, "Explosivité": 7, "Mental": 7, "Récupération": 5, "Concentration": 7},
    "Basket":      {"Force": 5, "Endurance": 7, "Vitesse": 8, "Agilité": 8, "Souplesse": 5, "Explosivité": 8, "Mental": 6, "Récupération": 5, "Concentration": 7},
    "Marche":      {"Force": 2, "Endurance": 5, "Vitesse": 2, "Agilité": 2, "Souplesse": 2, "Explosivité": 1, "Mental": 4, "Récupération": 10, "Concentration": 3},
    "Danse":       {"Force": 4, "Endurance": 6, "Vitesse": 5, "Agilité": 10, "Souplesse": 9, "Explosivité": 4, "Mental": 6, "Récupération": 6, "Concentration": 8},
    "Pilates":     {"Force": 5, "Endurance": 4, "Vitesse": 1, "Agilité": 6, "Souplesse": 9, "Explosivité": 2, "Mental": 8, "Récupération": 9, "Concentration": 9},
    "Ski":         {"Force": 6, "Endurance": 7, "Vitesse": 8, "Agilité": 7, "Souplesse": 3, "Explosivité": 5, "Mental": 6, "Récupération": 4, "Concentration": 8},
    "Randonnée":   {"Force": 4, "Endurance": 9, "Vitesse": 2, "Agilité": 3, "Souplesse": 2, "Explosivité": 2, "Mental": 7, "Récupération": 8, "Concentration": 5},
    "Judo":        {"Force": 9, "Endurance": 7, "Vitesse": 5, "Agilité": 7, "Souplesse": 6, "Explosivité": 8, "Mental": 9, "Récupération": 4, "Concentration": 9},
    "Karaté":      {"Force": 7, "Endurance": 7, "Vitesse": 8, "Agilité": 8, "Souplesse": 7, "Explosivité": 9, "Mental": 9, "Récupération": 5, "Concentration": 9},
    "Badminton":   {"Force": 3, "Endurance": 8, "Vitesse": 10, "Agilité": 10, "Souplesse": 5, "Explosivité": 8, "Mental": 7, "Récupération": 5, "Concentration": 8},
    "Rameur":      {"Force": 7, "Endurance": 9, "Vitesse": 5, "Agilité": 3, "Souplesse": 3, "Explosivité": 6, "Mental": 8, "Récupération": 6, "Concentration": 6},
    "Elliptique":  {"Force": 4, "Endurance": 8, "Vitesse": 4, "Agilité": 2, "Souplesse": 2, "Explosivité": 2, "Mental": 5, "Récupération": 7, "Concentration": 4},
    "Gymnastique": {"Force": 9, "Endurance": 6, "Vitesse": 5, "Agilité": 10, "Souplesse": 10, "Explosivité": 9, "Mental": 9, "Récupération": 4, "Concentration": 10},
    "Volley":      {"Force": 6, "Endurance": 6, "Vitesse": 6, "Agilité": 8, "Souplesse": 5, "Explosivité": 9, "Mental": 7, "Récupération": 5, "Concentration": 7}
}
SPORTS_LIST = sorted(list(DNA_MAP.keys()))

SPEED_MAP = {
    "Course": 10.0, "Vélo": 20.0, "Natation": 2.5, "Marche": 5.0, 
    "Randonnée": 4.0, "Ski": 15.0, "Football": 7.0, "Tennis": 3.0,
    "Musculation": 0.0, "Crossfit": 0.0, "Yoga": 0.0, "Pilates": 0.0,
    "Boxe": 0.0, "Danse": 0.0, "Escalade": 0.1, "Basket": 4.0,
    "Judo": 0.0, "Karaté": 0.0, "Gymnastique": 0.0, "Volley": 3.0,
    "Badminton": 4.0, "Rameur": 8.0, "Elliptique": 8.0
}

EPOC_MAP = {
    "Crossfit": 0.15, "Musculation": 0.10, "Boxe": 0.12, "Rugby": 0.12, "Judo": 0.12, "Karaté": 0.12,
    "Course": 0.07, "Vélo": 0.05, "Natation": 0.06, "Tennis": 0.05, "Football": 0.07, "Basket": 0.07,
    "Rameur": 0.08, "Elliptique": 0.05, "Badminton": 0.05, "Volley": 0.04,
    "Ski": 0.06, "Escalade": 0.05, "Danse": 0.04, "Gymnastique": 0.06,
    "Marche": 0.01, "Yoga": 0.02, "Pilates": 0.02, "Randonnée": 0.03
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
                dates_desc = sorted(user_dates, reverse=True)
                for i in range(len(dates_desc) - 1):
                    if (dates_desc[i] - dates_desc[i+1]).days == 1: user_streak += 1
                    else: break
            else: user_streak = 0

    team_streak = 0
    if not df_all.empty:
        today = date.today()
        check_date = today
        while True:
            day_minus_1 = check_date - timedelta(days=1)
            mask = (df_all['date'].dt.date == check_date) | (df_all['date'].dt.date == day_minus_1)
            unique_active_users = df_all[mask]['user'].nunique()
            if unique_active_users >= 3:
                team_streak += 1
                check_date -= timedelta(days=1)
            else:
                if check_date == today and team_streak == 0:
                    check_date -= timedelta(days=1)
                    continue
                else: break
    return user_streak, team_streak

def process_avatar(image_file):
    if image_file is None: return None
    try:
        img = Image.open(image_file).convert('RGB')
        img.thumbnail((150, 150))
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=70)
        return f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode()}"
    except: return None

def process_post_image(image_file):
    """Pour les posts, on garde un peu plus de qualité mais compressé"""
    if image_file is None: return None
    try:
        img = Image.open(image_file).convert('RGB')
        img.thumbnail((400, 400)) # Taille moyenne pour feed
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=60) # Compression
        return f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode()}"
    except: return None

# --- 3. GESTION DONNÉES ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        df_u = conn.read(worksheet="Profils", ttl=600)
        df_a = conn.read(worksheet="Activites", ttl=600)
        df_d = conn.read(worksheet="Defis", ttl=600)
        try: df_p = conn.read(worksheet="Posts", ttl=600)
        except: df_p = pd.DataFrame(columns=["id", "user", "date", "image", "comment", "seen_by"])
        
        try: df_s = conn.read(worksheet="Podometre", ttl=600)
        except: df_s = pd.DataFrame(columns=["date", "user", "steps"])
        
        if df_u.empty: df_u = pd.DataFrame(columns=["user", "pin", "json_data"])
        if df_a.empty: df_a = pd.DataFrame(columns=["date", "user", "sport", "minutes", "calories", "poids"])
        if df_d.empty: df_d = pd.DataFrame(columns=["id", "titre", "type", "objectif", "sport_cible", "createur", "participants", "date_fin", "statut"])
        if df_p.empty: df_p = pd.DataFrame(columns=["id", "user", "date", "image", "comment", "seen_by"])
        if df_s.empty: df_s = pd.DataFrame(columns=["date", "user", "steps"])
            
        df_a['date'] = pd.to_datetime(df_a['date'], errors='coerce')
        df_a = df_a.dropna(subset=['date'])
        df_p['date'] = pd.to_datetime(df_p['date'], errors='coerce')
        df_s['date'] = pd.to_datetime(df_s['date'], errors='coerce')
        
        return df_u, df_a, df_d, df_p, df_s
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def save_activity(new_row):
    try:
        df = conn.read(worksheet="Activites", ttl=0)
        upd = pd.concat([df, new_row], ignore_index=True)
        upd['date'] = pd.to_datetime(upd['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
        conn.update(worksheet="Activites", data=upd)
        st.cache_data.clear(); return True
    except: return False

def save_post(image_b64, comment):
    try:
        df = conn.read(worksheet="Posts", ttl=0)
        new = pd.DataFrame([{
            "id": str(uuid.uuid4()), "user": st.session_state.user, 
            "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "image": image_b64, "comment": comment, "seen_by": st.session_state.user
        }])
        conn.update(worksheet="Posts", data=pd.concat([df, new], ignore_index=True))
        st.cache_data.clear(); return True
    except: return False

def save_steps(user, steps):
    """Sauvegarde les pas manuels dans Podometre"""
    try:
        df = conn.read(worksheet="Podometre", ttl=0)
        new = pd.DataFrame([{
            "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "user": user, "steps": steps
        }])
        conn.update(worksheet="Podometre", data=pd.concat([df, new], ignore_index=True))
        st.cache_data.clear(); return True
    except: return False

def clean_old_posts(df_p):
    """Supprime les posts > 7 jours"""
    try:
        if df_p.empty: return
        now = datetime.now()
        df_p['date'] = pd.to_datetime(df_p['date'])
        # Garder uniquement les posts < 7 jours
        new_df = df_p[df_p['date'] >= (now - timedelta(days=7))]
        if len(new_df) < len(df_p):
            new_df['date'] = new_df['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
            conn.update(worksheet="Posts", data=new_df)
            st.cache_data.clear()
    except: pass

def mark_post_seen(post_id, current_user):
    try:
        df = conn.read(worksheet="Posts", ttl=0)
        idx = df[df['id'] == post_id].index[0]
        viewers = str(df.at[idx, 'seen_by']).split(',')
        if current_user not in viewers:
            viewers.append(current_user)
            df.at[idx, 'seen_by'] = ",".join(viewers)
            conn.update(worksheet="Posts", data=df)
            st.cache_data.clear()
    except: pass

def save_user(u, p, data):
    try:
        df = conn.read(worksheet="Profils", ttl=0)
        j = json.dumps(data)
        if not df.empty and u in df['user'].values: 
            df.loc[df['user'] == u, 'json_data'] = j; df.loc[df['user'] == u, 'pin'] = p
        else: 
            df = pd.concat([df, pd.DataFrame([{"user": u, "pin": p, "json_data": j}])], ignore_index=True)
        conn.update(worksheet="Profils", data=df)
        st.cache_data.clear(); return True
    except: return False

def change_username(old_u, new_u):
    """Change le nom d'utilisateur partout (Cascade)"""
    try:
        df_u = conn.read(worksheet="Profils", ttl=0)
        if new_u in df_u['user'].values: return "Ce pseudo existe déjà"
        
        df_a = conn.read(worksheet="Activites", ttl=0)
        df_d = conn.read(worksheet="Defis", ttl=0)
        df_p = conn.read(worksheet="Posts", ttl=0)
        df_s = conn.read(worksheet="Podometre", ttl=0)
        
        df_u.loc[df_u['user'] == old_u, 'user'] = new_u
        if not df_a.empty: df_a.loc[df_a['user'] == old_u, 'user'] = new_u
        if not df_s.empty: df_s.loc[df_s['user'] == old_u, 'user'] = new_u
        if not df_p.empty:
            df_p.loc[df_p['user'] == old_u, 'user'] = new_u
            def upd_csv(txt): return ",".join([new_u if x==old_u else x for x in str(txt).split(',')])
            df_p['seen_by'] = df_p['seen_by'].apply(upd_csv)
        if not df_d.empty:
            df_d.loc[df_d['createur'] == old_u, 'createur'] = new_u
            def upd_csv_d(txt): return ",".join([new_u if x==old_u else x for x in str(txt).split(',')])
            df_d['participants'] = df_d['participants'].apply(upd_csv_d)
            
        conn.update(worksheet="Profils", data=df_u)
        conn.update(worksheet="Activites", data=df_a)
        conn.update(worksheet="Defis", data=df_d)
        conn.update(worksheet="Posts", data=df_p)
        conn.update(worksheet="Podometre", data=df_s)
        st.cache_data.clear()
        return "OK"
    except Exception as e: return str(e)

def delete_current_user():
    try:
        user = st.session_state.user
        df_u = conn.read(worksheet="Profils", ttl=0); df_a = conn.read(worksheet="Activites", ttl=0); df_d = conn.read(worksheet="Defis", ttl=0)
        df_u = df_u[df_u['user'] != user]; df_a = df_a[df_a['user'] != user]
        def remove_p(p_str): parts = str(p_str).split(','); return ",".join([p for p in parts if p != user])
        df_d['participants'] = df_d['participants'].apply(remove_p)
        conn.update(worksheet="Profils", data=df_u); conn.update(worksheet="Activites", data=df_a); conn.update(worksheet="Defis", data=df_d)
        st.cache_data.clear(); return True
    except: return False

def create_challenge(titre, type_def, obj, sport_cible, fin):
    try:
        df = conn.read(worksheet="Defis", ttl=0)
        new = pd.DataFrame([{
            "id": str(uuid.uuid4()), "titre": titre, "type": type_def, "objectif": float(obj), 
            "sport_cible": sport_cible, "createur": st.session_state.user, 
            "participants": st.session_state.user, "date_fin": str(fin), "statut": "Actif"
        }])
        conn.update(worksheet="Defis", data=pd.concat([df, new], ignore_index=True))
        st.cache_data.clear(); return True
    except: return False

def join_challenge(c_id):
    try:
        df = conn.read(worksheet="Defis", ttl=0)
        idx = df[df['id'] == c_id].index[0]
        parts = df.at[idx, 'participants'].split(',')
        if st.session_state.user not in parts:
            parts.append(st.session_state.user)
            df.at[idx, 'participants'] = ",".join(parts)
            conn.update(worksheet="Defis", data=df); st.cache_data.clear()
        return True
    except: return False

def delete_challenge(c_id):
    try:
        df = conn.read(worksheet="Defis", ttl=0); df = df[df['id'] != c_id]
        conn.update(worksheet="Defis", data=df); st.cache_data.clear(); return True
    except: return False

def get_user_badge(username, df_u):
    try:
        row = df_u[df_u['user'] == username].iloc[0]
        p_data = json.loads(row['json_data'])
        avatar = p_data.get('avatar', "")
        if not avatar: avatar = f"https://api.dicebear.com/7.x/adventurer/svg?seed={username}"
    except: avatar = f"https://api.dicebear.com/7.x/adventurer/svg?seed={username}"
    return f"""<span style='display:inline-flex;align-items:center;border:1px solid rgba(255,255,255,0.2);border-radius:20px;padding:2px 10px;background:rgba(0,0,0,0.3);margin-right:5px;'><img src='{avatar}' style='width:25px;height:25px;border-radius:50%;margin-right:8px;object-fit:cover;background:white;'><span style='font-weight:bold;color:white;'>{username.capitalize()}</span></span>"""

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
    .celeb-box {{ background-color: rgba(255, 215, 0, 0.15); border: 1px solid #FFD700; padding: 15px; border-radius: 10px; text-align: center; margin-top: 10px; }}
    .stat-card {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 15px; text-align: center; flex: 1; min-width: 150px; }}
    .stat-val {{ font-size: 1.8em; font-weight: bold; color: #FF4B4B; }}
    .stat-label {{ font-size: 0.9em; opacity: 0.8; margin-top: 5px; }}
    .post-card {{ background: rgba(0,0,0,0.4); border-radius: 10px; padding: 15px; margin-bottom: 20px; border: 1px solid #444; }}
    </style>
""", unsafe_allow_html=True)

# --- 5. LOGIQUE ---
df_u, df_a, df_d, df_p, df_s = get_data()
clean_old_posts(df_p) # Nettoyage auto

if not st.session_state.user:
    st.title("✨ FollowFit")
    st.markdown("### L'aventure sportive commence ici.")
    st.info("👈 **C'est parti ! Ouvre le menu en haut à gauche pour te connecter ou t'inscrire.**")
    st.divider()
    with st.expander("💌 Le mot du Développeur", expanded=True):
        st.markdown("Salut la famille et les amis ! 👋 Ici, on se motive ensemble. Battez mes records ! 😉")
    st.sidebar.title("🔥 Connexion")
    menu = st.sidebar.selectbox("Menu", ["Se connecter", "Créer un compte"])
    u_input = st.sidebar.text_input("Pseudo").strip().lower()
    p_input = st.sidebar.text_input("PIN (4 chiffres)", type="password")
    
    if menu == "Se connecter":
        if st.sidebar.button("Se connecter"):
            if not df_u.empty and u_input in df_u['user'].values:
                if df_u[df_u['user']==u_input].iloc[0]['pin'] == hash_pin(p_input): st.session_state.user = u_input; st.rerun()
                else: st.sidebar.error("Mauvais PIN")
            else: st.sidebar.error("Utilisateur inconnu")
    elif menu == "Créer un compte":
        st.sidebar.markdown("### Profil")
        dob = st.sidebar.date_input("Naissance", value=date(2000,1,1), min_value=date(1900,1,1), max_value=date.today())
        sex = st.sidebar.selectbox("Sexe", ["Homme", "Femme"])
        h = st.sidebar.number_input("Taille (cm)", 100, 250, 175)
        act = st.sidebar.selectbox("Activité", ACTIVITY_OPTS)
        w_init = st.sidebar.number_input("Poids actuel (kg)", 30.0, 200.0, 70.0)
        w_obj = st.sidebar.number_input("Objectif (kg)", 30.0, 200.0, 65.0)
        if st.sidebar.button("S'inscrire"):
            if not df_u.empty and u_input in df_u['user'].values: st.sidebar.error("Pseudo pris")
            elif len(p_input) == 4:
                prof = {"dob": str(dob), "sex": sex, "h": h, "act": act, "w_init": w_init, "w_obj": w_obj}
                if save_user(u_input, hash_pin(p_input), prof): st.sidebar.success("Compte créé !"); time.sleep(1); st.rerun()
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
    
    DNA_KEYS = ["Force", "Endurance", "Vitesse", "Agilité", "Souplesse", "Explosivité", "Mental", "Récupération", "Concentration"]
    dna = {k: 0 for k in DNA_KEYS}
    for _, r in my_df.iterrows():
        s_dna = DNA_MAP.get(r['sport'], {})
        h = r['minutes'] / 60
        for k in DNA_KEYS: dna[k] += s_dna.get(k, 1) * h

    tabs = st.tabs(["🏠 Tableau de Bord", "📸 Partage", "➕ Séance", "👹 Boss", "⚔️ Défis", "📈 Statistiques", "🏆 Classement", "⚙️ Profil"])

    with tabs[0]: # DASHBOARD
        st.markdown(f"""<div style="display:flex;align-items:center;font-size:24px;font-weight:bold;margin-bottom:20px;">👋 Bienvenue &nbsp; {get_user_badge(user, df_u)}</div>""", unsafe_allow_html=True)
        st.markdown(f"<div class='quote-box'>{random.choice(['La douleur est temporaire.', 'Tu es une machine.', 'Go hard or go home.'])}</div>", unsafe_allow_html=True)
        lvl, pct, rem = get_level_progress(total_cal)
        st.markdown(f"### ⚡ Niveau {lvl}"); st.progress(pct); st.caption(f"Objectif Niveau {lvl+1} : Encore **{rem} kcal** à brûler ! 🔥")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Aujourd'hui", f"{int(my_df[my_df['date'].dt.date == date.today()]['calories'].sum())} kcal")
        
        # Récupération des pas automatiques (IFTTT) + Ajout manuel possible
        auto_steps = 0
        if not df_s.empty:
            today_s = df_s[(df_s['user'] == user) & (df_s['date'].dt.date == date.today())]
            if not today_s.empty: auto_steps = int(today_s['steps'].sum())
        
        with c2:
            st.metric("Pas (Auto)", f"{auto_steps}")
            with st.popover("➕ Ajouter pas manuels"):
                add_s = st.number_input("Nombre de pas", 0, 50000, 0)
                if st.button("Valider"): 
                    save_steps(user, add_s); st.success("Ajouté"); st.rerun()

        c3.metric("🔥 Série Perso", f"{streak_user} Jours")
        c4.metric("🏆 Trophées", f"{len(check_achievements(my_df))}")
        
        if not df_a.empty:
            all_totals = df_a.groupby('user')['calories'].sum()
            celebrations = []
            for u, cal in all_totals.items():
                u_lvl, _, _ = get_level_progress(cal)
                if u_lvl >= 5: celebrations.append(f"🎖️ {get_user_badge(u, df_u)} est un vétéran de Niveau {u_lvl} !")
                if cal > 10000: celebrations.append(f"🔥 {get_user_badge(u, df_u)} a brûlé plus de 10 000 kcal !")
            if celebrations: st.markdown(f"<div class='celeb-box'>{random.choice(celebrations)}</div>", unsafe_allow_html=True)
        st.divider()
        c_l, c_r = st.columns(2)
        with c_l:
            st.subheader("🧬 ADN Sportif")
            if sum(dna.values())>0:
                mx = max(dna.values())
                fig = px.line_polar(pd.DataFrame({'K':dna.keys(), 'V':[v/mx*100 for v in dna.values()]}), r='V', theta='K', line_close=True)
                fig.update_traces(fill='toself', line_color='rgba(255, 75, 75, 0.7)')
                fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 100]), bgcolor='rgba(0,0,0,0)'), font=dict(size=10, color="white"), paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=80, r=80, t=20, b=20), height=300)
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

    with tabs[1]: # PARTAGE (FEED)
        st.header("📸 Mur de Partage (7 jours)")
        with st.expander("📷 Poster une photo"):
            with st.form("post_form"):
                p_img = st.file_uploader("Photo (obligatoire)", type=['jpg','jpeg','png'])
                p_com = st.text_input("Un petit commentaire ?")
                if st.form_submit_button("Publier"):
                    if p_img:
                        b64_img = process_post_image(p_img)
                        if b64_img: save_post(b64_img, p_com); st.success("Publié !"); st.rerun()
                    else: st.error("Image requise.")
        
        st.divider()
        if not df_p.empty:
            df_p = df_p.sort_values(by="date", ascending=False)
            for _, r in df_p.iterrows():
                viewers = str(r['seen_by']).split(',')
                if user not in viewers: mark_post_seen(r['id'], user) 
                
                st.markdown(f"""
                <div class='post-card'>
                    <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>
                        {get_user_badge(r['user'], df_u)}
                        <span style='color:#aaa; font-size:0.8em;'>{r['date']}</span>
                    </div>
                    <img src='{r['image']}' style='width:100%; border-radius:5px; margin-bottom:10px;'>
                    <p style='font-size:1.1em;'>{r['comment']}</p>
                    <hr style='border-color:#555;'>
                    <div style='display:flex; flex-wrap:wrap; align-items:center;'>
                        <span style='margin-right:10px; color:#aaa; font-size:0.9em;'>Vu par :</span>
                        {''.join([get_user_badge(v, df_u) for v in viewers if v])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else: st.info("Aucun post récent. Soyez le premier !")

    with tabs[2]: # SEANCE
        st.subheader("Ajouter une séance")
        # Sélection du sport en dehors du form pour permettre le refresh
        s = st.selectbox("Sport", SPORTS_LIST, key="sport_selection")
        
        with st.form("add"):
            c1, c2 = st.columns(2)
            d = c1.date_input("Date", date.today())
            t = c2.time_input("Heure", datetime.now().time())
            
            # Champs conditionnels selon le sport choisi
            val_steps = 0
            val_km = 0.0
            
            if s == "Marche":
                input_type = st.radio("Je renseigne :", ["Durée (min)", "Nombre de pas", "Distance (km)"], horizontal=True)
                if input_type == "Nombre de pas":
                    val_steps = st.number_input("Nombre de pas", 0, 100000, 5000)
                elif input_type == "Distance (km)":
                    val_km = st.number_input("Distance (km)", 0.0, 100.0, 5.0)
            elif s == "Course":
                input_type = st.radio("Je renseigne :", ["Durée (min)", "Distance (km)"], horizontal=True)
                if input_type == "Distance (km)":
                    val_km = st.number_input("Distance (km)", 0.0, 100.0, 5.0)
                
            m = c2.number_input("Durée (min)", 1, 300, 45)
            w = st.number_input("Poids du jour", 0.0, 200.0, float(w_curr))
            
            if st.form_submit_button("Sauvegarder"):
                dt = datetime.combine(d, t)
                
                # Calcul spécifique selon le sport
                base_kcal = 0
                # Si l'utilisateur n'a pas renseigné la durée mais a mis des pas ou des km, on estime la durée pour la BDD
                if s == "Marche" and val_steps > 0:
                    base_kcal = val_steps * 0.045 # Moyenne 0.045 kcal/pas
                    if m <= 1: m = int(val_steps / 100) # Est. 100 pas/min
                elif (s == "Marche" or s == "Course") and val_km > 0:
                    base_kcal = w * val_km # Moyenne 1 kcal/kg/km
                    if m <= 1: 
                        if s == "Marche": m = int(val_km * 12) # Est. 5km/h
                        else: m = int(val_km * 6) # Est. 10km/h
                else:
                    # Formule standard pour les autres sports (et durée)
                    dna = DNA_MAP.get(s, {})
                    intens = (dna.get("Force", 5) + dna.get("Endurance", 5))/2
                    base_kcal = (calculate_bmr(w, prof['h'], 25, prof['sex'])/24) * (intens/1.5) * (m/60)
                
                epoc_rate = EPOC_MAP.get(s, 0.05)
                epoc_bonus = base_kcal * epoc_rate
                total_kcal = base_kcal + epoc_bonus
                
                if save_activity(pd.DataFrame([{"date": dt, "user": user, "sport": s, "minutes": m, "calories": int(total_kcal), "poids": w}])):
                    st.success(f"✅ +{int(total_kcal)} kcal"); st.caption(f"Effort: {int(base_kcal)} + Afterburn: {int(epoc_bonus)}"); st_lottie(load_lottieurl(LOTTIE_SUCCESS), height=100); time.sleep(2); st.rerun()
        
        st.divider()
        st.subheader("📜 Historique de vos séances")
        if not my_df.empty:
            df_display = my_df.copy(); df_display.insert(0, "Supprimer", False)
            edi = st.data_editor(df_display, use_container_width=True, num_rows="dynamic", column_config={"Supprimer": st.column_config.CheckboxColumn("🗑️ Cocher pour supprimer", default=False)})
            if st.button("💾 Sauvegarder changements"):
                to_keep = edi[edi['Supprimer'] == False].drop(columns=['Supprimer'])
                to_keep['date'] = pd.to_datetime(to_keep['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
                to_keep['poids'] = pd.to_numeric(to_keep['poids']); to_keep['calories'] = pd.to_numeric(to_keep['calories'])
                conn.update(worksheet="Activites", data=pd.concat([df_a[df_a['user'] != user], to_keep], ignore_index=True))
                st.cache_data.clear(); st.success("Mise à jour réussie !"); st.rerun()

    with tabs[3]: # BOSS
        curr_month_num = datetime.now().month
        boss_name, boss_max_hp, boss_img = BOSS_CALENDAR.get(curr_month_num, ("Monstre", 200000, ""))
        st.header(f"👹 BOSS DU MOIS : {boss_name.upper()}")
        df_month = df_a[df_a['date'].dt.strftime("%Y-%m") == datetime.now().strftime("%Y-%m")]
        dmg = df_month['calories'].sum(); pct_hp = max(0, (boss_max_hp - dmg) / boss_max_hp)
        c_img, c_stat = st.columns([1, 2])
        with c_img: st.image(boss_img, use_container_width=True)
        with c_stat:
            col = "#4CAF50" if pct_hp > 0.5 else ("#FF9800" if pct_hp > 0.2 else "#F44336")
            st.markdown(f"""<div style="margin-bottom:5px;color:white;font-weight:bold;">PV Restants : {int(boss_max_hp - dmg)} / {boss_max_hp}</div><div class="boss-bar"><div class="boss-fill" style="width: {pct_hp*100}%; background-color: {col};"></div></div>""", unsafe_allow_html=True)
            if pct_hp <= 0: st.balloons(); st.success("🏆 LE BOSS EST VAINCU !")
            else: st.info(f"Il reste {int(pct_hp*100)}% de vie.")
            st.markdown("### ⚔️ Meilleurs Attaquants")
            if not df_month.empty:
                for i, (u, val) in enumerate(df_month.groupby("user")['calories'].sum().sort_values(ascending=False).head(5).items()): st.markdown(f"**{i+1}. {get_user_badge(u, df_u)}** : {int(val)} dégâts", unsafe_allow_html=True)

    with tabs[4]: # DEFIS
        st.header("⚔️ Salle des Défis")
        with st.expander("➕ Lancer un nouveau défi"):
            with st.form("new_def"):
                dt = st.text_input("Nom"); type_def = st.selectbox("Cible", ["Calories (kcal)", "Durée (min)", "Distance (km)"]); sport_target = st.selectbox("Sport", ["Tous les sports"] + SPORTS_LIST); obj = st.number_input("Objectif", 10.0, 50000.0, 500.0); fin = st.date_input("Fin")
                if st.form_submit_button("Créer"): create_challenge(dt, type_def, obj, sport_target, fin); st.success("Lancé !"); time.sleep(1); st.rerun()
        st.subheader("Défis en cours")
        if not df_d.empty:
            for _, r in df_d[df_d['statut'] == 'Actif'].iterrows():
                parts = r['participants'].split(','); unit = "kcal" if "Calories" in r['type'] else ("km" if "Distance" in r['type'] else "min")
                c_df = df_a[(df_a['date'] <= r['date_fin']) & (df_a['user'].isin(parts))]
                if r['sport_cible'] != "Tous les sports": c_df = c_df[c_df['sport'] == r['sport_cible']]
                prog = c_df.groupby('user')['calories'].sum() if "Calories" in r['type'] else (c_df.groupby('user')['minutes'].sum() if "Durée" in r['type'] else c_df.apply(lambda row: (row['minutes']/60) * SPEED_MAP.get(row['sport'], 0), axis=1).groupby(c_df['user']).sum())
                prog = prog.reindex(parts, fill_value=0)
                st.markdown(f"<div class='challenge-card'><h3>🏆 {r['titre']}</h3><p>Cible : <b>{int(r['objectif'])} {unit}</b> avant le {r['date_fin']}</p><p style='font-size:0.9em; color:#aaa'>Créé par {get_user_badge(r['createur'], df_u)}</p></div>", unsafe_allow_html=True)
                c_act, c_list = st.columns([1, 2])
                with c_act:
                    if user not in parts: 
                        if st.button("Rejoindre", key=r['id']): join_challenge(r['id']); st.rerun()
                    else: st.write("✅ Participant")
                    if r['createur'] == user: 
                        if st.button("🗑️ Supprimer", key=f"del_{r['id']}"): delete_challenge(r['id']); st.rerun()
                with c_list:
                    for u, val in prog.sort_values(ascending=False).items():
                        pct = min(val/float(r['objectif']), 1.0); st.markdown(f"{get_user_badge(u, df_u)} : {int(val)} {unit}", unsafe_allow_html=True); st.progress(pct)
                st.divider()

    with tabs[5]: # STATS
        if not my_df.empty:
            st.subheader("🏆 Records")
            max_c = my_df['calories'].max(); max_m = my_df['minutes'].max(); fav = my_df['sport'].mode()[0] if not my_df['sport'].mode().empty else "Aucun"
            tot_sess = len(my_df)
            
            # CSS GRID pour le CARRÉ 2x2
            st.markdown(f"""
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px;">
                <div class="stat-card"><div style="font-size: 2em;">🔥</div><div class="stat-val">{int(max_c)}</div><div class="stat-label">Max Kcal</div></div>
                <div class="stat-card"><div style="font-size: 2em;">⏱️</div><div class="stat-val">{int(max_m)} min</div><div class="stat-label">Max Min</div></div>
                <div class="stat-card"><div style="font-size: 2em;">❤️</div><div class="stat-val">{fav}</div><div class="stat-label">Sport Favori</div></div>
                <div class="stat-card"><div style="font-size: 2em;">🏋️‍♂️</div><div class="stat-val">{tot_sess}</div><div class="stat-label">Total Sessions</div></div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("🔥 Info Afterburn"): st.info("L'Afterburn (EPOC) est ajouté automatiquement à vos calories !")
            df_chart = my_df.copy(); c1, c2 = st.columns(2)
            c1.plotly_chart(px.line(df_chart, x='date', y='poids', title="Poids", markers=True).update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white'), use_container_width=True, config={'staticPlot': True})
            c2.plotly_chart(px.bar(df_chart, x='date', y='calories', title="Kcal").update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white'), use_container_width=True, config={'staticPlot': True})

    with tabs[6]: # CLASSEMENT
        st.header("🏛️ Hall of Fame")
        if not df_a.empty:
            mc = df_a.loc[df_a['calories'].idxmax()]; mm = df_a.loc[df_a['minutes'].idxmax()]
            c1, c2 = st.columns(2)
            c1.markdown(f"<div class='glass'><h3>🔥 Machine</h3><p><b>{get_user_badge(mc['user'], df_u)}</b> {int(mc['calories'])} kcal</p></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='glass'><h3>⏳ Endurance</h3><p><b>{get_user_badge(mm['user'], df_u)}</b> {int(mm['minutes'])} min</p></div>", unsafe_allow_html=True)
            st.divider(); st.subheader("🏆 Semaine")
            w_df = df_a[df_a['date'] >= (pd.Timestamp.now() - pd.Timedelta(days=7))]
            if not w_df.empty:
                for i, (u, c) in enumerate(w_df.groupby("user")['calories'].sum().sort_values(ascending=False).items()):
                    st.markdown(f"**{i+1}. {get_user_badge(u, df_u)}** - {int(c)} kcal", unsafe_allow_html=True)

    with tabs[7]: # PROFIL
        st.subheader("📝 Profil")
        with st.form("prof"):
            c1, c2 = st.columns(2)
            new_pseudo = c1.text_input("Pseudo (Nom d'utilisateur)", value=user)
            nd = c2.date_input("Naissance", datetime.strptime(prof.get('dob','2000-01-01'),"%Y-%m-%d")); ns = c1.selectbox("Sexe",["Homme","Femme"],0 if prof.get('sex')=="Homme" else 1)
            nh = c2.number_input("Taille",100,250,int(prof.get('h',175))); nw = c1.number_input("Obj Poids",40.0,150.0,float(prof.get('w_obj',65.0)))
            na = c2.selectbox("Activité",ACTIVITY_OPTS); n_av = st.file_uploader("Avatar", type=['png','jpg']); np = st.text_input("Nouveau PIN", type="password", max_chars=4)
            if st.form_submit_button("Sauvegarder"):
                if new_pseudo != user:
                    res = change_username(user, new_pseudo)
                    if res == "OK":
                        st.session_state.user = new_pseudo
                        user = new_pseudo
                        st.success("Pseudo changé !")
                    else:
                        st.error(f"Erreur changement pseudo: {res}")
                
                fav = prof.get('avatar', ""); 
                if n_av: fav = process_avatar(n_av)
                prof.update({'dob':str(nd),'sex':ns,'h':int(nh),'w_obj':float(nw),'act':na,'avatar':fav})
                ps = row['pin']; 
                if np and len(np)==4: ps = hash_pin(np)
                save_user(user, ps, prof); st.success("Mis à jour !"); st.rerun()
        st.divider()
        if st.button("Supprimer mon compte"): 
            if delete_current_user(): st.session_state.user = None; st.rerun()
