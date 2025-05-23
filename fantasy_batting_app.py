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

st.set_page_config(page_title="MLB Fantasy Dashboard", layout="wide")
st.title("MLB Fantasy Dogout (Batters & Pitchers)")

TEAM_LOGOS = {
    'ARI': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/ari.png',
    'ATL': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/atl.png',
    'BAL': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/bal.png',
    'BOS': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/bos.png',
    'CHC': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/chc.png',
    'CIN': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/cin.png',
    'CLE': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/cle.png',
    'COL': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/col.png',
    'DET': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/det.png',
    'HOU': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/hou.png',
    'KCR': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/kc.png',
    'LAA': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/laa.png',
    'LAD': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/lad.png',
    'MIA': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/mia.png',
    'MIL': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/mil.png',
    'MIN': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/min.png',
    'NYY': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/nyy.png',
    'NYM': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/nym.png',
    'OAK': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/oak.png',
    'PHI': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/phi.png',
    'PIT': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/pit.png',
    'SDP': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/sd.png',
    'SEA': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/sea.png',
    'SFG': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/sf.png',
    'STL': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/stl.png',
    'TBR': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/tb.png',
    'TEX': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/tex.png',
    'TOR': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/tor.png',
    'WSN': 'https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/wsh.png'
}

TEAM_IDS = {
    'ARI': 109, 'ATL': 144, 'BAL': 110, 'BOS': 111, 'CHC': 112, 'CIN': 113, 'CLE': 114, 'COL': 115,
    'DET': 116, 'HOU': 117, 'KCR': 118, 'LAA': 108, 'LAD': 119, 'MIA': 146, 'MIL': 158, 'MIN': 142,
    'NYY': 147, 'NYM': 121, 'OAK': 133, 'PHI': 143, 'PIT': 134, 'SDP': 135, 'SEA': 136, 'SFG': 137,
    'STL': 138, 'TBR': 139, 'TEX': 140, 'TOR': 141, 'WSN': 120
}

selected_seasons = st.sidebar.multiselect("Select seasons:", [2023, 2024, 2025], default=[2023, 2024, 2025])
selected_team = st.sidebar.selectbox("Filter by Team:", ["All"] + list(TEAM_IDS.keys()))

if selected_team != "All" and selected_team in TEAM_LOGOS:
    st.sidebar.image(TEAM_LOGOS[selected_team], width=100)

@st.cache_data(show_spinner=True)
def get_batting_fantasy_stats(year):
    df = batting_stats(year, qual=0)
    df['1B'] = df['H'] - df['2B'] - df['3B'] - df['HR']
    df['Total_Bases'] = df['1B'] + df['2B'] * 2 + df['3B'] * 3 + df['HR'] * 4
    df['Season'] = year
    for col in ['Team', 'Position']:
        if col not in df.columns:
            df[col] = 'Unknown'
    df['Fantasy_Points'] = df['R'] + df['Total_Bases'] + df['RBI'] + df['BB'] - df['SO'] + df['SB']
    return df[['Name', 'Fantasy_Points', 'Season', 'Team', 'R', 'Total_Bases', 'RBI', 'BB', 'SO', 'SB']]

@st.cache_data(show_spinner=True)
def get_pitching_fantasy_stats(year):
    df = pitching_stats(year, qual=0)
    df = df.rename(columns={'Name': 'Player'})
    df['IP'] = pd.to_numeric(df['IP'], errors='coerce')
    df.fillna(0, inplace=True)
    df['Fantasy_Points'] = (
        df['IP'] * 3 + df['SO'] + df['W'] * 2 + df['SV'] * 5 + df['HLD'] * 2 -
        df['H'] - df['ER'] * 2 - df['BB'] - df['L'] * 2
    )
    df['Year'] = year
    for col in ['Team', 'Position']:
        if col not in df.columns:
            df[col] = 'Unknown'
    return df[['Player', 'Fantasy_Points', 'Year', 'Team', 'IP','H','ER','BB','SO', 'W','L', 'SV', 'HLD']]

batting_data = pd.concat([get_batting_fantasy_stats(year) for year in selected_seasons])
pitching_data = pd.concat([get_pitching_fantasy_stats(year) for year in selected_seasons])

if selected_team != "All":
    batting_data = batting_data[batting_data['Team'] == selected_team]
    pitching_data = pitching_data[pitching_data['Team'] == selected_team]

batting_summary = batting_data.groupby('Name', as_index=False).sum(numeric_only=True).drop(columns=['Season'], errors='ignore')
pitching_summary = pitching_data.groupby('Player', as_index=False).sum(numeric_only=True).drop(columns=['Year'], errors='ignore')

batters_tab, pitchers_tab, standings_tab, pred_batters_tab, pred_pitchers_tab = st.tabs([
    "Batters", "Pitchers", "Team Standings", "Batters Expected Performance", "Pitchers Expected Performance"])

with batters_tab:
    st.subheader("Top 100 Batters by Fantasy Points")
    st.dataframe(batting_summary[['Name', 'Fantasy_Points'] + [col for col in batting_summary.columns if col not in ['Name', 'Fantasy_Points']]].sort_values("Fantasy_Points", ascending=False).head(100), use_container_width=True)
    st.download_button("⬇ Download Batters as CSV", batting_summary.to_csv(index=False), file_name="batters.csv", mime="text/csv")

with pitchers_tab:
    st.subheader("Top 100 Pitchers by Fantasy Points")
    st.dataframe(pitching_summary[['Player', 'Fantasy_Points'] + [col for col in pitching_summary.columns if col not in ['Player', 'Fantasy_Points']]].sort_values("Fantasy_Points", ascending=False).head(100), use_container_width=True)
    st.download_button("⬇ Download Pitchers as CSV", pitching_summary.to_csv(index=False), file_name="pitchers.csv", mime="text/csv")

with standings_tab:
    st.subheader("Live MLB Team Standings")
    try:
        current_year = max(selected_seasons)
        standings_list = standings(current_year)
        standings_combined = pd.concat(standings_list, ignore_index=True)
        st.dataframe(standings_combined, use_container_width=True)
    except Exception as e:
        st.error(f"Could not load standings: {e}")

    st.subheader("Next 10 Games for Selected Team")

    def get_next_10_games(team_abbr):
        team_id = TEAM_IDS.get(team_abbr)
        if not team_id:
            return pd.DataFrame({'Error': [f'Team {team_abbr} not mapped.']})

        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={team_id}&startDate={datetime.today().strftime('%Y-%m-%d')}&endDate=2025-10-01&gameType=R&limit=10"
        response = requests.get(url).json()

        games = []
        for date in response.get('dates', []):
            for game in date.get('games', []):
                games.append({
                    'Date': date['date'],
                    'Home': game['teams']['home']['team']['name'],
                    'Away': game['teams']['away']['team']['name'],
                    'Status': game['status']['detailedState']
                })

        return pd.DataFrame(games)

    if selected_team != "All":
        games_df = get_next_10_games(selected_team)
        st.dataframe(games_df, use_container_width=True)
    else:
        st.info("Select a team from the sidebar to view its next 10 games.")

with pred_batters_tab:
    st.subheader("Predicted Fantasy Points for Batters (End of 2025)")
    df = pd.concat([get_batting_fantasy_stats(y) for y in [2023, 2024, 2025]])
    df.dropna(subset=['R', 'RBI', 'BB', 'SO', 'SB', 'Total_Bases'], inplace=True)
    X = df[['R', 'RBI', 'BB', 'SO', 'SB', 'Total_Bases']]
    y = df['Fantasy_Points']

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = Sequential([
        Dense(32, activation='relu', input_shape=(X.shape[1],)),
        Dense(16, activation='relu'),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    model.fit(X_scaled, y, epochs=50, batch_size=16, verbose=0)

    df_2025 = get_batting_fantasy_stats(2025)
    X_2025 = df_2025[['R', 'RBI', 'BB', 'SO', 'SB', 'Total_Bases']]
    X_2025_scaled = scaler.transform(X_2025)
    df_2025['Predicted_Points'] = model.predict(X_2025_scaled)
    st.dataframe(df_2025[['Name', 'Fantasy_Points', 'Predicted_Points']].sort_values('Predicted_Points', ascending=False).head(25), use_container_width=True)

with pred_pitchers_tab:
    st.subheader("Predicted Fantasy Points for Pitchers (End of 2025)")
    df = pd.concat([get_pitching_fantasy_stats(y) for y in [2023, 2024, 2025]])
    df.dropna(subset=['IP', 'H', 'ER', 'BB', 'SO', 'W', 'L', 'SV', 'HLD'], inplace=True)
    X = df[['IP', 'H', 'ER', 'BB', 'SO', 'W', 'L', 'SV', 'HLD']]
    y = df['Fantasy_Points']

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = Sequential([
        Dense(32, activation='relu', input_shape=(X.shape[1],)),
        Dense(16, activation='relu'),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    model.fit(X_scaled, y, epochs=50, batch_size=16, verbose=0)

    df_2025 = get_pitching_fantasy_stats(2025)
    X_2025 = df_2025[['IP', 'H', 'ER', 'BB', 'SO', 'W', 'L', 'SV', 'HLD']]
    X_2025_scaled = scaler.transform(X_2025)
    df_2025['Predicted_Points'] = model.predict(X_2025_scaled)
    st.dataframe(df_2025[['Player', 'Fantasy_Points', 'Predicted_Points']].sort_values('Predicted_Points', ascending=False).head(25), use_container_width=True)
