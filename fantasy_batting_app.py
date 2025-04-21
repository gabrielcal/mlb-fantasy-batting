import streamlit as st
from pybaseball import batting_stats, pitching_stats, standings
import pandas as pd
import requests
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="MLB Fantasy Dashboard", layout="wide")
st.title("MLB Fantasy Points (Batters & Pitchers)")

TEAM_LOGOS = { ... }  # same as before
TEAM_IDS = { ... }  # same as before

selected_seasons = st.sidebar.multiselect("Select seasons:", [2023, 2024, 2025], default=[2023, 2024, 2025])
selected_team = st.sidebar.selectbox("Filter by Team:", ["All"] + list(TEAM_IDS.keys()))
search_name = st.sidebar.text_input("Search player by name:", "")

if selected_team != "All" and selected_team in TEAM_LOGOS:
    st.sidebar.image(TEAM_LOGOS[selected_team], width=100)

st.sidebar.subheader("Compare Players")
compare_batters = st.sidebar.multiselect("Select batters to compare:", [])
compare_pitchers = st.sidebar.multiselect("Select pitchers to compare:", [])

st.markdown("""
    <style>
    @media only screen and (max-width: 768px) {
        .stApp { font-size: 14px; }
        .block-container { padding: 1rem; }
    }
    </style>
""", unsafe_allow_html=True)

# Función para obtener el coeficiente de dificultad de los próximos 10 rivales
@st.cache_data
def get_schedule_difficulty(team_abbr):
    team_id = TEAM_IDS.get(team_abbr)
    if not team_id:
        return pd.DataFrame()

    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={team_id}&startDate={datetime.today().strftime('%Y-%m-%d')}&endDate=2025-10-01&gameType=R&limit=10"
    response = requests.get(url).json()
    games = []
    for date in response.get('dates', []):
        for game in date.get('games', []):
            opponent = game['teams']['away']['team']['name'] if game['teams']['home']['team']['id'] == team_id else game['teams']['home']['team']['name']
            opponent_abbr = next((abbr for abbr, tid in TEAM_IDS.items() if tid == game['teams']['home']['team']['id'] or tid == game['teams']['away']['team']['id']), "")
            try:
                opponent_standings = standings(2025)
                all_standings = pd.concat(opponent_standings, ignore_index=True)
                win_pct = all_standings[all_standings['Team'] == opponent]['Win%'].values[0]
            except:
                win_pct = 0.5  # Valor neutral si falla
            games.append({
                'Date': date['date'],
                'Opponent': opponent,
                'Difficulty (Win%)': win_pct
            })
    return pd.DataFrame(games)

# Mostrar dificultad si hay equipo seleccionado
if selected_team != "All":
    st.subheader(f"📅 Schedule Difficulty: Next 10 Games for {selected_team}")
    difficulty_df = get_schedule_difficulty(selected_team)
    st.dataframe(difficulty_df, use_container_width=True)

# El resto del código (red neuronal, comparador, gráficos) sigue igual y ya está cargado
# Puedes continuar integrando otras mejoras a partir de aquí.
