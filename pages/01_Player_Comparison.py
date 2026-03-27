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

# 3. Data Fetching Functions (UPDATED TO NEW VIEWS)
@st.cache_data(ttl=3600)
def get_batter_data():
    # Changed from batter_stats_advanced to our new high-speed view
    response = supabase.table('view_batter_master').select('*').execute()
    return pd.DataFrame(response.data)

@st.cache_data(ttl=3600)
def get_bowler_data():
    # Changed from bowler_stats_advanced to our new high-speed view
    response = supabase.table('view_bowler_master').select('*').execute()
    return pd.DataFrame(response.data)

# Load Data
batters_df = get_batter_data()
bowlers_df = get_bowler_data()

# 4. UI Header
st.title("⚔️ Player Comparison")
st.markdown("Compare elite IPL performers using optimized historical data.")

# 5. Tabs for Batters and Bowlers
tab1, tab2 = st.tabs(["🏏 Batsmen Comparison", "⚾ Bowlers Comparison"])

# --- BATSMEN TAB ---
with tab1:
    selected_batters = st.multiselect(
        "Select up to 3 Batters to compare:",
        options=batters_df['player'].sort_values().unique(), # Column renamed to 'player'
        default=["V Kohli", "RG Sharma"] if "V Kohli" in batters_df['player'].values else None,
        max_selections=3
    )

    if selected_batters:
        comp_b_df = batters_df[batters_df['player'].isin(selected_batters)]
        
        # Stat Cards
        cols = st.columns(len(selected_batters))
        for i, player in enumerate(selected_batters):
            p_data = comp_b_df[comp_b_df['player'] == player].iloc[0]
            with cols[i]:
                st.subheader(player)
                st.metric("Total Runs", f"{int(p_data['runs']):,}") # Column renamed to 'runs'
                st.metric("Avg / SR", f"{p_data['avg']} / {p_data['sr']}") # Renamed to 'avg' / 'sr'
                st.write(f"**HS:** {int(p_data['hs'])} | **100s/50s:** {int(p_data['100s'])}/{int(p_data['50s'])}")
                st.write(f"**4s/6s:** {int(p_data['4s'])}/{int(p_data['6s'])}")

        # Radar Chart for Batters
        st.write("---")
        # UPDATED METRICS to match new schema
        metrics = ['runs', 'sr', 'avg', '4s', '6s']
        radar_list = []
        
        # Normalization logic to keep the radar chart balanced
        for _, row in comp_b_df.iterrows():
            for m in metrics:
                # We normalize relative to the max in the current selection
                max_val = batters_df[m].max()
                norm_val = (row[m] / max_val) * 100 if max_val != 0 else 0
                radar_list.append(dict(
                    Player=row['player'], 
                    Metric=m.replace('_', ' ').upper(), 
                    Value=norm_val,
                    Actual=row[m]
                ))
        
        fig_b = px.line_polar(pd.DataFrame(radar_list), r='Value', theta='Metric', color='Player', 
                             hover_data=['Actual'], line_close=True, template="plotly_dark", 
                             title="Relative Batting Strength (Percentile)")
        fig_b.update_traces(fill='toself', opacity=0.5)
        st.plotly_chart(fig_b, use_container_width=True)

# --- BOWLERS TAB ---
with tab2:
    selected_bowlers = st.multiselect(
        "Select up to 3 Bowlers to compare:",
        options=bowlers_df['player'].sort_values().unique(),
        default=["JJ Bumrah", "Rashid Khan"] if "JJ Bumrah" in bowlers_df['player'].values else None,
        max_selections=3
    )

    if selected_bowlers:
        comp_bw_df = bowlers_df[bowlers_df['player'].isin(selected_bowlers)]
        
        # Stat Cards
        cols_bw = st.columns(len(selected_bowlers))
        for i, player in enumerate(selected_bowlers):
            p_data = comp_bw_df[comp_bw_df['player'] == player].iloc[0]
            with cols_bw[i]:
                st.subheader(player)
                st.metric("Wickets", int(p_data['wkts'])) # Renamed to 'wkts'
                st.metric("Econ", f"{p_data['econ']}") # Renamed to 'econ'
                st.write(f"**Matches:** {int(p_data['mat'])}")
                st.write(f"**4w/5w:** {int(p_data['4w'])}/{int(p_data['5w'])}")

        # Radar Chart for Bowlers
        st.write("---")
        # Inverting Econ so that LOWER economy looks BETTER (larger) on the radar
        bw_metrics = ['wkts', 'mat', 'dots']
        radar_bw_list = []
        for _, row in comp_bw_df.iterrows():
            for m in bw_metrics:
                max_v = bowlers_df[m].max()
                norm_v = (row[m] / max_v) * 100 if max_v != 0 else 0
                radar_bw_list.append(dict(Player=row['player'], Metric=m.upper(), Value=norm_v, Actual=row[m]))
        
        fig_bw = px.line_polar(pd.DataFrame(radar_bw_list), r='Value', theta='Metric', color='Player', 
                              hover_data=['Actual'], line_close=True, template="plotly_dark", 
                              title="Relative Bowling Strength (Percentile)")
        fig_bw.update_traces(fill='toself', opacity=0.5)
        st.plotly_chart(fig_bw, use_container_width=True)