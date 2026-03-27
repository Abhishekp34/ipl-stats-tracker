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

# 3. Data Fetching Functions (Fetching from Materialized Views)
@st.cache_data(ttl=3600)
def get_master_data(table_name):
    # The database already did the hard work (Average, Strike Rate, HS)
    response = supabase.table(table_name).select('*').execute()
    return pd.DataFrame(response.data)

# Load Data
batters_df = get_master_data('view_batter_master')
bowlers_df = get_master_data('view_bowler_master')

# 4. UI Header
st.title("⚔️ Player Comparison")
st.markdown("Compare elite performers using **pre-computed, official-grade statistics**.")

# 5. Tabs
tab1, tab2 = st.tabs(["🏏 Batsmen Comparison", "⚾ Bowlers Comparison"])

# --- BATSMEN TAB ---
with tab1:
    selected_batters = st.multiselect(
        "Select up to 3 Batters to compare:",
        options=batters_df['player'].sort_values().unique(),
        default=["V Kohli", "RG Sharma"] if "V Kohli" in batters_df['player'].values else None,
        max_selections=3
    )

    if selected_batters:
        comp_b_df = batters_df[batters_df['player'].isin(selected_batters)]
        
        cols = st.columns(len(selected_batters))
        for i, player in enumerate(selected_batters):
            p_data = comp_b_df[comp_b_df['player'] == player].iloc[0]
            with cols[i]:
                st.subheader(player)
                # Displaying direct database values
                st.metric("Total Runs", f"{int(p_data['runs']):,}")
                st.metric("Avg / SR", f"{p_data['avg']} / {p_data['sr']}")
                st.write(f"**HS:** {p_data['hs']} | **Team:** {p_data['team']}")
                st.write(f"**100s/50s:** {int(p_data['100s'])}/{int(p_data['50s'])}")
                st.write(f"**4s/6s:** {int(p_data['4s'])}/{int(p_data['6s'])}")

        st.divider()
        # Radar Chart: Metrics normalized to the all-time high for scannability
        metrics = ['runs', 'sr', 'avg', '4s', '6s']
        radar_list = []
        for _, row in comp_b_df.iterrows():
            for m in metrics:
                max_val = batters_df[m].max()
                norm_val = (row[m] / max_val) * 100 if max_val != 0 else 0
                radar_list.append(dict(Player=row['player'], Metric=m.upper(), Value=norm_val, Actual=row[m]))
        
        fig_b = px.line_polar(pd.DataFrame(radar_list), r='Value', theta='Metric', color='Player', 
                             hover_data=['Actual'], line_close=True, template="plotly_dark", 
                             title="Relative Batting Strength (Percentile)")
        fig_b.update_traces(fill='toself', opacity=0.4)
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
        
        cols_bw = st.columns(len(selected_bowlers))
        for i, player in enumerate(selected_bowlers):
            p_data = comp_bw_df[comp_bw_df['player'] == player].iloc[0]
            with cols_bw[i]:
                st.subheader(player)
                st.metric("Wickets", int(p_data['wkts']))
                st.metric("Economy", p_data['econ'])
                st.write(f"**Matches:** {int(p_data['mat'])} | **Team:** {p_data['team']}")
                st.write(f"**4w/5w:** {int(p_data['4w'])}/{int(p_data['5w'])}")

        st.divider()
        # Bowler Metrics
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
        fig_bw.update_traces(fill='toself', opacity=0.4)
        st.plotly_chart(fig_bw, use_container_width=True)