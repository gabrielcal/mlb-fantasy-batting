import streamlit as st
from pybaseball import batting_stats, pitching_stats, standings
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="MLB Fantasy Dashboard", layout="wide")
st.title("MLB Fantasy Points (Batters & Pitchers)")

# Sidebar - Year Selection
selected_seasons = st.sidebar.multiselect(
    "Select seasons:",
    [2023, 2024, 2025],
    default=[2023, 2024, 2025]
)

# All MLB team IDs for next 10 games
TEAM_IDS = {
    'ARI': 109, 'ATL': 144, 'BAL': 110, 'BOS': 111, 'CHC': 112, 'CIN': 113, 'CLE': 114, 'COL': 115,
    'DET': 116, 'HOU': 117, 'KCR': 118, 'LAA': 108, 'LAD': 119, 'MIA': 146, 'MIL': 158, 'MIN': 142,
    'NYY': 147, 'NYM': 121, 'OAK': 133, 'PHI': 143, 'PIT': 134, 'SDP': 135, 'SEA': 136, 'SFG': 137,
    'STL': 138, 'TBR': 139, 'TEX': 140, 'TOR': 141, 'WSN': 120
}

# Sidebar - Filters
selected_team = st.sidebar.selectbox("Filter by Team:", ["All"] + list(TEAM_IDS.keys()))
selected_position = st.sidebar.selectbox("Filter by Position:", ["All", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "C", "DH", "TWP", "SP", "RP"])

@st.cache_data(show_spinner=True)
def get_batting_fantasy_stats(year):
    df = batting_stats(year, qual=0)
    df['1B'] = df['H'] - df['2B'] - df['3B'] - df['HR']
    df['Total_Bases'] = df['1B'] + df['2B'] * 2 + df['3B'] * 3 + df['HR'] * 4
    df['Season'] = year
    return df[['Name', 'Season', 'Team', 'Position', 'R', 'Total_Bases', 'RBI', 'BB', 'SO', 'SB']]

@st.cache_data(show_spinner=True)
def get_pitching_fantasy_stats(year):
    df = pitching_stats(year, qual=0)
    df = df.rename(columns={
        'Name': 'Player',
        'IP': 'IP', 'SO': 'SO', 'W': 'W', 'SV': 'SV',
        'HLD': 'HLD', 'H': 'H', 'ER': 'ER', 'BB': 'BB', 'L': 'L'
    })
    df['IP'] = pd.to_numeric(df['IP'], errors='coerce')
    df.fillna(0, inplace=True)
    df['Fantasy_Points'] = (
        df['IP'] * 3 + df['SO'] * 1 + df['W'] * 2 +
        df['SV'] * 5 + df['HLD'] * 2 - df['H'] * 1 -
        df['ER'] * 2 - df['BB'] * 1 - df['L'] * 2
    )
    df['Year'] = year
    return df[['Player', 'Year', 'Team', 'Position', 'IP','H','ER','BB','SO', 'W','L', 'SV', 'HLD', 'Fantasy_Points']]

# Load data for selected seasons
batting_data = pd.concat([get_batting_fantasy_stats(year) for year in selected_seasons])
pitching_data = pd.concat([get_pitching_fantasy_stats(year) for year in selected_seasons])

# Apply filters if selected
if selected_team != "All":
    batting_data = batting_data[batting_data['Team'] == selected_team]
    pitching_data = pitching_data[pitching_data['Team'] == selected_team]

if selected_position != "All":
    batting_data = batting_data[batting_data['Position'] == selected_position]
    pitching_data = pitching_data[pitching_data['Position'] == selected_position]

# Aggregate Batting Data
batting_summary = batting_data.groupby('Name', as_index=False).sum(numeric_only=True)
batting_summary['Fantasy_Points'] = (
    batting_summary['R'] + batting_summary['Total_Bases'] +
    batting_summary['RBI'] + batting_summary['BB'] -
    batting_summary['SO'] + batting_summary['SB']
)

# Aggregate Pitching Data
pitching_summary = pitching_data.groupby('Player', as_index=False).sum(numeric_only=True)

# Tabs for Batters, Pitchers, Standings
batters_tab, pitchers_tab, standings_tab = st.tabs(["Batters", "Pitchers", "Team Standings"])

with batters_tab:
    st.subheader("Top 100 Batters by Fantasy Points")
    st.dataframe(
        batting_summary.sort_values("Fantasy_Points", ascending=False).head(100),
        use_container_width=True
    )
    st.download_button("⬇ Download Batters as CSV", batting_summary.to_csv(index=False), file_name="batters.csv", mime="text/csv")

with pitchers_tab:
    st.subheader("Top 100 Pitchers by Fantasy Points")
    st.dataframe(
        pitching_summary.sort_values("Fantasy_Points", ascending=False).head(100),
        use_container_width=True
    )
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

    # Optional: Upcoming Games
    st.subheader("Next 10 Games for Selected Team")
    def get_next_10_games(team_abbr):
        team_id = TEAM_IDS.get(team_abbr)
        if not team_id:
            return pd.DataFrame({'Error': [f'Team {team_abbr} not mapped.']})

        url = f'https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={team_id}&startDate={datetime.today().strftime("%Y-%m-%d")}&endDate=2025-10-01&gameType=R&limit=10'
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
        st.info("Select a team from the sidebar to view its next 10 games.")h=True)
    except Exception as e:
        st.error(f"Could not load standings: {e}")

