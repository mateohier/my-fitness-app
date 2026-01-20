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
BACKGROUND_URL = "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=1470&auto=format&fit=crop"

# --- CALENDRIER DES BOSS ---
BOSS_CALENDAR = {
    1: ("Yéti des Glaces", 150000, "https://images.unsplash.com/photo-1546519638-68e109498ee3?q=80&w=1000"),
    2: ("Golem de Pierre", 160000, "https://images.unsplash.com/photo-1617374028688-66236b280388?q=80&w=1000"),
    3: ("Hydre des Marais", 180000, "https://images.unsplash.com/photo-1616091216791-a5360b5fc78a?q=80&w=1000"),
    4: ("Titan Colossal", 200000, "https://images.unsplash.com/photo-1590845947698-8924d7409b56?q=80&w=1000"),
    5: ("Reine des Enfers", 220000, "https://images.unsplash.com/photo-1627449557342-6323136209b9?q=80&w=1000"),
    6: ("Dragon Solaire", 250000, "https://images.unsplash.com/photo-1594956108155-2272e5052994?q=80&w=1000"),
    7: ("Kraken des Abysses", 250000, "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=1000"),
    8: ("Seigneur Volcanique", 240000, "https://images.unsplash.com/photo-1469598614039-ccfeb0a21111?q=80&w=1000"),
    9: ("Chevalier Noir", 210000, "https://images.unsplash.com/photo-1519074069444-1ba4fff66d16?q=80&w=1000"),
    10: ("Spectre d'Halloween", 200000, "https://images.unsplash.com/photo-1509557965875-b88c97052f0e?q=80&w=1000"),
    11: ("Cyborg du Futur", 190000, "https://images.unsplash.com/photo-1535378437323-955a6d73a36c?q=80&w=1000"),
    12: ("Père Fouettard Géant", 180000, "https://images.unsplash.com/photo-1543589077-47d81606c1bf?q=80&w=1000")
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
        if not df.empty and u in df['user'].values: df.loc[df['user'] == u, 'json_data'] = j
        else: df = pd.concat([df, pd.DataFrame([{"user": u, "pin": p, "json_data": j}])], ignore_index=True)
        conn.update(worksheet="Profils", data=df)
        st.cache_data.clear()
        return True
    except: return False

def delete_current_user():
    """Supprime l'utilisateur, ses activités et le retire des défis"""
    try:
        user = st.session_state.user
        
        # 1. Lire toutes les données
        df_u = conn.read(worksheet="Profils", ttl=0)
        df_a = conn.read(worksheet="Activites", ttl=0)
        df_d = conn.read(worksheet="Defis", ttl=0)
        
        # 2. Supprimer de Profils et Activites
        df_u = df_u[df_u['user'] != user]
        df_a = df_a[df_a['user'] != user]
        
        # 3. Retirer des participants aux défis
        def remove_participant(participants_str):
            parts = str(participants_str).split(',')
            if user in parts:
                parts.remove(user)
            return ",".join(parts)
            
        df_d['participants'] = df_d['participants'].apply(remove_participant)
        
        # 4. Sauvegarder
        conn.update(worksheet="Profils", data=df_u)
        conn.update(worksheet="Activites", data=df_a)
        conn.update(worksheet="Defis", data=df_d)
        
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erreur suppression : {e}")
        return False

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

ACTIVITY_OPTS = ["Sédentaire (1.2)", "Légèrement actif (1.375)", "Actif (1.55)", "Très actif (1.725)"]

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
        c2.metric("Total", f"{int(total_cal)} kcal")
        c3.metric("Poids", f"{w_curr} kg")
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
                st.plotly_chart(fig, use_container_width=True)
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

    with tabs[1]: # BOSS AUTOMATIQUE
        curr_month_num = datetime.now().month
        boss_name, boss_max_hp, boss_img = BOSS_CALENDAR.get(curr_month_num, ("Monstre", 200000, ""))
        
        st.header(f"👹 BOSS DU MOIS : {boss_name.upper()}")
        
        curr_month_str = datetime.now().strftime("%Y-%m")
        df_a['month'] = df_a['date'].dt.strftime("%Y-%m")
        df_month = df_a[df_a['month'] == curr_month_str]
        
        dmg = df_month['calories'].sum()
        pct_hp = max(0, (boss_max_hp - dmg) / boss_max_hp)
        
        c_img, c_stat = st.columns([1, 2])
        with c_img:
            st.image(boss_img, use_container_width=True)
        with c_stat:
            col = "#4CAF50" if pct_hp > 0.5 else ("#FF9800" if pct_hp > 0.2 else "#F44336")
            st.markdown(f"""
            <div style="margin-bottom:5px; color:white; font-size:1.2em; font-weight:bold;">
                PV Restants : {int(boss_max_hp - dmg)} / {boss_max_hp}
            </div>
            <div class="boss-bar">
                <div class="boss-fill" style="width: {pct_hp*100}%; background-color: {col};"></div>
            </div>
            """, unsafe_allow_html=True)
            
            if pct_hp <= 0:
                st.balloons()
                st.success("🏆 LE BOSS EST VAINCU ! Bravo à toute l'équipe !")
            else:
                st.info(f"L'objectif est collectif ! Il reste {int(pct_hp*100)}% de vie.")
                
            st.markdown("### ⚔️ Meilleurs Attaquants (Top DPS)")
            if not df_month.empty:
                dps = df_month.groupby("user")['calories'].sum().sort_values(ascending=False).head(5)
                for i, (u, val) in enumerate(dps.items()):
                    st.write(f"**{i+1}. {u}** : {int(val)} dégâts")

    with tabs[2]: # DEFIS DETAILLES
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
                
                # Calcul Stats pour tous les participants
                c_df = df_a[(df_a['date'] <= r['date_fin']) & (df_a['user'].isin(parts))]
                if r['sport_cible'] != "Tous les sports": c_df = c_df[c_df['sport'] == r['sport_cible']]

                prog = pd.Series(dtype=float)
                if "Calories" in r['type']: prog = c_df.groupby('user')['calories'].sum()
                elif "Durée" in r['type']: prog = c_df.groupby('user')['minutes'].sum()
                elif "Distance" in r['type']:
                    c_df['km_est'] = c_df.apply(lambda row: (row['minutes']/60) * SPEED_MAP.get(row['sport'], 0), axis=1)
                    prog = c_df.groupby('user')['km_est'].sum()
                
                # S'assurer que tous les participants sont dans la série, même avec 0
                prog = prog.reindex(parts, fill_value=0)

                st.markdown(f"""
                <div class='challenge-card'>
                    <h3>🏆 {r['titre']}</h3>
                    <p>Cible : <b>{int(r['objectif'])} {unit}</b> ({s_txt}) avant le {r['date_fin']}</p>
                    <p style='font-size:0.9em; color:#aaa'>Créé par {r['createur']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col_act, col_list = st.columns([1, 2])
                with col_act:
                    if user not in parts:
                        if st.button(f"Rejoindre l'équipe", key=r['id']): join_challenge(r['id']); st.rerun()
                    else: st.write("✅ Tu participes")
                with col_list:
                    # Affichage liste complète
                    st.write("**Classement :**")
                    sorted_prog = prog.sort_values(ascending=False)
                    for u, val in sorted_prog.items():
                        pct = min(val/float(r['objectif']), 1.0)
                        st.write(f"**{u}** : {int(val)} {unit} ({int(pct*100)}%)")
                        st.progress(pct)
                st.divider()
        else: st.info("Aucun défi.")

    with tabs[3]: # STATS & RECORDS
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
            
            c1, c2 = st.columns(2)
            c1.plotly_chart(px.line(my_df, x='date', y='poids', title="Poids"), use_container_width=True)
            c2.plotly_chart(px.bar(my_df, x='date', y='calories', title="Calories"), use_container_width=True)
            
            hm_data = my_df.groupby(my_df['date'].dt.date)['minutes'].sum().reset_index()
            hm_data['date'] = pd.to_datetime(hm_data['date'])
            hm_data['week'] = hm_data['date'].dt.isocalendar().week
            hm_data['day'] = hm_data['date'].dt.dayofweek
            fig_hm = go.Figure(go.Heatmap(x=hm_data['week'], y=hm_data['day'], z=hm_data['minutes'], colorscale='Greens', showscale=False))
            fig_hm.update_layout(height=150, margin=dict(t=20,b=20), yaxis=dict(ticktext=['Lun','','','','','','Dim'], tickvals=[0,1,2,3,4,5,6]), title="Régularité (Heatmap)")
            st.plotly_chart(fig_hm, use_container_width=True)
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

    with tabs[5]: # PROFIL & SUPPRESSION
        with st.form("prof"):
            nh = st.number_input("Taille (cm)", 100, 250, int(prof['h']))
            nw = st.number_input("Objectif Poids (kg)", 40.0, 150.0, float(prof['w_obj']))
            if st.form_submit_button("Mettre à jour"):
                prof['h']=int(nh)
                prof['w_obj']=float(nw)
                save_user(user, row['pin'], prof)
                st.success("Profil mis à jour !")
                time.sleep(1); st.rerun()
        
        st.subheader("Editer Historique")
        if not my_df.empty:
            edi = st.data_editor(my_df, use_container_width=True, num_rows="dynamic")
            if st.button("Sauvegarder Modifs"):
                df_others = df_a[df_a['user'] != user]
                edi['date'] = pd.to_datetime(edi['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
                edi['poids'] = pd.to_numeric(edi['poids'])
                edi['calories'] = pd.to_numeric(edi['calories'])
                conn.update(worksheet="Activites", data=pd.concat([df_others, edi], ignore_index=True))
                st.cache_data.clear(); st.success("OK"); st.rerun()
        
        st.divider()
        st.error("⚠️ Zone de Danger")
        if st.button("Supprimer mon compte définitivement"):
            st.session_state['confirm_delete'] = True
            
        if st.session_state.get('confirm_delete'):
            st.warning("Êtes-vous sûr ? Cette action est irréversible.")
            if st.button("Confirmer la suppression"):
                if delete_current_user():
                    st.session_state.user = None
                    st.success("Compte supprimé.")
                    time.sleep(1)
                    st.rerun()

    with tabs[6]: # TOP
        if not df_a.empty:
            w_df = df_a[df_a['date'] >= (pd.Timestamp.now() - pd.Timedelta(days=7))]
            top = w_df.groupby("user")['calories'].sum().sort_values(ascending=False)
            for i, (u, c) in enumerate(top.items()):
                st.markdown(f"### {i+1}. {u} - {int(c)} kcal")
