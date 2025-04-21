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

TEAM_IDS = {
    'ARI': 109, 'ATL': 144, 'BAL': 110, 'BOS': 111, 'CHC': 112, 'CIN': 113, 'CLE': 114, 'COL': 115,
    'DET': 116, 'HOU': 117, 'KCR': 118, 'LAA': 108, 'LAD': 119, 'MIA': 146, 'MIL': 158, 'MIN': 142,
    'NYY': 147, 'NYM': 121, 'OAK': 133, 'PHI': 143, 'PIT': 134, 'SDP': 135, 'SEA': 136, 'SFG': 137,
    'STL': 138, 'TBR': 139, 'TEX': 140, 'TOR': 141, 'WSN': 120
}

TEAM_LOGOS = {
    team: f"https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/{team.lower()[:3]}.png" for team in TEAM_IDS
}

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

@st.cache_data
def get_schedule_difficulty(team_abbr):
    team_id = TEAM_IDS.get(team_abbr)
    if not team_id:
        return pd.DataFrame()

    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={team_id}&startDate={datetime.today().strftime('%Y-%m-%d')}&endDate=2025-10-01&gameType=R&limit=10"
    response = requests.get(url).json()
    games = []
    try:
        all_standings = pd.concat(standings(2025), ignore_index=True)
    except:
        all_standings = pd.DataFrame()

    for date in response.get('dates', []):
        for game in date.get('games', []):
            opponent_id = game['teams']['away']['team']['id'] if game['teams']['home']['team']['id'] == team_id else game['teams']['home']['team']['id']
            opponent = game['teams']['away']['team']['name'] if game['teams']['home']['team']['id'] == team_id else game['teams']['home']['team']['name']
            try:
                win_pct = all_standings[all_standings['Team'].str.contains(opponent, na=False)]['Win%'].values[0]
            except:
                win_pct = 0.5
            games.append({
                'Date': date['date'],
                'Opponent': opponent,
                'Difficulty (Win%)': win_pct
            })
    return pd.DataFrame(games)

if selected_team != "All":
    st.subheader(f"📅 Schedule Difficulty: Next 10 Games for {selected_team}")
    difficulty_df = get_schedule_difficulty(selected_team)
    st.dataframe(difficulty_df, use_container_width=True)

# 🔮 Red Neuronal: Predicción Fantasy Points
st.header("🔮 Predicción de Fantasy Points 2025 (con Red Neuronal)")

@st.cache_data
def load_training_data():
    df = batting_stats(2025, qual=0)
    df.dropna(subset=['R', 'H', '2B', '3B', 'HR', 'BB', 'SO', 'SB', 'RBI'], inplace=True)
    df['1B'] = df['H'] - df['2B'] - df['3B'] - df['HR']
    df['Total_Bases'] = df['1B'] + df['2B'] * 2 + df['3B'] * 3 + df['HR'] * 4
    df['Fantasy_Points'] = df['R'] + df['Total_Bases'] + df['RBI'] + df['BB'] - df['SO'] + df['SB']
    return df

data = load_training_data()
features = ['R', '2B', '3B', 'HR', 'BB', 'SO', 'SB', 'RBI']
X = data[features]
y = data['Fantasy_Points']

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

model = Sequential([
    Dense(64, activation='relu', input_shape=(X.shape[1],)),
    Dense(32, activation='relu'),
    Dense(1)
])
model.compile(optimizer='adam', loss='mse')
history = model.fit(X_train, y_train, validation_split=0.2, epochs=50, batch_size=16, verbose=0)

st.success("Modelo entrenado con éxito para batters (2025)")

fig, ax = plt.subplots()
ax.plot(history.history['loss'], label='Train Loss')
ax.plot(history.history['val_loss'], label='Validation Loss')
ax.set_title("Training Loss Curve")
ax.set_xlabel("Epoch")
ax.set_ylabel("Loss")
ax.legend()
st.pyplot(fig)

# Predicción
X_2025 = scaler.transform(X)
data['Predicted_Points'] = model.predict(X_2025)
st.dataframe(data[['Name', 'Fantasy_Points', 'Predicted_Points']].sort_values('Predicted_Points', ascending=False).head(25), use_container_width=True)