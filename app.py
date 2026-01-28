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

# --- 1. CONFIGURATION & CONSTANTES (Doit rester en dehors du main) ---
st.set_page_config(page_title="FollowFit", page_icon="✨", layout="wide")

# URLs
LOTTIE_SUCCESS = "https://assets5.lottiefiles.com/packages/lf20_u4yrau.json"
BACKGROUND_URL = "https://raw.githubusercontent.com/mateohier/my-fitness-app/refs/heads/main/AAAAAAAAAAAAAAAA.png"

# CONSTANTE DE SECURITE (90% du total calculé = on enlève 10% par prudence)
SAFETY_FACTOR = 0.9

def main():
    # --- DEFINITION DES TITRES (Ordre dynamique) ---
    STATUS_TITLES = [
        ("Canapé Warrior", "Sortir du canapé, c’est déjà un exploit."),
        ("Je sors du canapé", "Ton corps se réveille et se rappelle qu’il existe."),
        ("Bougeur Régulier", "Bouger devient naturel, la routine s’installe."),
        ("Motivé", "Les entraînements ne font plus peur."),
        ("En Forme", "Énergie et endurance commencent à se voir."),
        ("Solide", "Force et régularité qui commencent à impressionner."),
        ("Affûté", "Endurance et technique au rendez-vous."),
        ("Bête de Sport", "Intensité élevée, performances visibles."),
        ("Champion du Quotidien", "Ton niveau inspire les autres autour de toi."),
        ("Héros de la Forme", "Niveau exceptionnel, respect total.")
    ]

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

    # --- MAPPINGS (Optimisés pour réalisme) ---
    DNA_MAP = {
        # Sports Cardio intenses
        "Course":          {"Force": 5, "Endurance": 25, "Vitesse": 10, "Agilité": 5, "Souplesse": 3, "Explosivité": 6, "Mental": 9, "Récupération": 8, "Concentration": 6},
        "Corde à sauter":  {"Force": 8, "Endurance": 28, "Vitesse": 9, "Agilité": 10, "Souplesse": 4, "Explosivité": 9, "Mental": 8, "Récupération": 6, "Concentration": 8},
        "Crossfit":        {"Force": 15, "Endurance": 15, "Vitesse": 6, "Agilité": 6, "Souplesse": 5, "Explosivité": 9, "Mental": 9, "Récupération": 6, "Concentration": 7},
        "Boxe":            {"Force": 12, "Endurance": 18, "Vitesse": 8, "Agilité": 9, "Souplesse": 6, "Explosivité": 9, "Mental": 9, "Récupération": 5, "Concentration": 9},
        "Natation":        {"Force": 10, "Endurance": 17, "Vitesse": 6, "Agilité": 6, "Souplesse": 7, "Explosivité": 6, "Mental": 9, "Récupération": 10, "Concentration": 8},
        
        # Sports Modérés / Cardio
        "Vélo":            {"Force": 8, "Endurance": 16, "Vitesse": 6, "Agilité": 3, "Souplesse": 2, "Explosivité": 4, "Mental": 7, "Récupération": 9, "Concentration": 5},
        "Rameur":          {"Force": 10, "Endurance": 14, "Vitesse": 5, "Agilité": 3, "Souplesse": 3, "Explosivité": 6, "Mental": 8, "Récupération": 6, "Concentration": 6},
        "Tennis":          {"Force": 8, "Endurance": 13, "Vitesse": 8, "Agilité": 9, "Souplesse": 4, "Explosivité": 7, "Mental": 7, "Récupération": 5, "Concentration": 9},
        "Football":        {"Force": 7, "Endurance": 14, "Vitesse": 8, "Agilité": 7, "Souplesse": 4, "Explosivité": 7, "Mental": 7, "Récupération": 5, "Concentration": 7},
        "Basket":          {"Force": 7, "Endurance": 14, "Vitesse": 8, "Agilité": 8, "Souplesse": 5, "Explosivité": 8, "Mental": 6, "Récupération": 5, "Concentration": 7},
        "Handball":        {"Force": 8, "Endurance": 13, "Vitesse": 7, "Agilité": 8, "Souplesse": 4, "Explosivité": 7, "Mental": 7, "Récupération": 5, "Concentration": 7},
        "Ski":             {"Force": 9, "Endurance": 12, "Vitesse": 8, "Agilité": 7, "Souplesse": 3, "Explosivité": 5, "Mental": 6, "Récupération": 4, "Concentration": 8},
        "Badminton":       {"Force": 6, "Endurance": 12, "Vitesse": 10, "Agilité": 10, "Souplesse": 5, "Explosivité": 8, "Mental": 7, "Récupération": 5, "Concentration": 8},
        "Elliptique":      {"Force": 6, "Endurance": 15, "Vitesse": 4, "Agilité": 2, "Souplesse": 2, "Explosivité": 2, "Mental": 5, "Récupération": 7, "Concentration": 4},
        
        # Sports de Force / Technique
        "Musculation":     {"Force": 15, "Endurance": 5, "Vitesse": 3, "Agilité": 2, "Souplesse": 3, "Explosivité": 6, "Mental": 7, "Récupération": 5, "Concentration": 8},
        "Escalade":        {"Force": 12, "Endurance": 8, "Vitesse": 3, "Agilité": 8, "Souplesse": 9, "Explosivité": 6, "Mental": 10, "Récupération": 4, "Concentration": 10},
        "Judo":            {"Force": 12, "Endurance": 9, "Vitesse": 5, "Agilité": 7, "Souplesse": 6, "Explosivité": 8, "Mental": 9, "Récupération": 4, "Concentration": 9},
        "Karaté":          {"Force": 10, "Endurance": 10, "Vitesse": 8, "Agilité": 8, "Souplesse": 7, "Explosivité": 9, "Mental": 9, "Récupération": 5, "Concentration": 9},
        "Volley":          {"Force": 8, "Endurance": 8, "Vitesse": 6, "Agilité": 8, "Souplesse": 5, "Explosivité": 9, "Mental": 7, "Récupération": 5, "Concentration": 7},
        "Gymnastique":     {"Force": 10, "Endurance": 8, "Vitesse": 5, "Agilité": 10, "Souplesse": 10, "Explosivité": 9, "Mental": 9, "Récupération": 4, "Concentration": 10},
        "Danse":           {"Force": 6, "Endurance": 10, "Vitesse": 5, "Agilité": 10, "Souplesse": 9, "Explosivité": 4, "Mental": 6, "Récupération": 6, "Concentration": 8},
        
        # Activités Douces
        "Randonnée":       {"Force": 6, "Endurance": 10, "Vitesse": 2, "Agilité": 3, "Souplesse": 2, "Explosivité": 2, "Mental": 7, "Récupération": 8, "Concentration": 5},
        "Marche":          {"Force": 3, "Endurance": 8, "Vitesse": 2, "Agilité": 2, "Souplesse": 2, "Explosivité": 1, "Mental": 4, "Récupération": 10, "Concentration": 3},
        "Yoga":            {"Force": 5, "Endurance": 6, "Vitesse": 1, "Agilité": 6, "Souplesse": 10, "Explosivité": 1, "Mental": 9, "Récupération": 10, "Concentration": 10},
        "Pilates":         {"Force": 6, "Endurance": 5, "Vitesse": 1, "Agilité": 6, "Souplesse": 9, "Explosivité": 2, "Mental": 8, "Récupération": 9, "Concentration": 9},
        "Sport de chambre": {"Force": 4, "Endurance": 7, "Vitesse": 4, "Agilité": 5, "Souplesse": 7, "Explosivité": 4, "Mental": 5, "Récupération": 9, "Concentration": 6}
    }
    SPORTS_LIST = sorted(list(DNA_MAP.keys()))

    SPEED_MAP = {
        "Course": 10.0, "Vélo": 20.0, "Natation": 2.5, "Marche": 5.0, 
        "Randonnée": 4.0, "Ski": 15.0, "Football": 7.0, "Tennis": 3.0,
        "Musculation": 0.0, "Crossfit": 0.0, "Yoga": 0.0, "Pilates": 0.0,
        "Boxe": 0.0, "Danse": 0.0, "Escalade": 0.1, "Basket": 4.0,
        "Judo": 0.0, "Karaté": 0.0, "Gymnastique": 0.0, "Volley": 3.0,
        "Handball": 6.0,
        "Badminton": 4.0, "Rameur": 8.0, "Elliptique": 8.0,
        "Corde à sauter": 0.0,
        "Sport de chambre": 0.0
    }

    EPOC_MAP = {
        "Crossfit": 0.15, "Musculation": 0.10, "Boxe": 0.12, "Rugby": 0.12, "Judo": 0.12, "Karaté": 0.12,
        "Course": 0.07, "Vélo": 0.05, "Natation": 0.12, "Tennis": 0.05, "Football": 0.07, "Basket": 0.07,
        "Rameur": 0.08, "Elliptique": 0.05, "Badminton": 0.05, "Volley": 0.04,
        "Ski": 0.06, "Escalade": 0.05, "Danse": 0.04, "Gymnastique": 0.06,
        "Handball": 0.07, "Corde à sauter": 0.12,
        "Marche": 0.01, "Yoga": 0.02, "Pilates": 0.02, "Randonnée": 0.03,
        "Sport de chambre": 0.04
    }

    ACTIVITY_OPTS = ["Sédentaire (1.2)", "Légèrement actif (1.375)", "Actif (1.55)", "Très actif (1.725)"]

    FOOD_LEVELS = {
        1: 150, 2: 300, 3: 500,
        4: 800, 5: 1200, 6: 1800,
        7: 2500
    }

    FOOD_LABELS = {
        1: "🍏 Très léger (Snack)", 2: "🥗 Léger (Salade)", 3: "🍲 Moyen (Equilibré)",
        4: "🍝 Normal (Assiette pleine)", 5: "🍗 Copieux (Resto)", 6: "🍔 Très Riche (Fast Food XL)",
        7: "🎂 Festin (Buffet à volonté)"
    }

    # --- PALIERS DE VOYAGE (KM) ---
    MILESTONES = [
        (42, "Marathon 🏃"),
        (344, "Paris ➡ Londres 🇬🇧"),
        (1000, "Traversée de la France (Nord-Sud) 🇫🇷"),
        (1332, "Tour de l'Islande 🇮🇸"),
        (2480, "Paris ➡ Moscou 🇷🇺"),
        (3940, "Route 66 (USA) 🇺🇸"),
        (4500, "New York ➡ Los Angeles 🗽"),
        (5836, "Paris ➡ New York ✈️")
    ]

    # --- 2. UTILITAIRES ---
    def hash_pin(pin): return hashlib.sha256(str(pin).encode()).hexdigest()

    def safe_date_convert(df, col_name):
        """Force la conversion en datetime et supprime les erreurs"""
        if df.empty: return df
        if col_name in df.columns:
            df[col_name] = pd.to_datetime(df[col_name], errors='coerce')
            df = df.dropna(subset=[col_name])
        return df

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
        try:
            val = (10 * float(weight)) + (6.25 * float(height)) - (5 * float(age))
            return (val + 5)*1.2 if sex == "Homme" else (val - 161)*1.2
        except: return 1500

    def get_level_progress(total_cal):
        factor = 150 
        if total_cal == 0: return 1, 0.0, 100
        # Cette formule permet des niveaux infinis (ex: 470 000 cal = niveau 262 en 3 ans)
        # 5*L^2 + 495*L = Calories
        level = int((-495 + (495**2 - 4 * 5 * (-total_cal))**0.5) / 10)
        if level == 0: level = 1
        
        cal_curr = 5 * (level**2) + 495 * level
        next_lvl = level + 1
        cal_next = 5 * (next_lvl**2) + 495 * next_lvl
        
        pct = min(max((total_cal - cal_curr) / (cal_next - cal_curr), 0.0), 1.0)
        return level, pct, int(cal_next - total_cal)

    def get_status_from_level(lvl):
        """
        Détermine le titre en fonction du niveau.
        Logique de progression des paliers :
        - Statut 0 : Niv 1 à 5 (Gap=5).
        - Statut 1 : Atteint au Niv 6 (Gap=11).
        - Statut 2 : Atteint au Niv 17 (Gap=17).
        - Progression gap : +6 à chaque rang (5, 11, 17, 23, 29...).
        """
        threshold = 1 # Niveau de départ
        gap = 5       # Premier saut (5 niveaux pour atteindre le statut 1)
        
        # On parcourt la liste des titres
        for i in range(len(STATUS_TITLES)):
            next_threshold = threshold + gap
            if lvl < next_threshold:
                return STATUS_TITLES[i]
            
            threshold = next_threshold
            gap += 6 # L'écart grandit de 6 niveaux à chaque rang

        # Gestion des niveaux infinis
        base_t, _ = STATUS_TITLES[-1]
        prestige_count = 0
        while lvl >= threshold + gap:
            threshold += gap
            gap += 6
            prestige_count += 1
            
        return f"{base_t} (Prestige {prestige_count + 1})", "Légende vivante."

    def check_achievements(df):
        badges = []
        if df.empty: return badges
        df = safe_date_convert(df.copy(), 'date')
        try:
            df['hour'] = df['date'].dt.hour
            df['day'] = df['date'].dt.day_name()
            if len(df[df['hour'] < 8]) >= 3: badges.append(("🌅 Lève-tôt", "3 séances avant 8h"))
            if len(df[df['day'] == 'Sunday']) >= 4: badges.append(("⛪ Messe Sportive", "4 Dimanches actifs"))
            if df['minutes'].max() >= 120: badges.append(("🥵 Titan", "Séance > 2h"))
            if df['calories'].sum() >= 10000: badges.append(("🔥 Fournaise", "10k kcal brûlées"))
        except: pass
        return badges

    def calculate_advanced_streaks(df_all, current_user):
        user_streak = 0
        df_user = df_all[df_all['user'] == current_user].copy()
        df_user = safe_date_convert(df_user, 'date')
        
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
            df_all = safe_date_convert(df_all.copy(), 'date')
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
            try: df_b = conn.read(worksheet="Bouffe", ttl=600)
            except: df_b = pd.DataFrame(columns=["date", "user", "type_repas", "calorie_est"])
            try: df_bal = conn.read(worksheet="Balance", ttl=600)
            except: df_bal = pd.DataFrame(columns=["date", "user", "poids"])
            
            if df_u.empty: df_u = pd.DataFrame(columns=["user", "pin", "json_data"])
            
            # --- STRUCTURE ---
            if df_a.empty: 
                df_a = pd.DataFrame(columns=["date", "user", "sport", "minutes", "calories", "distance", "pas"])
            else:
                if 'distance' not in df_a.columns: df_a['distance'] = 0.0
                if 'pas' not in df_a.columns: df_a['pas'] = 0
                if 'steps' in df_a.columns: df_a = df_a.drop(columns=['steps'])
            
            if df_d.empty: 
                df_d = pd.DataFrame(columns=["id", "titre", "type", "objectif", "sport_cible", "createur", "participants", "date_fin", "statut", "date_debut"])
            else:
                # Ajout rétroactif colonne date_debut si manquante
                if 'date_debut' not in df_d.columns: df_d['date_debut'] = "2024-01-01"

            if df_p.empty: df_p = pd.DataFrame(columns=["id", "user", "date", "image", "comment", "seen_by"])
            if df_b.empty: df_b = pd.DataFrame(columns=["date", "user", "type_repas", "calorie_est"])
            if df_bal.empty: df_bal = pd.DataFrame(columns=["date", "user", "poids"])
                
            # --- CONVERSION SECURISEE ---
            df_a = safe_date_convert(df_a, 'date')
            df_a['calories'] = pd.to_numeric(df_a['calories'], errors='coerce').fillna(0)
            df_a['minutes'] = pd.to_numeric(df_a['minutes'], errors='coerce').fillna(0)
            
            df_p = safe_date_convert(df_p, 'date')
            
            df_b = safe_date_convert(df_b, 'date')
            df_b['calorie_est'] = pd.to_numeric(df_b['calorie_est'], errors='coerce').fillna(0)

            df_bal = safe_date_convert(df_bal, 'date')
            df_bal['poids'] = pd.to_numeric(df_bal['poids'], errors='coerce').fillna(0)
            
            return df_u, df_a, df_d, df_p, df_b, df_bal
        except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    def save_activity(new_row):
        try:
            df = conn.read(worksheet="Activites", ttl=0)
            if 'distance' not in df.columns: df['distance'] = 0.0
            if 'pas' not in df.columns: df['pas'] = 0
            
            upd = pd.concat([df, new_row], ignore_index=True)
            upd['date'] = pd.to_datetime(upd['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
            conn.update(worksheet="Activites", data=upd)
            st.cache_data.clear(); return True
        except: return False

    def save_weight(new_row):
        try:
            df = conn.read(worksheet="Balance", ttl=0)
            upd = pd.concat([df, new_row], ignore_index=True)
            upd['date'] = pd.to_datetime(upd['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
            conn.update(worksheet="Balance", data=upd)
            st.cache_data.clear(); return True
        except: return False

    def save_food(new_row):
        try:
            df = conn.read(worksheet="Bouffe", ttl=0)
            upd = pd.concat([df, new_row], ignore_index=True)
            upd['date'] = pd.to_datetime(upd['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
            conn.update(worksheet="Bouffe", data=upd)
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

    def clean_old_posts(df_p):
        try:
            if df_p.empty: return
            now = datetime.now()
            df_p = safe_date_convert(df_p, 'date')
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
        try:
            df_u = conn.read(worksheet="Profils", ttl=0)
            if new_u in df_u['user'].values: return "Ce pseudo existe déjà"
            
            df_a = conn.read(worksheet="Activites", ttl=0)
            df_d = conn.read(worksheet="Defis", ttl=0)
            df_p = conn.read(worksheet="Posts", ttl=0)
            df_b = conn.read(worksheet="Bouffe", ttl=0)
            
            df_u.loc[df_u['user'] == old_u, 'user'] = new_u
            if not df_a.empty: df_a.loc[df_a['user'] == old_u, 'user'] = new_u
            if not df_b.empty: df_b.loc[df_b['user'] == old_u, 'user'] = new_u

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
            conn.update(worksheet="Bouffe", data=df_b)
            st.cache_data.clear()
            return "OK"
        except Exception as e: return str(e)

    def delete_current_user():
        try:
            user = st.session_state.user
            df_u = conn.read(worksheet="Profils", ttl=0); df_a = conn.read(worksheet="Activites", ttl=0); df_d = conn.read(worksheet="Defis", ttl=0); df_b = conn.read(worksheet="Bouffe", ttl=0)
            df_u = df_u[df_u['user'] != user]; df_a = df_a[df_a['user'] != user]; df_b = df_b[df_b['user'] != user]
            def remove_p(p_str): parts = str(p_str).split(','); return ",".join([p for p in parts if p != user])
            df_d['participants'] = df_d['participants'].apply(remove_p)
            conn.update(worksheet="Profils", data=df_u); conn.update(worksheet="Activites", data=df_a); conn.update(worksheet="Defis", data=df_d); conn.update(worksheet="Bouffe", data=df_b)
            st.cache_data.clear(); return True
        except: return False

    def create_challenge(titre, type_def, obj, sport_cible, fin):
        try:
            df = conn.read(worksheet="Defis", ttl=0)
            # AJOUT : date_debut est fixé à aujourd'hui
            new = pd.DataFrame([{
                "id": str(uuid.uuid4()), "titre": titre, "type": type_def, "objectif": float(obj), 
                "sport_cible": sport_cible, "createur": st.session_state.user, 
                "participants": st.session_state.user, "date_fin": str(fin), 
                "statut": "Actif", "date_debut": datetime.now().strftime('%Y-%m-%d')
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
        return f"""<span style='display:inline-flex;align-items:center;border:1px solid rgba(128,128,128,0.3);border-radius:20px;padding:2px 10px;background:rgba(128,128,128,0.2);margin-right:5px;'><img src='{avatar}' style='width:25px;height:25px;border-radius:50%;margin-right:8px;object-fit:cover;background:white;'><span style='font-weight:bold;'>{username.capitalize()}</span></span>"""

    # --- 4. LOGIQUE & THEME ---
    if 'user' not in st.session_state: st.session_state.user = None

    # Chargement données (df_bal pour la balance)
    df_u, df_a, df_d, df_p, df_b, df_bal = get_data()
    clean_old_posts(df_p)

    current_theme = "Sombre"
    if st.session_state.user:
        try:
            u_row = df_u[df_u['user'] == st.session_state.user].iloc[0]
            u_prof = json.loads(u_row['json_data'])
            current_theme = u_prof.get('theme', 'Sombre')
        except: pass

    # --- CSS DYNAMIQUE ---
    if current_theme == "Sombre":
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
        plotly_layout_dark = True
    else:
        st.markdown(f"""
        <style>
        .stApp {{ background-color: #f8f9fa; }}
        .stMetricValue {{ font-size: 1.5rem !important; color: #d32f2f !important; }}
        div[data-testid="stSidebar"] {{ background-color: #ffffff; border-right: 1px solid #ddd; }}
        .quote-box {{ padding: 10px; background: linear-gradient(90deg, #FF4B4B, #FF9068); border-radius: 8px; color: white; text-align: center; font-weight: bold; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .glass {{ background: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #ddd; box-shadow: 0 4px 6px rgba(0,0,0,0.05); color: #333; }}
        .challenge-card {{ background: #ffffff; border-left: 5px solid #FF4B4B; padding: 15px; margin-bottom: 10px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); color: #333; }}
        .boss-bar {{ width: 100%; background-color: #e0e0e0; border-radius: 10px; overflow: hidden; height: 30px; margin-bottom: 10px; border: 1px solid #ccc; }}
        .boss-fill {{ height: 100%; background: linear-gradient(90deg, #FF4B4B, #FF0000); transition: width 0.5s; }}
        .celeb-box {{ background-color: #fff9c4; border: 1px solid #fbc02d; padding: 15px; border-radius: 10px; text-align: center; margin-top: 10px; color: #333; }}
        .stat-card {{ background: #ffffff; border: 1px solid #ddd; border-radius: 10px; padding: 15px; text-align: center; flex: 1; min-width: 150px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .stat-val {{ font-size: 1.8em; font-weight: bold; color: #d32f2f; }}
        .stat-label {{ font-size: 0.9em; color: #555; margin-top: 5px; font-weight: 500; }}
        .post-card {{ background: #ffffff; border-radius: 10px; padding: 15px; margin-bottom: 20px; border: 1px solid #ddd; box-shadow: 0 2px 5px rgba(0,0,0,0.05); color: #333; }}
        h1, h2, h3, p, div, span {{ color: #212529; }}
        .stMarkdown {{ color: #212529; }}
        div[data-baseweb="select"] > div, div[data-baseweb="base-input"], input {{ background-color: #ffffff !important; color: #000000 !important; border-color: #d3d3d3 !important; }}
        .stTextInput input, .stNumberInput input, .stDateInput input, .stTimeInput input {{ color: #000000 !important; }}
        div[data-baseweb="popover"], div[data-baseweb="menu"] {{ background-color: #ffffff !important; }}
        div[data-baseweb="option"] {{ color: #000000 !important; }}
        div[data-baseweb="select"] div {{ color: #000000 !important; }}
        button {{ background-color: #ffffff !important; color: #000000 !important; border: 1px solid #d3d3d3 !important; }}
        button[kind="primary"] {{ background-color: #FF4B4B !important; color: white !important; border: none !important; }}
        </style>
        """, unsafe_allow_html=True)
        plotly_layout_dark = False

    # --- 5. LOGIQUE INTERFACE ---
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
                    prof = {"dob": str(dob), "sex": sex, "h": h, "act": act, "w_init": w_init, "w_obj": w_obj, "theme": "Sombre"}
                    if save_user(u_input, hash_pin(p_input), prof): st.sidebar.success("Compte créé !"); time.sleep(1); st.rerun()
    else:
        user = st.session_state.user
        st.sidebar.markdown(f"👤 **{user.capitalize()}**")
        if st.sidebar.button("Déconnexion"): st.session_state.user = None; st.rerun()
        
        row = df_u[df_u['user'] == user].iloc[0]
        prof = json.loads(row['json_data'])
        my_df = df_a[df_a['user'] == user].copy()
        my_food = df_b[df_b['user'] == user].copy() if not df_b.empty else pd.DataFrame(columns=["date", "user", "type_repas", "calorie_est"])
        
        # Gestion des données Balance
        my_bal = df_bal[df_bal['user'] == user].copy() if not df_bal.empty else pd.DataFrame(columns=["date", "user", "poids"])
        
        # Poids actuel : dernier poids saisi dans Balance ou poids initial
        w_curr = float(my_bal.iloc[-1]['poids']) if not my_bal.empty else float(prof.get('w_init', 70))
        
        total_cal = my_df['calories'].sum()
        streak_user, streak_team = calculate_advanced_streaks(df_a, user)
        
        # --- ZONE DE MAINTENANCE (VISIBLE UNIQUEMENT PAR MAT) ---
        if user == "mat":
            with st.expander("⚠️ ADMIN ZONE - MISE À JOUR HISTORIQUE"):
                st.warning("Attention : Recalcul global de l'historique avec les nouvelles stats (DNA_MAP) et le facteur de sécurité (0.9).")
                
                if st.button("♻️ Lancer le recalcul"):
                    try:
                        # 1. Lire les données
                        df_act = conn.read(worksheet="Activites", ttl=0)
                        df_prof = conn.read(worksheet="Profils", ttl=0)
                        
                        if not df_act.empty and not df_prof.empty:
                            # 2. Fonction de recalcul
                            def update_row_calories(row):
                                u = row['user']
                                u_data = df_prof[df_prof['user'] == u]
                                if u_data.empty: return row['calories']
                                
                                prof_json = json.loads(u_data.iloc[0]['json_data'])
                                
                                # Valeurs par défaut si données manquantes
                                w = float(prof_json.get('w_init', 70)) 
                                h = float(prof_json.get('h', 175))
                                a = calculate_age(prof_json.get('dob', '2000-01-01'))
                                s = prof_json.get('sex', 'Homme')
                                bmr = calculate_bmr(w, h, a, s)
                                
                                sport = row['sport']
                                # Utilise les nouvelles stats définies plus haut dans ton code
                                stats = DNA_MAP.get(sport, {"Force": 5, "Endurance": 5}) 
                                
                                force = stats.get('Force', 5)
                                endurance = stats.get('Endurance', 5)
                                duree_h = row['minutes'] / 60
                                
                                # Intensité forcée à 1.0 (Moyenne)
                                base_kcal = (bmr / 24) * ((force + endurance) / 3) * duree_h * 1.0 
                                epoc = base_kcal * EPOC_MAP.get(sport, 0.05)
                                
                                # APPLIQUER LE FACTEUR DE SECURITE ICI AUSSI
                                return int((base_kcal + epoc) * SAFETY_FACTOR)

                            with st.spinner("Recalcul des calories en cours..."):
                                df_act['calories'] = df_act.apply(update_row_calories, axis=1)
                                conn.update(worksheet="Activites", data=df_act)
                                st.cache_data.clear()
                                
                            st.success("✅ Base de données mise à jour avec succès !")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Pas de données.")
                    except Exception as e:
                        st.error(f"Erreur : {e}")
        # --- FIN ZONE MAINTENANCE ---
        
        DNA_KEYS = ["Force", "Endurance", "Vitesse", "Agilité", "Souplesse", "Explosivité", "Mental", "Récupération", "Concentration"]
        dna = {k: 0 for k in DNA_KEYS}
        for _, r in my_df.iterrows():
            s_dna = DNA_MAP.get(r['sport'], {})
            h = r['minutes'] / 60
            for k in DNA_KEYS: dna[k] += s_dna.get(k, 1) * h

        tabs = st.tabs(["🏠 Tableau de Bord", "⚖️ Balance", "🍔 Bouffe", "📸 Partage", "➕ Séance", "👹 Boss", "⚔️ Défis", "📈 Statistiques", "🏆 Classement", "⚙️ Profil"])

        with tabs[0]: # DASHBOARD
            st.markdown(f"""<div style="display:flex;align-items:center;font-size:24px;font-weight:bold;margin-bottom:20px;">👋 Bienvenue &nbsp; {get_user_badge(user, df_u)}</div>""", unsafe_allow_html=True)
            st.markdown(f"<div class='quote-box'>{random.choice(['La douleur est temporaire.', 'Tu es une machine.', 'Go hard or go home.'])}</div>", unsafe_allow_html=True)
            
            lvl, pct, rem = get_level_progress(total_cal)
            
            # --- LOGIQUE AFFICHAGE NIVEAU ---
            user_title, user_desc = get_status_from_level(lvl)

            st.markdown(f"### ⚡ Niveau {lvl} : {user_title}")
            st.progress(pct)
            st.caption(f"_{user_desc}_")
            st.caption(f"Objectif Niveau {lvl+1} : Encore **{rem} kcal** à brûler ! 🔥")
            
            # --- CALCUL DU DÉFICIT COMPLEXE (Tab 0) ---
            total_fat_loss_real = 0.0
            if not my_df.empty or not my_food.empty:
                # 1. On détermine la date de début
                d_start_s = my_df['date'].min() if not my_df.empty else datetime.now()
                d_start_f = my_food['date'].min() if not my_food.empty else datetime.now()
                start_calc = min(d_start_s, d_start_f).date()
                end_calc = date.today()
                
                # 2. BMR Utilisateur
                u_bmr = calculate_bmr(w_curr, prof.get('h', 175), calculate_age(prof.get('dob', '2000-01-01')), prof.get('sex', 'Homme'))
                
                # 3. On groupe les données par jour
                df_s_group = my_df.copy(); df_s_group['day'] = df_s_group['date'].dt.date
                s_by_day = df_s_group.groupby('day')['calories'].sum()
                
                df_f_group = my_food.copy(); df_f_group['day'] = df_f_group['date'].dt.date
                f_by_day = df_f_group.groupby('day')['calorie_est'].sum()
                logged_days = set(df_f_group['day'].unique())
                
                # 4. Boucle jour par jour pour additionner le déficit
                cumul_deficit = 0
                for single_date in pd.date_range(start_calc, end_calc):
                    d = single_date.date()
                    s_val = s_by_day.get(d, 0)
                    f_val = f_by_day.get(d, 0)
                    
                    if d in logged_days:
                        # Si repas noté : (BMR + Sport) - Bouffe
                        day_res = (u_bmr + s_val) - f_val
                    else:
                        # Si rien noté : On ne compte que le sport (Prudence)
                        day_res = s_val
                    
                    cumul_deficit += day_res
                
                # Conversion kcal -> kg de gras
                total_fat_loss_real = cumul_deficit / 7700

            # --- AFFICHAGE METRIQUES (Modifié pour inclure le compteur) ---
            st.markdown("### 📊 Cumul Global")
            k1, k2, k3 = st.columns(3) # On passe de 2 à 3 colonnes
            
            # Colonne 1 : Originale
            k1.metric("Total Sport (Kcal)", f"{int(total_cal)} kcal")
            
            # Colonne 2 : Originale (Juste renommée pour clarifier)
            kg_fat_sport = total_cal / 7700
            k2.metric("Gras (Sport seul)", f"{kg_fat_sport:.2f} kg", help="Calculé uniquement sur l'activité physique.")
            
            # Colonne 3 : NOUVELLE (Calcul Complexe)
            k3.metric("🔥 Perte Réelle (Déficit)", f"{total_fat_loss_real:.2f} kg", delta="BMR + Sport - Repas", help="Prend en compte votre métabolisme et vos repas enregistrés.")
            
            st.divider()
            
            # --- RESTE DU DASHBOARD INITIAL (INCHANGÉ) ---
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Aujourd'hui", f"{int(my_df[my_df['date'].dt.date == date.today()]['calories'].sum())} kcal")
            c2.metric("🔥 Série Perso", f"{streak_user} Jours")
            c3.metric("🛡️ Série Équipe", f"{streak_team} Jours", "3 actifs min.")
            c4.metric("Trophées", f"{len(check_achievements(my_df))}")
            
            if not df_a.empty:
                all_totals = df_a.groupby('user')['calories'].sum()
                celebrations = []
                for u, cal in all_totals.items():
                    u_lvl, _, _ = get_level_progress(cal)
                    
                    # LOGIQUE CELEBRATION MISE A JOUR
                    if u_lvl >= 5:
                        u_title_cel = get_status_from_level(u_lvl)[0]
                        celebrations.append(f"🎖️ {get_user_badge(u, df_u)} est maintenant **{u_title_cel}** !")
                    
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
                    font_col = "white" if plotly_layout_dark else "black"
                    fig.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 100]), bgcolor='rgba(0,0,0,0)'), font=dict(size=10, color=font_col), paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=80, r=80, t=20, b=20), height=300)
                    st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})
                else: st.info("Pas assez de données")
            with c_r:
                st.subheader("🌍 Voyage")
                km = total_cal / 60
                target_label = "Vers l'infini"; target_km = 99999
                for dist, label in MILESTONES:
                    if km < dist: target_label = label; target_km = dist; break
                st.markdown(f"<div class='glass'>🏃‍♂️ <b>{int(km)} km</b> parcourus<br>Cap sur : <b>{target_label}</b> ({int(target_km - km)} km restants)</div>", unsafe_allow_html=True)
                st.progress(min(km/target_km, 1.0))

        with tabs[1]: # BALANCE
            st.header("⚖️ Suivi du Poids")
            st.caption("Suivez votre progression ici.")
            
            with st.form("weight_form"):
                w_date = st.date_input("Date de la pesée", date.today())
                w_val = st.number_input("Poids (kg)", 30.0, 200.0, float(w_curr), step=0.1)
                
                if st.form_submit_button("Enregistrer le poids"):
                    dt_w = datetime.combine(w_date, datetime.now().time())
                    new_w_row = pd.DataFrame([{"date": dt_w, "user": user, "poids": w_val}])
                    if save_weight(new_w_row):
                        st.success(f"Poids enregistré : {w_val} kg")
                        time.sleep(1); st.rerun()

            st.divider()
            st.subheader("Historique et Modification")
            if not my_bal.empty:
                df_bal_edit = my_bal.copy().sort_values(by='date', ascending=False)
                df_bal_edit.insert(0, "Supprimer", False)
                
                col_conf_bal = {
                    "Supprimer": st.column_config.CheckboxColumn("🗑️", default=False),
                    "date": st.column_config.DatetimeColumn("Date", format="D MMM HH:mm"),
                    "poids": st.column_config.NumberColumn("Poids (kg)", min_value=30.0, max_value=200.0, step=0.1)
                }
                
                edi_bal = st.data_editor(df_bal_edit, column_config=col_conf_bal, use_container_width=True, num_rows="dynamic", hide_index=True)
                
                if st.button("💾 Sauvegarder modifications balance"):
                    to_keep_bal = edi_bal[edi_bal['Supprimer'] == False].drop(columns=['Supprimer'])
                    to_keep_bal['date'] = pd.to_datetime(to_keep_bal['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
                    to_keep_bal['poids'] = pd.to_numeric(to_keep_bal['poids'])
                    other_users_bal = df_bal[df_bal['user'] != user]
                    final_bal = pd.concat([other_users_bal, to_keep_bal], ignore_index=True)
                    conn.update(worksheet="Balance", data=final_bal)
                    st.cache_data.clear()
                    st.success("Historique balance mis à jour !")
                    time.sleep(1); st.rerun()
            else:
                st.info("Aucune pesée enregistrée.")
        
        with tabs[2]: # BOUFFE
            st.header("🍔 Suivi Alimentaire (Est.)")
            st.caption("Une méthode simple basée sur le ressenti.")
            
            c_f1, c_f2 = st.columns([1, 2])
            with c_f1:
                with st.form("food_form"):
                    f_date = st.date_input("Date du repas", date.today())
                    f_time = st.time_input("Heure", datetime.now().time())
                    st.markdown("### Ressenti du repas")
                    f_level = st.slider("Quelle taille faisait ce repas ?", 1, 7, 4)
                    
                    st.markdown("##### 📏 Guide des portions :")
                    for i in range(1, 8):
                        st.markdown(f"<div style='font-size:0.8em; color:gray;'><b>Niveau {i}</b> : {FOOD_LABELS[i]} (~{FOOD_LEVELS[i]} kcal)</div>", unsafe_allow_html=True)
                    
                    est_cal = FOOD_LEVELS[f_level]; est_label = FOOD_LABELS[f_level]
                    
                    if st.form_submit_button("Enregistrer ce repas"):
                        dt_food = datetime.combine(f_date, f_time)
                        new_food = pd.DataFrame([{"date": dt_food, "user": user, "type_repas": est_label, "calorie_est": est_cal}])
                        if save_food(new_food): st.success(f"Repas ajouté : {est_label}"); time.sleep(1); st.rerun()
                
                st.markdown("---")
                if st.button("🚫 Enregistrer un JEÛNE (0 kcal)"):
                    dt_food = datetime.combine(date.today(), datetime.now().time())
                    new_food = pd.DataFrame([{"date": dt_food, "user": user, "type_repas": "🚫 JEÛNE TOTAL", "calorie_est": 0}])
                    if save_food(new_food): st.success("Jeûne enregistré ! Le déficit sera maximal."); time.sleep(1); st.rerun()

            with c_f2:
                st.subheader("Résumé Récent")
                if not my_food.empty:
                    my_food = safe_date_convert(my_food, 'date')
                    my_food = my_food.sort_values(by='date', ascending=False)
                    daily_food = my_food.copy()
                    daily_food['date_day'] = daily_food['date'].dt.date
                    df_food_chart = daily_food.groupby('date_day')['calorie_est'].sum().reset_index()
                    fig_food = px.bar(df_food_chart, x='date_day', y='calorie_est', title="Apport Calorique Quotidien", color_discrete_sequence=['#FFA500'])
                    font_col = "white" if plotly_layout_dark else "black"
                    plotly_grid_color = "rgba(255,255,255,0.2)" if plotly_layout_dark else "#e0e0e0"
                    fig_food.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color=font_col, xaxis=dict(showgrid=False, tickfont=dict(color=font_col)), yaxis=dict(showgrid=True, gridcolor=plotly_grid_color, tickfont=dict(color=font_col)))
                    st.plotly_chart(fig_food, use_container_width=True)
                else: st.info("Aucun repas enregistré pour le moment.")
            
            st.divider(); st.subheader("📜 Historique et Modification")
            if not my_food.empty:
                df_food_edit = my_food.copy(); df_food_edit.insert(0, "Supprimer", False)
                col_conf_food = {"Supprimer": st.column_config.CheckboxColumn("🗑️", default=False), "date": st.column_config.DatetimeColumn("Date", format="D MMM HH:mm"), "type_repas": st.column_config.TextColumn("Repas"), "calorie_est": st.column_config.NumberColumn("Kcal", min_value=0, max_value=5000)}
                edi_food = st.data_editor(df_food_edit, column_config=col_conf_food, use_container_width=True, num_rows="dynamic", hide_index=True)
                if st.button("💾 Sauvegarder modifications repas"):
                    to_keep_food = edi_food[edi_food['Supprimer'] == False].drop(columns=['Supprimer'])
                    to_keep_food['date'] = pd.to_datetime(to_keep_food['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
                    other_users_data = df_b[df_b['user'] != user]
                    final_df = pd.concat([other_users_data, to_keep_food], ignore_index=True)
                    conn.update(worksheet="Bouffe", data=final_df); st.cache_data.clear(); st.success("Historique repas mis à jour !"); time.sleep(1); st.rerun()

        with tabs[3]: # PARTAGE
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
                    st.markdown(f"""<div class='post-card'><div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>{get_user_badge(r['user'], df_u)}<span style='opacity:0.6; font-size:0.8em;'>{r['date']}</span></div><img src='{r['image']}' style='width:100%; border-radius:5px; margin-bottom:10px;'><p style='font-size:1.1em;'>{r['comment']}</p><hr style='border-color:#555;'><div style='display:flex; flex-wrap:wrap; align-items:center;'><span style='margin-right:10px; opacity:0.6; font-size:0.9em;'>Vu par :</span>{''.join([get_user_badge(v, df_u) for v in viewers if v])}</div></div>""", unsafe_allow_html=True)
            else: st.info("Aucun post récent. Soyez le premier !")

        with tabs[4]: # SEANCE
            st.subheader("Ajouter une séance")
            c1, c2 = st.columns(2)
            d = c1.date_input("Date", date.today())
            
            s = c1.selectbox("Sport", SPORTS_LIST)
            m = 0.0; dist = 0.0; steps = 0; input_type = "Durée" 
            if s in ["Course", "Natation","Vélo"]: input_type = c2.radio("Type d'objectif", ["Durée", "Distance"], horizontal=True)
            elif s == "Marche": input_type = c2.radio("Type d'objectif", ["Durée", "Pas","Distance"], horizontal=True)
            else: c2.info("⏱️ Objectif : Durée")
            if input_type == "Durée": m = c1.number_input("Durée (min)", 1, 300, 45)
            elif input_type == "Distance":
                default_dist = 5.0 if s == "Course" else 1.0
                dist = c1.number_input("Distance (km)", 0.1, 200.0, default_dist)
                speed = SPEED_MAP.get(s, 1.0)
                if speed > 0: m = (dist / speed) * 60
            elif input_type == "Pas": steps = c1.number_input("Nombre de pas", 100, 100000, 5000); m = steps / 100.0 
            if input_type != "Durée": c2.success(f"⏱️ Équivalent : {int(m)} min")
            
            intensity_factor = 1.0; intensite = c2.selectbox("Intensité", ["Légère (x0.8)", "Moyenne (x1.0)", "Élevée (x1.2)", "Maximale (x1.5)"], index=1)
            if "Légère" in intensite: intensity_factor = 0.8
            elif "Élevée" in intensite: intensity_factor = 1.2
            elif "Maximale" in intensite: intensity_factor = 1.5
            
            if st.button("Sauvegarder la séance", type="primary"):
                t = datetime.now().time()
                dt = datetime.combine(d, t)
                base_kcal = (calculate_bmr(w_curr, prof['h'], 25, prof['sex'])/24) * ((DNA_MAP.get(s,{}).get("Force",5) + DNA_MAP.get(s,{}).get("Endurance",5))/3) * (m/60) * intensity_factor
                epoc_bonus = base_kcal * EPOC_MAP.get(s, 0.05)
                # APPLICATION DU FACTEUR DE SECURITE
                total_kcal = (base_kcal + epoc_bonus) * SAFETY_FACTOR
                new_row = pd.DataFrame([{"date": dt, "user": user, "sport": s, "minutes": m, "calories": int(total_kcal), "distance": dist, "pas": steps}])
                
                if save_activity(new_row):
                    st.success(f"✅ +{int(total_kcal)} kcal")
                    if dist > 0: st.caption(f"Distance : {dist} km")
                    if steps > 0: st.caption(f"Pas : {steps}")
                    st.caption(f"Effort: {int(base_kcal)} + Afterburn: {int(epoc_bonus)}")
                    st_lottie(load_lottieurl(LOTTIE_SUCCESS), height=100); time.sleep(2); st.rerun()
            
            st.divider(); st.subheader("📜 Historique de vos séances")
            if not my_df.empty:
                df_display = my_df.copy(); df_display.insert(0, "Supprimer", False)
                col_conf = {"Supprimer": st.column_config.CheckboxColumn("🗑️", default=False), "distance": st.column_config.NumberColumn("Dist (km)", format="%.2f"), "pas": st.column_config.NumberColumn("Pas", format="%d"), "minutes": st.column_config.NumberColumn("Min", format="%d")}
                edi = st.data_editor(df_display, use_container_width=True, num_rows="dynamic", column_config=col_conf)
                if st.button("💾 Sauvegarder changements"):
                    to_keep = edi[edi['Supprimer'] == False].drop(columns=['Supprimer'])
                    to_keep['date'] = pd.to_datetime(to_keep['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
                    to_keep['calories'] = pd.to_numeric(to_keep['calories'])
                    if 'distance' in to_keep.columns: to_keep['distance'] = pd.to_numeric(to_keep['distance'])
                    if 'pas' in to_keep.columns: to_keep['pas'] = pd.to_numeric(to_keep['pas'])
                    conn.update(worksheet="Activites", data=pd.concat([df_a[df_a['user'] != user], to_keep], ignore_index=True))
                    st.cache_data.clear(); st.success("Mise à jour réussie !"); st.rerun()

        with tabs[5]: # BOSS
            curr_month_num = datetime.now().month
            boss_name, boss_max_hp, boss_img = BOSS_CALENDAR.get(curr_month_num, ("Monstre", 200000, ""))
            st.header(f"👹 BOSS DU MOIS : {boss_name.upper()}")
            df_month = df_a[df_a['date'].dt.strftime("%Y-%m") == datetime.now().strftime("%Y-%m")]
            dmg = df_month['calories'].sum(); pct_hp = max(0, (boss_max_hp - dmg) / boss_max_hp)
            c_img, c_stat = st.columns([1, 2]); c_img.image(boss_img, use_container_width=True)
            col = "#4CAF50" if pct_hp > 0.5 else ("#FF9800" if pct_hp > 0.2 else "#F44336")
            c_stat.markdown(f"""<div style="margin-bottom:5px;font-weight:bold;">PV Restants : {int(boss_max_hp - dmg)} / {boss_max_hp}</div><div class="boss-bar"><div class="boss-fill" style="width: {pct_hp*100}%; background-color: {col};"></div></div>""", unsafe_allow_html=True)
            if pct_hp <= 0: st.balloons(); st.success("🏆 LE BOSS EST VAINCU !")
            else: c_stat.info(f"Il reste {int(pct_hp*100)}% de vie.")
            c_stat.markdown("### ⚔️ Meilleurs Attaquants")
            if not df_month.empty:
                for i, (u, val) in enumerate(df_month.groupby("user")['calories'].sum().sort_values(ascending=False).head(5).items()): c_stat.markdown(f"**{i+1}. {get_user_badge(u, df_u)}** : {int(val)} dégâts", unsafe_allow_html=True)

        with tabs[6]: # DEFIS
            st.header("⚔️ Salle des Défis")
            st.subheader("🏆 Vos Victoires"); wins = 0
            if not df_d.empty and not df_a.empty:
                completed_challenges = df_d[(df_d['date_fin'] < date.today().strftime('%Y-%m-%d'))]
                for _, ch in completed_challenges.iterrows():
                    if user in str(ch['participants']):
                        # FIX: Filtrer par date de début du défi si elle existe, sinon prendre tout l'historique
                        start_d = pd.to_datetime(ch['date_debut']) if 'date_debut' in ch and pd.notna(ch['date_debut']) else pd.to_datetime('2000-01-01')
                        c_df = df_a[(df_a['date'] <= ch['date_fin']) & (df_a['date'] >= start_d) & (df_a['user'] == user)]
                        
                        if ch['sport_cible'] != "Tous les sports": c_df = c_df[c_df['sport'] == ch['sport_cible']]
                        val = 0
                        if "Calories" in ch['type']: val = c_df['calories'].sum()
                        elif "Durée" in ch['type']: val = c_df['minutes'].sum()
                        elif "Distance" in ch['type']: val = c_df.apply(lambda row: (row['minutes']/60) * SPEED_MAP.get(row['sport'], 0), axis=1).sum()
                        if val >= float(ch['objectif']): wins += 1
            if wins > 0: st.markdown(f"<div class='celeb-box' style='background:#FFD700; color:black;'>🥇 Vous avez remporté <b>{wins}</b> défis !</div>", unsafe_allow_html=True)
            else: st.caption("Gagnez des défis pour voir vos trophées ici !")
            st.divider()
            with st.expander("➕ Lancer un nouveau défi"):
                with st.form("new_def"):
                    dt = st.text_input("Nom"); type_def = st.selectbox("Cible", ["Calories (kcal)", "Durée (min)", "Distance (km)"]); sport_target = st.selectbox("Sport", ["Tous les sports"] + SPORTS_LIST); obj = st.number_input("Objectif", 10.0, 50000.0, 500.0); fin = st.date_input("Fin")
                    if st.form_submit_button("Créer"): create_challenge(dt, type_def, obj, sport_target, fin); st.success("Lancé !"); time.sleep(1); st.rerun()
            st.subheader("Défis en cours")
            if not df_d.empty:
                active_challenges = df_d[df_d['date_fin'] >= date.today().strftime('%Y-%m-%d')]
                for _, r in active_challenges.iterrows():
                    parts = r['participants'].split(','); unit = "kcal" if "Calories" in r['type'] else ("km" if "Distance" in r['type'] else "min")
                    
                    # FIX: Filtrer par date de début du défi
                    start_d = pd.to_datetime(r['date_debut']) if 'date_debut' in r and pd.notna(r['date_debut']) else pd.to_datetime('2000-01-01')
                    c_df = df_a[(df_a['date'] <= r['date_fin']) & (df_a['date'] >= start_d) & (df_a['user'].isin(parts))]
                    
                    if r['sport_cible'] != "Tous les sports": c_df = c_df[c_df['sport'] == r['sport_cible']]
                    prog = c_df.groupby('user')['calories'].sum() if "Calories" in r['type'] else (c_df.groupby('user')['minutes'].sum() if "Durée" in r['type'] else c_df.apply(lambda row: (row['minutes']/60) * SPEED_MAP.get(row['sport'], 0), axis=1).groupby(c_df['user']).sum())
                    prog = prog.reindex(parts, fill_value=0)
                    st.markdown(f"<div class='challenge-card'><h3>🏆 {r['titre']}</h3><p>Cible : <b>{int(r['objectif'])} {unit}</b> avant le {r['date_fin']}</p><p style='font-size:0.9em; opacity:0.7'>Créé par {get_user_badge(r['createur'], df_u)}</p></div>", unsafe_allow_html=True)
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

        with tabs[7]: # STATS
            if not my_df.empty:
                st.subheader("🏆 Records")
                max_c = my_df['calories'].max(); max_m = my_df['minutes'].max(); fav = my_df['sport'].mode()[0] if not my_df['sport'].mode().empty else "Aucun"
                tot_sess = len(my_df)
                st.markdown(f"""<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px;"><div class="stat-card"><div style="font-size: 2em;">🔥</div><div class="stat-val">{int(max_c)}</div><div class="stat-label">Record Calories</div></div><div class="stat-card"><div style="font-size: 2em;">⏱️</div><div class="stat-val">{int(max_m)} min</div><div class="stat-label">Record Durée</div></div><div class="stat-card"><div style="font-size: 2em;">❤️</div><div class="stat-val">{fav}</div><div class="stat-label">Sport Favori</div></div><div class="stat-card"><div style="font-size: 2em;">🏋️‍♂️</div><div class="stat-val">{tot_sess}</div><div class="stat-label">Total Sessions</div></div></div>""", unsafe_allow_html=True)
                with st.expander("🔥 Info Afterburn"): st.info("L'Afterburn (EPOC) est ajouté automatiquement à vos calories !")
                
                filter_option = st.selectbox("Période", ["Semaine", "Mois", "3 Mois", "Année", "Tout"])
                today = datetime.now(); start_date = None
                if filter_option == "Semaine": start_date = today - timedelta(days=7)
                elif filter_option == "Mois": start_date = today - timedelta(days=30)
                elif filter_option == "3 Mois": start_date = today - timedelta(days=90)
                elif filter_option == "Année": start_date = today - timedelta(days=365)
                
                c1, c2 = st.columns(2)
                
                # 1. Données réelles (Balance)
                df_w_chart = my_bal.copy()
                # FIX: Trier par date pour éviter que le graphe ne boucle sur lui-même
                df_w_chart = df_w_chart.sort_values(by='date')
                
                if start_date: df_w_chart = df_w_chart[df_w_chart['date'] >= start_date]
                
                target_w = float(prof.get('w_obj', 65.0))
                initial_w_profile = float(prof.get('w_init', 70.0))
                
                fig_w = go.Figure()
                
                if not df_w_chart.empty:
                    fig_w.add_trace(go.Scatter(x=df_w_chart['date'], y=df_w_chart['poids'], mode='lines+markers', name='Poids Réel (Balance)', line=dict(color='#00BFFF', width=3)))
                
                fig_w.add_hline(y=target_w, line_dash="dash", line_color="#00CC96", annotation_text=f"Obj: {target_w} kg", annotation_position="top right")

                # 2. Données Théoriques
                first_sport = my_df['date'].min()
                first_food = my_food['date'].min() if not my_food.empty else first_sport
                global_start = min(first_sport, first_food).date()
                all_days = pd.date_range(start=global_start, end=date.today())
                
                df_calc = pd.DataFrame({'day': all_days})
                df_calc['day'] = df_calc['day'].dt.date 
                
                sport_daily = my_df.copy(); sport_daily['day'] = sport_daily['date'].dt.date
                sport_sum = sport_daily.groupby('day')['calories'].sum().reset_index()
                
                food_sum = pd.DataFrame(columns=['day', 'calorie_est', 'is_logged'])
                if not my_food.empty:
                    food_daily = my_food.copy(); food_daily['day'] = food_daily['date'].dt.date
                    food_sum = food_daily.groupby('day')['calorie_est'].sum().reset_index()
                    food_sum['is_logged'] = 1 
                
                df_calc = df_calc.merge(sport_sum, on='day', how='left').fillna(0)
                df_calc = df_calc.merge(food_sum, on='day', how='left').fillna(0)
                
                user_bmr = calculate_bmr(w_curr, prof['h'], calculate_age(prof['dob']), prof['sex'])
                
                def calc_deficit(row):
                    if row['is_logged'] == 1:
                        return (user_bmr + row['calories']) - row['calorie_est']
                    else:
                        return row['calories']
                
                df_calc['daily_deficit'] = df_calc.apply(calc_deficit, axis=1)
                df_calc['cum_deficit'] = df_calc['daily_deficit'].cumsum()
                df_calc['theo_weight'] = initial_w_profile - (df_calc['cum_deficit'] / 7700)
                
                if start_date: df_theo_display = df_calc[df_calc['day'] >= start_date.date()]
                else: df_theo_display = df_calc

                if not df_theo_display.empty:
                    fig_w.add_trace(go.Scatter(x=df_theo_display['day'], y=df_theo_display['theo_weight'], mode='lines', name='Théorique (Bilan Cal.)', line=dict(dash='dot', color='#FFA500')))
                    
                    if not df_w_chart.empty:
                        last_real = df_w_chart.sort_values('date').iloc[-1]['poids']
                        last_theo = df_calc.iloc[-1]['theo_weight']
                        diff = last_real - last_theo
                        if abs(diff) > 2.0: 
                             st.info(f"ℹ️ **Écart de {diff:.1f} kg** entre réalité et théorie.")

                vals = []
                if not df_w_chart.empty: vals.extend(df_w_chart['poids'].tolist())
                if not df_theo_display.empty: vals.extend(df_theo_display['theo_weight'].tolist())
                if vals:
                    min_y, max_y = min(vals), max(vals)
                    fig_w.update_yaxes(range=[min_y - 2, max_y + 2])

                fig_w.update_layout(title="Évolution du Poids (Réel vs Théorique)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                    font_color=("white" if current_theme=="Sombre" else "black"),
                                    xaxis=dict(showgrid=True, gridcolor=("rgba(255,255,255,0.2)" if current_theme=="Sombre" else "#e0e0e0")), 
                                    yaxis=dict(showgrid=True, gridcolor=("rgba(255,255,255,0.2)" if current_theme=="Sombre" else "#e0e0e0")),
                                    legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5))
                
                c1.plotly_chart(fig_w, use_container_width=True)
                
                # --- CORRECTION GRAPHIQUE BMR/SPORT/BOUFFE (Tab 7) ---
                if start_date: s_d = start_date.date()
                else:
                    d1 = my_df['date'].min() if not my_df.empty else datetime.now()
                    d2 = my_food['date'].min() if not my_food.empty else datetime.now()
                    s_d = min(d1, d2).date()
                
                e_d = date.today()
                
                # Création du calendrier complet (Master)
                full_dates = pd.date_range(start=s_d, end=e_d)
                df_master = pd.DataFrame({'date_day': full_dates.date})

                df_sport_agg = pd.DataFrame(columns=['date_day', 'calories'])
                if not my_df.empty:
                    temp_sport = my_df.copy(); temp_sport['date_day'] = temp_sport['date'].dt.date
                    df_sport_agg = temp_sport.groupby('date_day')['calories'].sum().reset_index()
                
                df_food_agg = pd.DataFrame(columns=['date_day', 'calorie_est'])
                if not my_food.empty:
                    temp_food = my_food.copy(); temp_food['date_day'] = temp_food['date'].dt.date
                    df_food_agg = temp_food.groupby('date_day')['calorie_est'].sum().reset_index()

                # Fusionner tout sur le calendrier maître
                df_master = df_master.merge(df_sport_agg, on='date_day', how='left')
                df_master = df_master.merge(df_food_agg, on='date_day', how='left')
                df_master = df_master.fillna(0)

                bmr_daily = int(user_bmr)
                
                fig_bar = go.Figure()
                # BMR (Gris)
                fig_bar.add_trace(go.Bar(x=df_master['date_day'], y=[bmr_daily] * len(df_master), name='Métabolisme (BMR)', marker_color='#C0C0C0'))
                # Sport (Bleu)
                fig_bar.add_trace(go.Bar(x=df_master['date_day'], y=df_master['calories'], name='Sport', marker_color='#00BFFF'))
                # Bouffe (Ligne Rouge)
                fig_bar.add_trace(go.Scatter(x=df_master['date_day'], y=df_master['calorie_est'], mode='lines+markers', name='Apport Bouffe', line=dict(color='red', width=3)))
                
                fig_bar.update_layout(
                    barmode='stack', 
                    title="Dépense Totale (BMR+Sport) vs Apport (Rouge)", 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)', 
                    font_color=("white" if current_theme=="Sombre" else "black"), 
                    bargap=0.1,
                    xaxis=dict(showgrid=True, gridcolor=("rgba(255,255,255,0.2)" if current_theme=="Sombre" else "#e0e0e0")), 
                    yaxis=dict(showgrid=True, gridcolor=("rgba(255,255,255,0.2)" if current_theme=="Sombre" else "#e0e0e0")),
                    legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)
                )
                c2.plotly_chart(fig_bar, use_container_width=True, config={'staticPlot': True})

        with tabs[8]: # CLASSEMENT
            st.header("🏛️ Hall of Fame")
            if not df_a.empty:
                try:
                    df_a_numeric = df_a.copy()
                    mc_idx = df_a_numeric['calories'].idxmax(); mm_idx = df_a_numeric['minutes'].idxmax()
                    mc = df_a_numeric.loc[mc_idx]; mm = df_a_numeric.loc[mm_idx]
                    c1, c2 = st.columns(2)
                    c1.markdown(f"<div class='glass'><h3>🔥 Machine</h3><p><b>{get_user_badge(mc['user'], df_u)}</b> {int(mc['calories'])} kcal</p></div>", unsafe_allow_html=True)
                    c2.markdown(f"<div class='glass'><h3>⏳ Endurance</h3><p><b>{get_user_badge(mm['user'], df_u)}</b> {int(mm['minutes'])} min</p></div>", unsafe_allow_html=True)
                except Exception as e: st.error(f"Erreur classement: {e}")
                st.divider(); st.subheader("🏆 Semaine")
                w_df = df_a[df_a['date'] >= (pd.Timestamp.now() - pd.Timedelta(days=7))]
                if not w_df.empty:
                    for i, (u, c) in enumerate(w_df.groupby("user")['calories'].sum().sort_values(ascending=False).items()): st.markdown(f"**{i+1}. {get_user_badge(u, df_u)}** - {int(c)} kcal", unsafe_allow_html=True)

        with tabs[9]: # PROFIL
            st.subheader("📝 Profil")
            with st.form("prof"):
                c1, c2 = st.columns(2)
                new_pseudo = c1.text_input("Pseudo (Nom d'utilisateur)", value=user)
                try: h_val = int(float(prof.get('h', 175)))
                except: h_val = 175
                try: w_obj_val = float(prof.get('w_obj', 65.0))
                except: w_obj_val = 65.0
                try: w_init_val = float(prof.get('w_init', 70.0))
                except: w_init_val = 70.0
                nd = c2.date_input("Naissance", datetime.strptime(prof.get('dob','2000-01-01'),"%Y-%m-%d")); ns = c1.selectbox("Sexe",["Homme","Femme"],0 if prof.get('sex')=="Homme" else 1)
                nh = c2.number_input("Taille",100,250, h_val); nw = c1.number_input("Obj Poids",40.0,150.0, w_obj_val)
                ni = c1.number_input("Poids de départ (kg)", 30.0, 200.0, w_init_val)
                na = c2.selectbox("Activité",ACTIVITY_OPTS)
                current_theme_idx = 0 if prof.get('theme', 'Sombre') == "Sombre" else 1
                nt = c1.selectbox("Thème (Apparence)", ["Sombre", "Clair"], index=current_theme_idx)
                n_av = st.file_uploader("Avatar", type=['png','jpg']); np = st.text_input("Nouveau PIN", type="password", max_chars=4)
                if st.form_submit_button("Sauvegarder"):
                    if new_pseudo != user:
                        res = change_username(user, new_pseudo)
                        if res == "OK": st.session_state.user = new_pseudo; user = new_pseudo; st.success("Pseudo changé !")
                        else: st.error(f"Erreur changement pseudo: {res}")
                    fav = prof.get('avatar', ""); 
                    if n_av: fav = process_avatar(n_av)
                    prof.update({'dob':str(nd), 'sex':ns, 'h':int(nh), 'w_obj':float(nw), 'w_init': float(ni), 'act':na, 'avatar':fav, 'theme': nt})
                    current_pin = row['pin']
                    refresh_df = conn.read(worksheet="Profils", ttl=0)
                    if not refresh_df.empty and user in refresh_df['user'].values: current_pin = refresh_df[refresh_df['user'] == user].iloc[0]['pin']
                    ps = current_pin
                    if np and len(np)==4: ps = hash_pin(np)
                    save_user(user, ps, prof); st.success("Mis à jour !"); st.rerun()
            st.divider()
            if st.button("Supprimer mon compte"): 
                if delete_current_user(): st.session_state.user = None; st.rerun()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Erreur fatale capturée : {e}")
        st.markdown(f"Une erreur est survenue: {e}")
