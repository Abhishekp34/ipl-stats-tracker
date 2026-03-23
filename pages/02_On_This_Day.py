import streamlit as st
import pandas as pd
import datetime
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# 1. Page Config
st.set_page_config(page_title="On This Day | IPL Tracker", layout="wide")

# 2. Database Connection
@st.cache_resource
def init_connection():
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    return create_client(url, key)

supabase = init_connection()

st.title("📅 IPL: On This Day")

# 3. Date Picker
target_date = st.date_input("Select a date to see history:", datetime.date.today())
month = int(target_date.month)
day = int(target_date.day)

# --- DATA FETCHING ---

@st.cache_data(ttl=3600)
def get_otd_data(m, d):
    # Call the SQL function we created in Step 1
    matches_res = supabase.rpc('get_matches_by_day_month', {
        'target_month': m, 
        'target_day': d
    }).execute()
    
    matches_df = pd.DataFrame(matches_res.data)
    
    if matches_df.empty:
        return matches_df, pd.DataFrame(), []

    match_ids = matches_df['match_id'].tolist()
    
    # Fetch Deliveries for these specific matches
    deliv_res = supabase.table('deliveries').select(
        'match_id, batter, runs_batter, bowler, wicket_type'
    ).in_('match_id', match_ids).execute()
    
    deliv_df = pd.DataFrame(deliv_res.data)
    
    return matches_df, deliv_df, match_ids

matches_df, deliv_df, match_ids = get_otd_data(month, day)

if matches_df.empty:
    st.warning(f"No IPL matches were played on {target_date.strftime('%B %d')} in history.")
else:
    # 4. Match Highlights
    st.subheader(f"🏟️ Matches Played on {target_date.strftime('%B %d')}")
    for _, row in matches_df.iterrows():
        year = str(row['match_date'])[:4]
        with st.expander(f"{year}: {row['team1']} vs {row['team2']}"):
            st.write(f"**Venue:** {row['venue']}, {row['city']}")
            st.success(f"🏆 Winner: {row['winner']}")

    # 5. Legendary Performances
    st.divider()
    st.subheader("🌟 Legendary Performances")
    
    if not deliv_df.empty:
        # Centuries
        runs_per_match = deliv_df.groupby(['match_id', 'batter'])['runs_batter'].sum().reset_index()
        centuries = runs_per_match[runs_per_match['runs_batter'] >= 100]
        
        # 5-Wicket Hauls
        wickets = ['bowled', 'caught', 'lbw', 'stumped', 'caught and bowled', 'hit wicket']
        deliv_df['is_wicket'] = deliv_df['wicket_type'].isin(wickets)
        wkts_per_match = deliv_df.groupby(['match_id', 'bowler'])['is_wicket'].sum().reset_index()
        five_fers = wkts_per_match[wkts_per_match['is_wicket'] >= 5]

        col_a, col_b = st.columns(2)
        with col_a:
            st.write("🏏 **Centuries Today**")
            if not centuries.empty:
                for _, row in centuries.iterrows():
                    st.info(f"**{row['batter']}** scored {int(row['runs_batter'])}")
            else:
                st.write("None")
        
        with col_b:
            st.write("🎯 **5-Wicket Hauls Today**")
            if not five_fers.empty:
                for _, row in five_fers.iterrows():
                    st.error(f"**{row['bowler']}** took {int(row['is_wicket'])} wickets")
            else:
                st.write("None")

    # 6. Leaderboards: Top of the Day
    st.divider()
    st.subheader(f"📊 All-time Leaderboard for this Date")
    
    top_n = st.radio("Show top:", [5, 10], horizontal=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"🔥 Most Runs")
        top_batters = deliv_df.groupby('batter')['runs_batter'].sum().sort_values(ascending=False).head(top_n)
        st.dataframe(top_batters, use_container_width=True)

    with col2:
        st.write(f"🎯 Most Wickets")
        top_bowlers = deliv_df.groupby('bowler')['is_wicket'].sum().sort_values(ascending=False).head(top_n)
        st.dataframe(top_bowlers, use_container_width=True)