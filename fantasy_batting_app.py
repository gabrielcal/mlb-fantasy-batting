import streamlit as st
from pybaseball import batting_stats, pitching_stats, standings
import pandas as pd

st.set_page_config(page_title="MLB Fantasy Dashboard", layout="wide")
st.title("MLB Fantasy Points (Batters & Pitchers)")

# Sidebar - Year Selection
selected_seasons = st.sidebar.multiselect(
    "Select seasons:",
    [2023, 2024, 2025],
    default=[2023, 2024, 2025]
)

@st.cache_data(show_spinner=True)
def get_batting_fantasy_stats(year):
    df = batting_stats(year, qual=0)
    df['1B'] = df['H'] - df['2B'] - df['3B'] - df['HR']
    df['Total_Bases'] = df['1B'] + df['2B'] * 2 + df['3B'] * 3 + df['HR'] * 4
    df['Season'] = year
    return df[['Name', 'Season', 'R', 'Total_Bases', 'RBI', 'BB', 'SO', 'SB']]

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
    return df[['Player', 'Year', 'IP','H','ER','BB','SO', 'W','L', 'SV', 'HLD', 'Fantasy_Points']]

# Load data for selected seasons
batting_data = pd.concat([get_batting_fantasy_stats(year) for year in selected_seasons])
pitching_data = pd.concat([get_pitching_fantasy_stats(year) for year in selected_seasons])

# Aggregate Batting Data
batting_summary = batting_data.groupby('Name', as_index=False).sum()
batting_summary['Fantasy_Points'] = (
    batting_summary['R'] + batting_summary['Total_Bases'] +
    batting_summary['RBI'] + batting_summary['BB'] -
    batting_summary['SO'] + batting_summary['SB']
)

# Aggregate Pitching Data
pitching_summary = pitching_data.groupby('Player', as_index=False).sum()

# Tabs for Batters and Pitchers
batters_tab, pitchers_tab, standings_tab = st.tabs(["Batters", "Pitchers", "Team Standings"])

with batters_tab:
    st.subheader("Top 100 Batters by Fantasy Points")
    st.dataframe(
        batting_summary.sort_values("Fantasy_Points", ascending=False).head(100),
        use_container_width=True
    )
    with st.expander("Filter Batters"):
        name_filter = st.text_input("Filter by name:")
        if name_filter:
            filtered = batting_summary[batting_summary['Name'].str.contains(name_filter, case=False)]
            st.dataframe(filtered.sort_values("Fantasy_Points", ascending=False), use_container_width=True)

with pitchers_tab:
    st.subheader("Top 100 Pitchers by Fantasy Points")
    st.dataframe(
        pitching_summary.sort_values("Fantasy_Points", ascending=False).head(100),
        use_container_width=True
    )
    with st.expander("Filter Pitchers"):
        name_filter = st.text_input("Filter by name:", key="pitcher_filter")
        if name_filter:
            filtered = pitching_summary[pitching_summary['Player'].str.contains(name_filter, case=False)]
            st.dataframe(filtered.sort_values("Fantasy_Points", ascending=False), use_container_width=True)

with standings_tab:
    st.subheader("Live MLB Team Standings")
    try:
        current_year = max(selected_seasons)
        standings_df = standings(current_year)
        st.dataframe(standings_df, use_container_width=True)
    except Exception as e:
        st.error(f"Could not load standings: {e}")

