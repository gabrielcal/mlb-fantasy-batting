import streamlit as st
from pybaseball import batting_stats
import pandas as pd

# Title
st.title("MLB Fantasy Batting Points (2023–2025)")

# Sidebar controls
selected_seasons = st.multiselect(
    "Select seasons to include:",
    [2023, 2024, 2025],
    default=[2023, 2024, 2025]
)

@st.cache_data(show_spinner=True)
def get_batting_stats(year):
    df = batting_stats(year, qual=0)
    df['1B'] = df['H'] - df['2B'] - df['3B'] - df['HR']
    df['Total_Bases'] = df['1B'] + df['2B'] * 2 + df['3B'] * 3 + df['HR'] * 4
    return df[['Name', 'R', 'Total_Bases', 'RBI', 'BB', 'SO', 'SB']]

# Load and combine stats
all_data = []
for year in selected_seasons:
    try:
        df = get_batting_stats(year)
        df['Season'] = year
        all_data.append(df)
    except Exception as e:
        st.error(f"Failed to load data for {year}: {e}")

if all_data:
    combined = pd.concat(all_data)
    summary = combined.groupby('Name', as_index=False).sum()
    summary['Fantasy_Points'] = (
        summary['R'] + summary['Total_Bases'] + summary['RBI'] +
        summary['BB'] - summary['SO'] + summary['SB']
    )
    
    # Show table
    st.subheader("Top Fantasy Batters")
    st.dataframe(summary.sort_values('Fantasy_Points', ascending=False).head(50))
    
    # Optional download
    st.download_button("Download as CSV", summary.to_csv(index=False), "fantasy_stats.csv", "text/csv")
else:
    st.warning("Please select at least one season.")
