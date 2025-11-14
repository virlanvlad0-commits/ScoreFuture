import streamlit as st
import pandas as pd
import numpy as np
import os
import unicodedata
import re
import random

st.set_page_config(page_title="Predictor Fotbal - Analiză și Predicție Inteligentă", layout="wide")
st.title("⚽ Predictor Fotbal - Analiză și Predicție Inteligentă")

DATA_PATH = os.path.join("data", "istoric.csv")

# === Încărcare fișier ===
@st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH):
        # 🛑 Aici lipsea apelul către update_istoric.main()
        st.error("⚠️ Fișierul data/istoric.csv lipsește. Rulează mai întâi update_istoric.py.")
        return pd.DataFrame()
    return pd.read_csv(DATA_PATH)

# === Normalizare nume echipe ===
def normalize_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    name = name.lower()
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("utf-8")
    name = re.sub(r"\b(fc|cf|club|sc|sk|real|sporting|ss|as|ac|paris|saint|germain|munchen|muenchen)\b", "", name)
    name = name.replace("bayernmunchen", "bayernmunich").replace("psg", "parissaintgermain")
    name = re.sub(r"[^a-z0-9]", "", name)
    return name.strip()

# === Aliasuri echipe mari ===
ALIASE = {
    "psg": ["parissaintgermain", "psg", "paris"],
    "bayernmunich": ["bayern", "fcbayern", "fcbayernmunich", "bayernmunchen"],
    "realmadrid": ["realmadrid", "madrid"],
    "barcelona": ["barcelona", "fcb", "fcbarcelona"],
    "manchestercity": ["manchestercity", "city", "mancity"],
    "arsenal": ["arsenal", "arsenalfc"],
    "acmilan": ["acmilan", "milan"],
    "intermilan": ["intermilan", "inter", "internazionale"],
}

def echipe_egale(e1, e2):
    n1, n2 = normalize_name(e1), normalize_name(e2)
    for k, alias_list in ALIASE.items():
        if n1 in alias_list and n2 in alias_list:
            return True
    return n1 == n2

# === Meniu principal ===
pagina = st.sidebar.radio("📍 Meniu principal", [
    "📊 Istoric echipă",
    "🤖 Predicție AI realistă (posesie + scoruri variate)"
])

# ======================================================
# 📊 PAGINA: ISTORIC ECHIPĂ
# ======================================================
if pagina == "📊 Istoric echipă":
    st.header("📅 Analiză istorică echipă")

    df = load_data()
    if df.empty:
        st.stop()

    echipe = sorted(df["Echipa"].unique())
    echipa_select = st.selectbox("Alege echipa", echipe)
    echipa_df = df[df["Echipa"] == echipa_select].sort_values(by="Data", ascending=False).copy()

    rezultate = []
    for _, row in echipa_df.iterrows():
        try:
            g1, g2 = int(row["Scor_Gazda"]), int(row["Scor_Oaspete"])
            gazda, oaspete = row["Gazda"], row["Oaspete"]

            if echipe_egale(echipa_select, gazda):
                rezultat = "Victorie" if g1 > g2 else "Egal" if g1 == g2 else "Înfrângere"
            elif echipe_egale(echipa_select, oaspete):
                rezultat = "Victorie" if g2 > g1 else "Egal" if g1 == g2 else "Înfrângere"
            else:
                rezultat = "Neidentificat"
        except:
            rezultat = "Neîncheiat"
        rezultate.append(rezultat)

    echipa_df["Rezultat_Calculat"] = rezultate
    st.dataframe(echipa_df, hide_index=True, use_container_width=True)

    # === Statistici ===
    w = (echipa_df["Rezultat_Calculat"] == "Victorie").sum()
    d = (echipa_df["Rezultat_Calculat"] == "Egal").sum()
    l = (echipa_df["Rezultat_Calculat"] == "Înfrângere").sum()

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("🏆 Victorii", w)
    c2.metric("🤝 Egaluri", d)
    c3.metric("❌ Înfrângeri", l)
    st.markdown("---")

    # === Forma recentă ===
    ultima_forma = echipa_df["Rezultat_Calculat"].head(5).tolist()
    simboluri = {"Victorie": "🟩", "Egal": "🟨", "Înfrângere": "🟥"}
    forma_text = " ".join(simboluri.get(r, "⬜") for r in ultima_forma)
    st.markdown(f"**Forma recentă (ultimele 5 meciuri):** {forma_text}")

# ======================================================
# 🤖 PAGINA: PREDICȚIE AI REALISTĂ
# ======================================================
elif pagina == "🤖 Predicție AI realistă (posesie + scoruri variate)":
    st.header("🧠 Predicție AI realistă (bazată pe istoric și posesie simulată)")

    df = load_data()
    if df.empty:
        st.stop()

    echipe = sorted(df["Echipa"].unique())
    echipa1 = st.selectbox("🏠 Echipa gazdă", echipe)
    echipa2 = st.selectbox("🚗 Echipa oaspete", echipe)

    if echipa1 == echipa2:
        st.warning("⚠️ Alege echipe diferite pentru o predicție realistă.")
        st.stop()

    df1 = df[df["Echipa"] == echipa1].head(15)
    df2 = df[df["Echipa"] == echipa2].head(15)

    def analiza(df, echipa):
        puncte, goluri_marcate, goluri_primite = 0, 0, 0
        for _, r in df.iterrows():
            try:
                g1, g2 = int(r["Scor_Gazda"]), int(r["Scor_Oaspete"])
                gazda, oaspete = r["Gazda"], r["Oaspete"]
                if echipe_egale(echipa, gazda):
                    goluri_marcate += g1
                    goluri_primite += g2
                    puncte += 3 if g1 > g2 else 1 if g1 == g2 else 0
                elif echipe_egale(echipa, oaspete):
                    goluri_marcate += g2
                    goluri_primite += g1
                    puncte += 3 if g2 > g1 else 1 if g1 == g2 else 0
            except:
                continue
        return puncte, goluri_marcate, goluri_primite

    p1, g1m, g1p = analiza(df1, echipa1)
    p2, g2m, g2p = analiza(df2, echipa2)

    # === Simulare posesie inteligentă ===
    def estimeaza_posesie(echipa, puncte):
        elite = ["bayern", "barcelona", "city", "psg", "real", "arsenal"]
        base = 60 if any(e in normalize_name(echipa) for e in elite) else 50
        ajustare = np.clip(puncte / 45 * 10, -5, 10)
        return np.clip(base + ajustare + np.random.uniform(-7, 7), 40, 70)

    pos1 = estimeaza_posesie(echipa1, p1)
    pos2 = 100 - pos1

    if st.button("🚀 Calculează predicția"):
        forma_home = p1 / max(1, len(df1)) + (g1m - g1p) * 0.3 + (pos1 - 50) * 0.05
        forma_away = p2 / max(1, len(df2)) + (g2m - g2p) * 0.3 + (pos2 - 50) * 0.05

        surpriza = np.random.uniform(-0.5, 0.5)
        gol_home = np.clip(np.random.normal(1.6 + (forma_home - forma_away) * 0.08 + surpriza, 0.9), 0, 7)
        gol_away = np.clip(np.random.normal(1.2 - (forma_home - forma_away) * 0.08 - surpriza, 1.0), 0, 7)

        home_goals = int(round(gol_home))
        away_goals = int(round(gol_away))

        if random.random() < 0.2:
            home_goals += random.choice([1, 2, 3])
            away_goals += random.choice([0, 1, 2])

        if home_goals > away_goals:
            msg = f"🏆 **{echipa1}** e favorită!"
            color = "green"
        elif home_goals < away_goals:
            msg = f"🥇 **{echipa2}** pare mai puternică!"
            color = "red"
        else:
            msg = "🤝 Meci echilibrat — posibil **egal**."
            color = "gold"

        st.markdown(f"<h3 style='color:{color}'>{msg}</h3>", unsafe_allow_html=True)
        st.markdown(
            f"<h2 style='text-align:center;color:{color}'>⚽ Scor estimat: "
            f"**{echipa1}** {home_goals} - {away_goals} **{echipa2}**</h2>",
            unsafe_allow_html=True
        )

        st.markdown(
            f"<p style='text-align:center;color:gray'>📊 Posesie estimată: "
            f"**{echipa1}** {pos1:.1f}% - {pos2:.1f}% **{echipa2}**</p>",
            unsafe_allow_html=True
        )