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
st.markdown("Discover historical matches and top performances delivered on this calendar date.")

# 3. Date Selection
target_date = st.date_input("Select a date:", datetime.date.today())
month = int(target_date.month)
day = int(target_date.day)

@st.cache_data(ttl=3600)
def get_otd_data(m, d):
    # Call the RPC function we created earlier
    matches_res = supabase.rpc('get_matches_by_day_month', {
        'target_month': m, 
        'target_day': d
    }).execute()
    
    matches_df = pd.DataFrame(matches_res.data)
    
    if matches_df.empty:
        return matches_df, pd.DataFrame()

    match_ids = matches_df['match_id'].astype(str).tolist()
    
    # Fetch all deliveries for these specific matches
    deliv_res = supabase.table('deliveries').select(
        'match_id, batter, runs_batter, bowler, wicket_type'
    ).in_('match_id', match_ids).execute()
    
    return matches_df, pd.DataFrame(deliv_res.data)

matches_df, deliv_df = get_otd_data(month, day)

if matches_df.empty:
    st.warning(f"No IPL matches were played on **{target_date.strftime('%B %d')}** in recorded history.")
else:
    # 4. Match List
    st.subheader(f"🏟️ Matches on {target_date.strftime('%B %d')}")
    
    # Display matches in a clean grid
    for _, row in matches_df.iterrows():
        year = pd.to_datetime(row['match_date']).year
        with st.expander(f"**{year}**: {row['team1']} vs {row['team2']}"):
            col1, col2 = st.columns(2)
            col1.write(f"📍 **Venue:** {row['venue']}")
            col1.write(f"🏙️ **City:** {row['city']}")
            col2.success(f"🏆 **Winner:** {row['winner']}")

    # 5. Star Performances of the Day
    st.divider()
    st.subheader("🌟 Top Performances on this Date")
    
    if not deliv_df.empty:
        # Calculate scores for these matches
        match_scores = deliv_df.groupby(['match_id', 'batter'])['runs_batter'].sum().reset_index()
        high_scores = match_scores[match_scores['runs_batter'] >= 50].sort_values('runs_batter', ascending=False)
        
        # Calculate wickets for these matches
        valid_wickets = ['bowled', 'caught', 'lbw', 'stumped', 'caught and bowled']
        deliv_df['is_wicket'] = deliv_df['wicket_type'].isin(valid_wickets)
        match_wickets = deliv_df.groupby(['match_id', 'bowler'])['is_wicket'].sum().reset_index()
        top_bowlers = match_wickets[match_wickets['is_wicket'] >= 3].sort_values('is_wicket', ascending=False)

        col_bat, col_bowl = st.columns(2)
        
        with col_bat:
            st.write("### 🏏 Batting Heroes")
            if not high_scores.empty:
                for _, s in high_scores.iterrows():
                    st.info(f"**{s['batter']}** scored **{int(s['runs_batter'])}** runs")
            else:
                st.write("No 50+ scores on this date.")

        with col_bowl:
            st.write("### 🎯 Bowling Heroes")
            if not top_bowlers.empty:
                for _, w in top_bowlers.iterrows():
                    st.error(f"**{w['bowler']}** took **{int(w['is_wicket'])}** wickets")
            else:
                st.write("No 3+ wicket hauls on this date.")

    # 6. Cumulative Leaders for this Date
    st.divider()
    st.subheader(f"📊 All-Time {target_date.strftime('%B %d')} Leaders")
    st.info("Total stats accumulated by players across all matches played on this specific calendar date.")
    
    c1, c2 = st.columns(2)
    with c1:
        st.write("**Most Runs Today**")
        all_time_bat = deliv_df.groupby('batter')['runs_batter'].sum().sort_values(ascending=False).head(10)
        st.table(all_time_bat)

    with c2:
        st.write("**Most Wickets Today**")
        all_time_bowl = deliv_df.groupby('bowler')['is_wicket'].sum().sort_values(ascending=False).head(10)
        st.table(all_time_bowl)