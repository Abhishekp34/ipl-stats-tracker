import os
import pandas as pd
import streamlit as st
import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# 1. Setup the Page
st.set_page_config(page_title="IPL Stats Tracker", layout="wide")
st.title("🏏 IPL Stats Tracker")
st.markdown("### Your Automated Home for IPL Analytics")

# 2. Securely connect to Supabase
@st.cache_resource
def init_connection():
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    return create_client(url, key)

supabase = init_connection()

# 3. Data Fetching
@st.cache_data(ttl=3600)
def get_summary_stats():
    # Fetch all matches to calculate high-level totals
    response = supabase.table('matches').select('match_id, season, city, winner').limit(2000).execute()
    return pd.DataFrame(response.data)

matches_df = get_summary_stats()

# 4. KPI Section (Major Highlights)
col1, col2, col3 = st.columns(3)
col1.metric("Total Matches", len(matches_df))
col2.metric("IPL Seasons", matches_df['season'].nunique())
col3.metric("Venues Covered", matches_df['city'].nunique())

st.divider()

# 5. "On This Day" - Quick Glimpse (Home Page Version)
today = datetime.date.today()
st.subheader(f"📅 On This Day: {today.strftime('%B %d')}")

# Simple query for matches played on this day historically
# We use .filter() with postgres syntax for extraction
try:
    otd_response = supabase.table('matches').select('match_date, team1, team2, winner, venue')\
        .filter('match_date', 'cs', f'-{today.strftime("%m-%d")}')\
        .order('match_date', desc=True).execute()
    
    otd_matches = pd.DataFrame(otd_response.data)

    if not otd_matches.empty:
        for _, row in otd_matches.iterrows():
            year = str(row['match_date'])[:4]
            st.write(f"**{year}**: {row['team1']} vs {row['team2']} at {row['venue']}")
            st.info(f"🏆 Result: {row['winner']} won")
    else:
        st.write("No matches were played on this specific day in previous IPL seasons.")
except Exception as e:
    st.error("Could not load historic matches for today.")

st.sidebar.success("Select a page above for deep-dive stats!")