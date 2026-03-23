import streamlit as st
import pandas as pd
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="Player Comparison | IPL Tracker", layout="wide")

# 2. Database Connection
@st.cache_resource
def init_connection():
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    return create_client(url, key)

supabase = init_connection()

# 3. Data Fetching Functions
@st.cache_data(ttl=3600)
def get_batter_data():
    # Fetching from the advanced view we created in Supabase
    response = supabase.table('batter_stats_advanced').select('*').execute()
    return pd.DataFrame(response.data)

@st.cache_data(ttl=3600)
def get_bowler_data():
    # Fetching from the advanced view we created in Supabase
    response = supabase.table('bowler_stats_advanced').select('*').execute()
    return pd.DataFrame(response.data)

# Load Data
batters_df = get_batter_data()
bowlers_df = get_bowler_data()

# 4. UI Header
st.title("⚔️ Player Comparison")
st.markdown("Compare elite IPL performers across all historical seasons.")

# 5. Tabs for Batters and Bowlers
tab1, tab2 = st.tabs(["🏏 Batsmen Comparison", "⚾ Bowlers Comparison"])

# --- BATSMEN TAB ---
with tab1:
    selected_batters = st.multiselect(
        "Select up to 3 Batters to compare:",
        options=batters_df['batter'].sort_values().unique(),
        default=["V Kohli", "MS Dhoni"] if "V Kohli" in batters_df['batter'].values else None,
        max_selections=3
    )

    if selected_batters:
        comp_b_df = batters_df[batters_df['batter'].isin(selected_batters)]
        
        # Stat Cards
        cols = st.columns(len(selected_batters))
        for i, player in enumerate(selected_batters):
            p_data = comp_b_df[comp_b_df['batter'] == player].iloc[0]
            with cols[i]:
                st.subheader(player)
                st.metric("Total Runs", f"{int(p_data['total_runs']):,}")
                st.metric("Avg / SR", f"{p_data['batting_avg']} / {p_data['strike_rate']}")
                st.write(f"**HS:** {int(p_data['highest_score'])} | **100s/50s:** {int(p_data['hundreds'])}/{int(p_data['fifties'])}")
                st.write(f"**4s/6s:** {int(p_data['fours'])}/{int(p_data['sixes'])}")

        # Radar Chart for Batters
        st.write("---")
        # Normalize data for radar chart to make it look "sleek"
        metrics = ['total_runs', 'strike_rate', 'batting_avg', 'fours', 'sixes']
        radar_list = []
        for _, row in comp_b_df.iterrows():
            for m in metrics:
                radar_list.append(dict(Player=row['batter'], Metric=m.replace('_', ' ').title(), Value=row[m]))
        
        fig_b = px.line_polar(pd.DataFrame(radar_list), r='Value', theta='Metric', color='Player', 
                             line_close=True, template="plotly_dark", title="Batting Profile Comparison")
        fig_b.update_traces(fill='toself', opacity=0.5)
        st.plotly_chart(fig_b, use_container_width=True)

# --- BOWLERS TAB ---
with tab2:
    selected_bowlers = st.multiselect(
        "Select up to 3 Bowlers to compare:",
        options=bowlers_df['bowler'].sort_values().unique(),
        default=["JJ Bumrah", "Rashid Khan"] if "JJ Bumrah" in bowlers_df['bowler'].values else None,
        max_selections=3
    )

    if selected_bowlers:
        comp_bw_df = bowlers_df[bowlers_df['bowler'].isin(selected_bowlers)]
        
        # Stat Cards
        cols_bw = st.columns(len(selected_bowlers))
        for i, player in enumerate(selected_bowlers):
            p_data = comp_bw_df[comp_bw_df['bowler'] == player].iloc[0]
            with cols_bw[i]:
                st.subheader(player)
                st.metric("Wickets", int(p_data['total_wickets']))
                st.metric("Econ / Avg", f"{p_data['economy_rate']} / {p_data['bowling_avg']}")
                st.write(f"**Best:** {int(p_data['best_wickets_match'])} wkts")
                st.write(f"**4w/5w:** {int(p_data['four_fers'])}/{int(p_data['five_fers'])}")

        # Radar Chart for Bowlers
        st.write("---")
        bw_metrics = ['total_wickets', 'economy_rate', 'bowling_avg', 'balls_bowled']
        radar_bw_list = []
        for _, row in comp_bw_df.iterrows():
            for m in bw_metrics:
                radar_bw_list.append(dict(Player=row['bowler'], Metric=m.replace('_', ' ').title(), Value=row[m]))
        
        fig_bw = px.line_polar(pd.DataFrame(radar_bw_list), r='Value', theta='Metric', color='Player', 
                              line_close=True, template="plotly_dark", title="Bowling Profile Comparison")
        fig_bw.update_traces(fill='toself', opacity=0.5)
        st.plotly_chart(fig_bw, use_container_width=True)