import os
import pandas as pd
import streamlit as st
import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# 1. Setup the Page
st.set_page_config(page_title="The IPL Tracker", layout="wide", page_icon="🏏")

# 2. Securely connect to Supabase
@st.cache_resource
def init_connection():
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    return create_client(url, key)

supabase = init_connection()

# 3. Custom Styling
st.markdown("""
    <style>
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        color: #f1c40f;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏏 The IPL Tracker")
st.divider()

# 4. Quick Navigation Section (Updated to match your file structure)
st.subheader("🚀 Quick Navigation")
n1, n2, n3, n4 = st.columns(4)

with n1:
    with st.container(border=True):
        st.markdown("### 🏆")
        st.write("**Leaderboards**")
        st.page_link("pages/05_Leaderboards.py", label="View Rankings", icon="📊")

with n2:
    with st.container(border=True):
        st.markdown("### ⚔️")
        st.write("**Comparison**")
        st.page_link("pages/01_Player_Comparison.py", label="Compare Players", icon="⚖️")

with n3:
    with st.container(border=True):
        st.markdown("### 👤")
        st.write("**Profiles**")
        st.page_link("pages/04_Player_Profiles.py", label="Player Resume", icon="📄")

with n4:
    with st.container(border=True):
        st.markdown("### 📅")
        st.write("**History**")
        st.page_link("pages/02_On_This_Day.py", label="On This Day", icon="🕰️")

st.divider()

# 5. Global Highlights Section
@st.cache_data(ttl=3600)
def get_global_totals():
    # Efficiently get counts from your Materialized Views and Matches table
    b_res = supabase.table('view_batter_master').select('player', count='exact').limit(1).execute()
    m_res = supabase.table('matches').select('match_id', count='exact').limit(1).execute()
    return m_res.count, b_res.count

try:
    total_matches, total_players = get_global_totals()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Matches", f"{total_matches}")
    col2.metric("Unique Players", f"{total_players}")
    col3.metric("IPL Seasons", "17") 
except:
    st.error("Stats temporarily unavailable.")

st.divider()

# 6. Historic Matches: The Fix
today = datetime.date.today()
st.subheader(f"🕰️ Historic Matches: {today.strftime('%B %d')}")

@st.cache_data(ttl=3600)
def get_home_otd(m, d):
    # Using the RPC function for accurate date filtering
    try:
        res = supabase.rpc('get_matches_by_day_month', {
            'target_month': m, 
            'target_day': d
        }).execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

otd_matches = get_home_otd(today.month, today.day)

if not otd_matches.empty:
    # Display the 3 most recent historical matches on this date
    # Sort by date in pandas to ensure the latest years appear first
    otd_matches['match_date'] = pd.to_datetime(otd_matches['match_date'])
    otd_matches = otd_matches.sort_values('match_date', ascending=False)
    
    for _, row in otd_matches.head(3).iterrows():
        year = row['match_date'].year
        with st.chat_message("user", avatar="🏏"):
            st.write(f"**{year}**: {row['team1']} vs {row['team2']}")
            st.caption(f"📍 {row['venue']} | 🏆 {row['winner']} won")
else:
    st.info(f"No matches recorded on {today.strftime('%B %d')} in previous seasons.")

st.sidebar.info("Tip: Use the sidebar or cards above to navigate.")