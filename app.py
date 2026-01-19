import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from github import Github
from datetime import date, datetime, timedelta
from io import StringIO
import hashlib

# =======================
# 1. CONFIGURATION PAGE
# =======================
st.set_page_config(page_title="Fitness Gamified Pro", layout="wide")

# =======================
# 2. STYLE & BACKGROUND
# =======================
def add_bg_from_github():
    img_url = "https://raw.githubusercontent.com/mateohier/my-fitness-app/main/AAAAAAAAAAAAAAAA.png"
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("{img_url}");
            background-attachment: fixed;
            background-size: cover;
            background-position: center;
        }}
        [data-testid="stSidebar"], .stTabs {{
            background-color: rgba(0,0,0,0.65);
            padding: 20px;
            border-radius: 15px;
            backdrop-filter: blur(8px);
        }}
        h1, h2, h3, p, label, .stMarkdown {{
            color: white !important;
        }}
        .stButton>button {{
            background-color: #1E88E5;
            color: white;
            border-radius: 10px;
            border: none;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

add_bg_from_github()

# =======================
# 3. GITHUB CONFIG
# =======================
try:
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo(st.secrets["REPO_NAME"])
except Exception:
    st.error("⚠️ Erreur GitHub : vérifie les secrets.")
    st.stop()

# =======================
# 4. OUTILS CLOUD
# =======================
def save_file(path, content):
    try:
        f = repo.get_contents(path)
        repo.update_file(f.path, f"MAJ {path}", content, f.sha)
    except:
        repo.create_file(path, f"Création {path}", content)

def load_file(path):
    try:
        return repo.get_contents(path).decoded_content.decode()
    except:
        return None

# =======================
# 5. SÉCURITÉ PIN
# =======================
def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()

# =======================
# 6. RANG
# =======================
def get_rank(total):
    if total < 5_000: return "Débutant 🥚", 5_000, "Bronze", "Chaque effort compte."
    if total < 15_000: return "Actif 🐣", 15_000, "Argent", "Bon rythme !"
    if total < 30_000: return "Sportif 🏃", 30_000, "Or", "Très solide !"
    if total < 60_000: return "Athlète 🏆", 60_000, "Platine", "Niveau élite."
    return "Légende 🔥", 1_000_000, "Diamant", "Intouchable."

# =======================
# 7. STATS GLOBALES
# =======================
def get_global_stats():
    data = []
    try:
        for f in repo.get_contents("user_data"):
            if f.name.endswith(".csv"):
                user = f.name.replace(".csv", "")
                df = pd.read_csv(StringIO(repo.get_contents(f.path).decoded_content.decode()))
                if not df.empty:
                    df["user"] = user
                    data.append(df)
    except:
        return None
    return pd.concat(data, ignore_index=True) if data else None

# =======================
# 8. AUTHENTIFICATION
# =======================
st.sidebar.title("🔐 Profil")
menu = st.sidebar.radio("Menu", ["Connexion", "Créer un compte"])
user = None

if menu == "Créer un compte":
    u = st.sidebar.text_input("Nom").strip().lower()
    p = st.sidebar.text_input("PIN (4 chiffres)", type="password")
    obj = st.sidebar.number_input("Objectif poids (kg)", 40.0, 150.0, 70.0)
    if st.sidebar.button("Créer"):
        if u and p.isdigit() and len(p) == 4:
            save_file(f"user_data/{u}.pin", hash_pin(p))
            save_file(f"user_data/{u}.obj", str(obj))
            save_file(f"user_data/{u}.csv", "date,poids,sport,minutes,calories")
            st.sidebar.success("Compte créé !")

else:
    u = st.sidebar.text_input("Nom").strip().lower()
    p = st.sidebar.text_input("PIN", type="password")
    stored = load_file(f"user_data/{u}.pin") if u else None
    if stored and hash_pin(p) == stored:
        user = u
    elif stored:
        st.sidebar.error("PIN incorrect")

# =======================
# 9. INTERFACE
# =======================
if not user:
    st.markdown("<h1 style='text-align:center'>Bienvenue 👋</h1>", unsafe_allow_html=True)
    st.stop()

df = pd.read_csv(StringIO(load_file(f"user_data/{user}.csv")))
df["date"] = pd.to_datetime(df["date"]) if not df.empty else df
objectif = float(load_file(f"user_data/{user}.obj"))

full_df = get_global_stats()
if full_df is not None:
    full_df["date"] = pd.to_datetime(full_df["date"])

tabs = st.tabs(["🏆 Stats", "📊 Graphiques", "➕ Ajouter", "⚙️ Gestion"])

# =======================
# 🏆 STATS
# =======================
with tabs[0]:
    total = df["calories"].sum() if not df.empty else 0
    rank, nxt, medal, msg = get_rank(total)

    st.header(f"{user.capitalize()} — {rank}")
    st.info(msg)
    st.progress(min(total / nxt, 1.0))

    c1, c2, c3 = st.columns(3)
    c1.metric("🔥 Calories", f"{int(total)}")
    c2.metric("⚖️ Perte estimée", f"{total/7700:.2f} kg")
    c3.metric("🏅 Médaille", medal)

# =======================
# 📊 GRAPHIQUES
# =======================
with tabs[1]:
    if not df.empty:
        fig, ax = plt.subplots()
        ax.plot(df["date"], df["poids"], marker="o")
        ax.axhline(objectif, color="red", linestyle="--")
        st.pyplot(fig)

# =======================
# ➕ AJOUT
# =======================
with tabs[2]:
    with st.form("add"):
        d = st.date_input("Date", date.today())
        p = st.number_input("Poids", 40.0, 160.0, 75.0)
        s = st.selectbox("Sport", ["Marche", "Fitness", "Musculation", "Vélo", "Natation", "Course"])
        m = st.number_input("Minutes", 5, 300, 30)
        if st.form_submit_button("Sauvegarder"):
            mets = {
                "Marche": 3.3,
                "Fitness": 4.5,
                "Musculation": 5,
                "Vélo": 6.8,
                "Natation": 7,
                "Course": 8.5
            }
            cal = (m / 60) * mets[s] * p
            new = pd.DataFrame([{
                "date": d,
                "poids": p,
                "sport": s,
                "minutes": m,
                "calories": cal
            }])
            df = pd.concat([df, new], ignore_index=True)
            save_file(f"user_data/{user}.csv", df.to_csv(index=False))
            st.success("Ajouté !")
            st.rerun()

# =======================
# ⚙️ GESTION
# =======================
with tabs[3]:
    df_reset = df.reset_index(drop=True)
    st.dataframe(df_reset)

    idx = st.selectbox("Supprimer une ligne", df_reset.index)
    if st.button("❌ Supprimer"):
        df = df_reset.drop(idx)
        save_file(f"user_data/{user}.csv", df.to_csv(index=False))
        st.rerun()
