import streamlit as st
import pandas as pd
import os
import sys
import time
from supabase import create_client
from dotenv import load_dotenv

# Ensure we can import race_utils from the root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from race_utils import d3_bar_chart_race
from ui_utils import inject_custom_css

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
        if not res.data: break
        all_rows.extend(res.data)
        if len(res.data) < step: break
        start += step
    return pd.DataFrame(all_rows)

def render_race(category):
    table = 'view_top_30_batting_race' if category == "Batting" else 'view_top_30_bowling_race'
    metric_col = 'cumulative_runs' if category == "Batting" else 'cumulative_wickets'
    
    with st.spinner(f"Loading {category} data..."):
        full_df = fetch_all_race_data(table, metric_col)

    if full_df.empty:
        st.error("No data available.")
        return

    st.markdown(f"### 🏃 All-Time {category} Leaderboard Race")
    st.info("The D3.js engine handles rank-swapping and bar sliding for a broadcast-quality experience.")

    if st.button(f"▶️ Launch {category} Race Animation", key=f"btn_{category}", use_container_width=True):
        # We pass the entire dataframe. The JS handles the animation frames.
        # To make it even smoother, we can filter to only the Top 10 per match here if needed.
        d3_bar_chart_race(full_df, metric_col, category)
    else:
        st.write("Click the button above to start the smooth animation. Use the tabs to switch categories.")

# --- UI EXECUTION ---
st.title("🏃 All-Time Player Race")
t1, t2 = st.tabs(["🏏 Batting Race", "🎾 Bowling Race"])
with t1: render_race("Batting")
with t2: render_race("Bowling")