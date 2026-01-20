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

# URLs Animations & Images
LOTTIE_SUCCESS = "https://assets5.lottiefiles.com/packages/lf20_u4yrau.json"
# Image de fond générale (Remplace par ton lien RAW GitHub si tu veux)
BACKGROUND_URL = "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=1470&auto=format&fit=crop"
# Image Anatomique (Silhouette Humaine)
ANATOMY_BG = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Human_body_front_and_side_schematics.svg/800px-Human_body_front_and_side_schematics.svg.png"

# --- MAPPINGS (ADN & MUSCLES) ---
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
    "Pilates":     {"Force": 4, "Endurance": 3, "Agilité": 8, "Mental": 6}
}

MUSCLE_MAP = {
    "Musculation": {"Bras": 8, "Pecs": 8, "Dos": 8, "Cuisses": 6, "Cardio": 2},
    "Course": {"Cuisses": 10, "Cardio": 9, "Mollets": 7},
    "Vélo": {"Cuisses": 9, "Cardio": 8, "Mollets": 9},
    "Natation": {"Dos": 10, "Bras": 9, "Cardio": 8, "Cuisses": 6, "Pecs": 5},
    "Crossfit": {"Bras": 8, "Cuisses": 8, "Cardio": 9, "Pecs": 7, "Dos": 7, "Abdos": 8},
    "Fitness": {"Cardio": 8, "Cuisses": 6, "Bras": 5, "Abdos": 7},
    "Boxe": {"Bras": 9, "Cardio": 10, "Dos": 6, "Cuisses": 7, "Abdos": 8},
    "Yoga": {"Dos": 7, "Abdos": 6, "Cuisses": 5},
    "Escalade": {"Bras": 10, "Dos": 9, "Cuisses": 7, "Abdos": 8},
    "Tennis": {"Bras": 7, "Cuisses": 8, "Cardio": 8},
    "Football": {"Cuisses": 9, "Cardio": 9, "Abdos": 5},
    "Marche": {"Cardio": 4, "Cuisses": 5},
    "Pilates": {"Abdos": 10, "Dos": 7, "Cuisses": 5},
    "Danse": {"Cuisses": 8, "Cardio": 7, "Abdos": 6}
}
SPORTS_LIST = sorted(list(MUSCLE_MAP.keys()))

# Coordonnées Anatomiques (X, Y) pour l'image de fond
BODY_COORDS = {
    "Cardio": (0, 8.5),     # Coeur/Tête
    "Pecs": (0, 7.2),       # Poitrine
    "Abdos": (0, 5.8),      # Ventre
    "Bras": (1.8, 6.5),     # Bras (Sera dupliqué G/D)
    "Dos": (0, 7.5),        # Haut du dos
    "Cuisses": (0.8, 4.0),  # Cuisses (Sera dupliqué G/D)
    "Mollets": (0.9, 1.5),  # Mollets (Sera dupliqué G/D)
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
    factor = 150 # Difficulté
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
        if df_d.empty: df_d = pd.DataFrame(columns=["id", "titre", "type", "objectif", "createur", "participants", "date_fin", "statut"])
            
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

def create_challenge(titre, type_def, obj, fin):
    try:
        df = conn.read(worksheet="Defis", ttl=0)
        new = pd.DataFrame([{
            "id": str(uuid.uuid4()), "titre": titre, "type": type_def, 
            "objectif": float(obj), "createur": st.session_state.user, 
            "participants": st.session_state.user, "date_fin": str(fin), "statut": "Actif"
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
    </style>
""", unsafe_allow_html=True)

# --- 5. LOGIQUE ---
df_u, df_a, df_d = get_data()

ACTIVITY_OPTS = ["Sédentaire (1.2)", "Légèrement actif (1.375)", "Actif (1.55)", "Très actif (1.725)"]

# SIDEBAR LOGIN
if not st.session_state.user:
    st.sidebar.title("🔥 Connexion")
    menu = st.sidebar.selectbox("Menu", ["Connexion", "Créer un compte"])
    u_input = st.sidebar.text_input("Pseudo").strip().lower()
    p_input = st.sidebar.text_input("PIN (4 chiffres)", type="password")
    
    if menu == "Connexion":
        if st.sidebar.button("Se connecter"):
            if not df_u.empty and u_input in df_u['user'].values:
                if df_u[df_u['user']==u_input].iloc[0]['pin'] == hash_pin(p_input):
                    st.session_state.user = u_input
                    st.rerun()
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
                    st.sidebar.success("Compte créé ! Connecte-toi.")
                    time.sleep(1)
                    st.rerun()
else:
    # --- USER LOGGED IN ---
    user = st.session_state.user
    st.sidebar.markdown(f"👤 **{user.capitalize()}**")
    if st.sidebar.button("Déconnexion"): st.session_state.user = None; st.rerun()
    
    # LOAD USER DATA
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

    # TABS
    tabs = st.tabs(["🏠 Dashboard", "🩻 Anatomie", "⚔️ Défis", "📈 Stats", "➕ Séance", "⚙️ Profil", "🏆 Top"])

    with tabs[0]: # DASHBOARD
        st.markdown(f"<div class='quote-box'>{random.choice(['Pain is fuel.', 'Go hard or go home.', 'Tu es une machine.'])}</div>", unsafe_allow_html=True)
        
        # XP
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

    with tabs[1]: # ANATOMIE REALISTE
        st.header("🩻 Carte Corporelle (7 jours)")
        # Calcul 7 jours
        m_scores = {}
        recent = my_df[my_df['date'] >= (pd.Timestamp.now() - pd.Timedelta(days=7))]
        for _, r in recent.iterrows():
            imps = MUSCLE_MAP.get(r['sport'], {"Cardio": 5})
            h = r['minutes'] / 60
            for m, s in imps.items(): m_scores[m] = m_scores.get(m, 0) + (s * h)
            
        if m_scores:
            x, y, s, c, t = [], [], [], [], []
            for m, score in m_scores.items():
                if m in BODY_COORDS:
                    bx, by = BODY_COORDS[m]
                    # Duplication symétrique pour membres
                    if m in ["Bras", "Cuisses", "Mollets"]:
                        x.extend([bx, -bx]); y.extend([by, by])
                        s.extend([score*8, score*8]); c.extend([score, score])
                        t.extend([m, m])
                    else:
                        x.append(bx); y.append(by)
                        s.append(score*10); c.append(score); t.append(m)
            
            fig = go.Figure()
            # Image Anatomique en Fond
            fig.add_layout_image(dict(
                source=ANATOMY_BG,
                xref="x", yref="y",
                x=-4, y=10.5, sizex=8, sizey=11,
                opacity=0.6, layer="below"
            ))
            # Heatmap Points
            fig.add_trace(go.Scatter(
                x=x, y=y, mode='markers', text=t,
                marker=dict(size=s, color=c, colorscale='Reds', opacity=0.8, showscale=False),
                hovertemplate="<b>%{text}</b><br>Intensité: %{marker.color:.1f}<extra></extra>"
            ))
            fig.update_layout(
                width=400, height=600,
                xaxis=dict(range=[-3, 3], visible=False),
                yaxis=dict(range=[0, 10], visible=False),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=0, b=0)
            )
            c1, c2 = st.columns([1, 2])
            with c1: st.plotly_chart(fig, use_container_width=True)
            with c2: 
                st.write("### Top Muscles")
                for m, sc in sorted(m_scores.items(), key=lambda x:x[1], reverse=True)[:5]:
                    st.progress(min(sc/50, 1.0), text=f"{m}")
        else: st.info("Fais du sport cette semaine pour voir l'anatomie !")

    with tabs[2]: # DEFIS
        st.header("⚔️ Défis de Groupe")
        
        # Création
        with st.expander("Créer un nouveau défi"):
            with st.form("new_def"):
                dt = st.text_input("Titre du défi (ex: 'Marathon de Noël')")
                typ = st.selectbox("Type", ["Calories", "Minutes", "Sport"])
                obj = st.number_input("Objectif (Total à atteindre)", 100, 50000, 1000)
                fin = st.date_input("Date de fin")
                if st.form_submit_button("Lancer le défi 🔥"):
                    create_challenge(dt, typ, obj, fin)
                    st.success("Défi créé !"); time.sleep(1); st.rerun()
        
        # Liste
        st.subheader("Défis en cours")
        if not df_d.empty:
            active = df_d[df_d['statut'] == 'Actif']
            for _, r in active.iterrows():
                parts = r['participants'].split(',')
                my_contribution = 0
                
                # Calcul contribution
                c_df = df_a[(df_a['date'] <= r['date_fin']) & (df_a['user'].isin(parts))]
                if r['type'] == 'Calories': prog = c_df.groupby('user')['calories'].sum()
                elif r['type'] == 'Minutes': prog = c_df.groupby('user')['minutes'].sum()
                else: prog = c_df[c_df['sport']==r['type']].groupby('user')['minutes'].sum() # Si type est un sport
                
                # Affichage Card
                with st.container():
                    st.markdown(f"<div class='glass'><h4>{r['titre']}</h4>Objectif: {r['objectif']} {r['type']} <br> Fin: {r['date_fin']}</div>", unsafe_allow_html=True)
                    
                    # Bouton rejoindre
                    if user not in parts:
                        if st.button(f"Rejoindre", key=r['id']): join_challenge(r['id']); st.rerun()
                    
                    # Leaderboard interne
                    if not prog.empty:
                        st.caption("Classement :")
                        for u, val in prog.sort_values(ascending=False).items():
                            st.write(f"{'👑' if val>=float(r['objectif']) else '🏃'} **{u}** : {int(val)} / {int(r['objectif'])}")
                            st.progress(min(val/float(r['objectif']), 1.0))
                    st.divider()
        else: st.info("Aucun défi actif.")

    with tabs[3]: # STATS
        if not my_df.empty:
            c1, c2 = st.columns(2)
            c1.plotly_chart(px.line(my_df, x='date', y='poids', title="Poids"), use_container_width=True)
            c2.plotly_chart(px.bar(my_df, x='date', y='calories', title="Calories"), use_container_width=True)
            
            # Heatmap
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

    with tabs[5]: # PROFIL
        with st.form("prof"):
            # FIX IMPORTANT : Forcer les floats et ints pour éviter l'erreur MixedTypes
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

    with tabs[6]: # TOP
        if not df_a.empty:
            w_df = df_a[df_a['date'] >= (pd.Timestamp.now() - pd.Timedelta(days=7))]
            top = w_df.groupby("user")['calories'].sum().sort_values(ascending=False)
            for i, (u, c) in enumerate(top.items()):
                st.markdown(f"### {i+1}. {u} - {int(c)} kcal")
