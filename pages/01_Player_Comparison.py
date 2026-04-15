import streamlit as st
import pandas as pd
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import plotly.express as px
from ui_utils import inject_custom_css, styled_stat_card

# 1. Page Configuration
st.set_page_config(page_title="Player Comparison | IPL Tracker", layout="wide")
inject_custom_css()

# Custom CSS for centered, professional stat cards
st.markdown("""
    <style>
    .comparison-container { text-align: center; padding: 10px; border-radius: 10px; background-color: #1e1e1e; margin-bottom: 20px; }
    .stat-label { font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1.2px; margin-top: 15px; margin-bottom: 2px; }
    .stat-value { font-size: 1.6rem; font-weight: bold; color: #F1C40F; margin-bottom: 10px; }
    .player-header { font-size: 2.2rem; font-weight: bold; color: white; margin-bottom: 20px; border-bottom: 2px solid #333; padding-bottom: 10px; }
    .team-badge { font-size: 0.9rem; color: #bbb; font-style: italic; }
    </style>
""", unsafe_allow_html=True)

# 2. Database Connection
@st.cache_resource
def init_connection():
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    return create_client(url, key)

supabase = init_connection()

# 3. Session State for Dynamic Players
if 'num_players' not in st.session_state:
    st.session_state.num_players = 2

# 4. Data Fetching
@st.cache_data(ttl=3600)
def get_master_data(table_name):
    response = supabase.table(table_name).select('*').execute()
    return pd.DataFrame(response.data)

batters_df = get_master_data('view_batter_master')
bowlers_df = get_master_data('view_bowler_master')

# 5. UI Header
st.title("⚔️ Player Comparison")
st.markdown("Compare elite performers with centered, side-by-side analytics.")

# 6. Tabs
tab1, tab2 = st.tabs(["🏏 Batsmen Comparison", "⚾ Bowlers Comparison"])

# Helper function to render a player column
def render_player_column(p_data, is_batter=True):
    with st.container():
        st.markdown(f"<div class='player-header'>{p_data['player']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='team-badge'>{p_data['team']}</div>", unsafe_allow_html=True)
        
        if is_batter:
            stats = [
                ("Matches", int(p_data['mat'])),
                ("Total Runs", f"{int(p_data['runs']):,}"),
                ("Not Outs", int(p_data['not_outs'])),
                ("Avg / SR", f"{p_data['avg']} / {p_data['sr']}"),
                ("Highest Score", p_data['hs']),
                ("100s / 50s", f"{int(p_data['100s'])} / {int(p_data['50s'])}"),
                ("4s / 6s", f"{int(p_data['4s'])} / {int(p_data['6s'])}"),
                ("POTM Awards", int(p_data['potm']))
            ]
        else:
            stats = [
                ("Matches", int(p_data['mat'])),
                ("Total Wickets", int(p_data['wkts'])),
                ("Economy", p_data['econ']),
                ("Dots", f"{int(p_data['dots']):,}"),
                ("4w / 5w", f"{int(p_data['4w'])} / {int(p_data['5w'])}")
            ]
            
        for label, value in stats:
            st.markdown(f"<p class='stat-label'>{label}</p><p class='stat-value'>{value}</p>", unsafe_allow_html=True)

# --- BATSMEN TAB ---
with tab1:
    # Selection Area
    sel_cols = st.columns(st.session_state.num_players)
    selected_b = []
    
    for i in range(st.session_state.num_players):
        with sel_cols[i]:
            choice = st.selectbox(f"Select Batter {i+1}", batters_df['player'].sort_values(), key=f"bat_{i}", index=i)
            selected_b.append(choice)
    
    # Add/Remove Player Controls
    c1, c2, _ = st.columns([1, 1, 4])
    if st.session_state.num_players < 3:
        if c1.button("➕ Add Player", key="add_b"):
            st.session_state.num_players += 1
            st.rerun()
    if st.session_state.num_players > 2:
        if c2.button("➖ Remove", key="rem_b"):
            st.session_state.num_players -= 1
            st.rerun()

    st.divider()

    # Comparison Area
    if selected_b:
        comp_cols = st.columns(len(selected_b))
        for i, name in enumerate(selected_b):
            p_data = batters_df[batters_df['player'] == name].iloc[0]
            with comp_cols[i]:
                render_player_column(p_data, is_batter=True)
    st.divider()
st.subheader("📈 Season-by-Season Performance")

# Fetch Season Data
season_res = supabase.table('view_player_season_stats').select('*').in_('player', selected_b).execute()
season_df = pd.DataFrame(season_res.data)

if not season_df.empty:
    # Ensure season is sorted chronologically
    season_df = season_df.sort_values(['season', 'player'])
    
    fig_season = px.line(
        season_df, 
        x='season', 
        y='season_runs', 
        color='player',
        markers=True,
        line_shape='spline',
        template="plotly_dark",
        labels={'season_runs': 'Runs Scored', 'season': 'Year'},
        color_discrete_sequence=['#F1C40F', '#E74C3C', '#3498DB'] # Gold, Red, Blue
    )
    
    fig_season.update_layout(
        hovermode="x unified",
        yaxis=dict(showgrid=False),
        xaxis=dict(tickmode='linear')
    )
    
    st.plotly_chart(fig_season, use_container_width=True)

# --- BOWLERS TAB ---
with tab2:
    sel_cols_bw = st.columns(st.session_state.num_players)
    selected_bw = []
    
    for i in range(st.session_state.num_players):
        with sel_cols_bw[i]:
            choice = st.selectbox(f"Select Bowler {i+1}", bowlers_df['player'].sort_values(), key=f"bowl_{i}", index=i)
            selected_bw.append(choice)

    st.divider()

    if selected_bw:
        comp_cols_bw = st.columns(len(selected_bw))
        for i, name in enumerate(selected_bw):
            p_data = bowlers_df[bowlers_df['player'] == name].iloc[0]
            with comp_cols_bw[i]:
                render_player_column(p_data, is_batter=False)