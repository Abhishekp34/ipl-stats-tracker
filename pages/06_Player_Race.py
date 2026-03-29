import streamlit as st
import pandas as pd
import os
import plotly.express as px
from supabase import create_client
from dotenv import load_dotenv
import time

# 1. Initialize Connection (Globally defined to fix "supabase is not defined")
@st.cache_resource
def init_connection():
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    return create_client(url, key)

supabase = init_connection()

# 2. Player Color Mapping (Globally defined to fix "PLAYER_COLORS is not defined")
@st.cache_resource
def get_player_colors():
    return {
        "Virat Kohli": "#E41B17", "MS Dhoni": "#FFFF00", "Rohit Sharma": "#004BA0",
        "S Dhawan": "#F2A04F", "DA Warner": "#FFD700", "SK Raina": "#FFCC00",
        "AB de Villiers": "#EC1C24", "CH Gayle": "#339933", "RV Uthappa": "#221E1F"
    }

PLAYER_COLORS = get_player_colors()

def display_race_plot(container, seq, table, metric_col, category):
    """Fetches data and renders the sliding bar chart"""
    res = supabase.table(table).select("player", metric_col) \
        .eq("match_seq", seq) \
        .order(metric_col, desc=True) \
        .limit(10) \
        .execute()
    
    df = pd.DataFrame(res.data)
    
    if not df.empty:
        # Highest at top: Plotly Y-axis goes bottom-to-top, 
        # so we sort ascending=True to put the leader at the top of the screen.
        df = df.sort_values(metric_col, ascending=True)
        
        fig = px.bar(
            df,
            x=metric_col,
            y="player",
            orientation='h',
            text=metric_col,
            color="player",
            color_discrete_map=PLAYER_COLORS,
            template="plotly_dark",
            title=f"IPL {category} - Match #{seq}"
        )
        
        x_limit = 9000 if category == "Batting" else 220
        
        fig.update_layout(
            xaxis_range=[0, x_limit],
            height=500,
            showlegend=False,
            # This 'categoryorder' is what makes the bars swap places smoothly
            yaxis={'categoryorder':'total ascending'},
            # Smooth transition duration in milliseconds
            transition={'duration': 200, 'easing': 'cubic-in-out'},
            margin=dict(t=50, b=20, l=150, r=50)
        )
        
        # Ensures numbers stay outside the bars for readability
        fig.update_traces(textposition='outside', cliponaxis=False)
        
        container.plotly_chart(fig, use_container_width=True, key=f"race_{category}_{seq}")

def render_race(category):
    table = 'view_top_30_batting_race' if category == "Batting" else 'view_top_30_bowling_race'
    metric_col = 'cumulative_runs' if category == "Batting" else 'cumulative_wickets'
    
    col1, col2 = st.columns([1, 4])
    with col1:
        play_btn = st.button(f"▶️ Start {category} Race", key=f"btn_{category}")
    with col2:
        selected_seq = st.slider("Timeline", 1, 1169, 1169, key=f"sld_{category}")

    chart_holder = st.empty()

    if play_btn:
        # Step=5 makes the animation significantly smoother for 1000+ matches
        for i in range(1, 1170, 5): 
            display_race_plot(chart_holder, i, table, metric_col, category)
            time.sleep(0.001) 
    else:
        display_race_plot(chart_holder, selected_seq, table, metric_col, category)

# --- UI EXECUTION ---
st.set_page_config(page_title="IPL Player Race", layout="wide")
st.title("🏃 All-Time Player Race")

t1, t2 = st.tabs(["🏏 Batting Race", "🎾 Bowling Race"])
with t1: render_race("Batting")
with t2: render_race("Bowling")