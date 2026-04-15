import streamlit as st
import pandas as pd
import os
import plotly.express as px
from supabase import create_client
from dotenv import load_dotenv
import time
from ui_utils import inject_custom_css, get_team_color

# 1. Page Configuration
st.set_page_config(page_title="IPL Player Race", layout="wide")
inject_custom_css()

@st.cache_resource
def init_connection():
    load_dotenv()
    return create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

supabase = init_connection()

@st.cache_data(ttl=3600)
def fetch_all_race_data(table, metric_col):
    all_rows = []
    start = 0
    step = 5000
    
    while True:
        res = supabase.table(table).select("player", "team", "match_seq", metric_col).range(start, start + step - 1).execute()
        if not res.data:
            break
        all_rows.extend(res.data)
        if len(res.data) < step:
            break
        start += step
    
    return pd.DataFrame(all_rows)

def render_race(category):
    table = 'view_top_30_batting_race' if category == "Batting" else 'view_top_30_bowling_race'
    metric_col = 'cumulative_runs' if category == "Batting" else 'cumulative_wickets'
    
    with st.spinner(f"Fetching full {category} history..."):
        full_df = fetch_all_race_data(table, metric_col)

    if full_df.empty:
        st.warning("No data found in the optimized race view.")
        return

    # Permanent Color Map logic remains the same
    player_team_map = full_df.sort_values('match_seq').groupby('player')['team'].last().to_dict()
    color_discrete_map = {p: get_team_color(t) for p, t in player_team_map.items()}

    max_matches = full_df['match_seq'].max()

    col1, col2 = st.columns([1, 4])
    with col1:
        play_btn = st.button(f"▶️ Start {category} Race", key=f"play_btn_{category}")
    with col2:
        selected_seq = st.slider("Timeline", 1, max_matches, max_matches, key=f"sld_{category}")

    chart_holder = st.empty()

    def draw_frame(seq):
        frame_df = full_df[full_df['match_seq'] == seq].nlargest(10, metric_col).sort_values(metric_col, ascending=True)
        
        fig = px.bar(
            frame_df, x=metric_col, y="player", orientation='h',
            text=metric_col, color="player",
            color_discrete_map=color_discrete_map,
            template="plotly_dark",
            title=f"IPL {category} - Match #{seq}"
        )
        
        x_limit = full_df[metric_col].max() * 1.05
        fig.update_layout(
            xaxis_range=[0, x_limit], height=600, showlegend=False,
            yaxis={'categoryorder':'total ascending'},
            transition={'duration': 300, 'easing': 'cubic-in-out'},
            margin=dict(t=50, b=20, l=150, r=50),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        fig.update_traces(textposition='outside', cliponaxis=False, marker_line_color='white', marker_line_width=1)
        chart_holder.plotly_chart(fig, use_container_width=True, key=f"race_plot_{category}_{seq}")

    if play_btn:
        for i in range(1, max_matches + 1, 2): 
            draw_frame(i)
            time.sleep(0.04)
    else:
        draw_frame(selected_seq)

# --- UI EXECUTION ---
st.title("🏃 All-Time Player Race")
t1, t2 = st.tabs(["🏏 Batting Race", "🎾 Bowling Race"])
with t1: render_race("Batting")
with t2: render_race("Bowling")