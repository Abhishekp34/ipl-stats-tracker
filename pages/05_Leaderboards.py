import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# 1. Setup & Connection
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

st.set_page_config(page_title="IPL Leaderboards", layout="wide")

st.title("🏆 IPL Season Leaderboards")
st.markdown("---")

# 2. Sidebar Filters
st.sidebar.header("Filter Leaderboard")
category = st.sidebar.radio("Select Category", ["Batting", "Bowling"])

# 3. Data Fetching Logic
@st.cache_data(ttl=600)
def get_leaderboard_data(table_name):
    response = supabase.table(table_name).select("*").execute()
    return pd.DataFrame(response.data)

if category == "Batting":
    df = get_leaderboard_data("view_batter_master")
    
    # Batting Metrics
    metric_options = {
        "runs": "Most Runs (Orange Cap)",
        "hs": "Highest Score",
        "avg": "Best Average",
        "sr": "Highest Strike Rate",
        "6s": "Most Sixes",
        "4s": "Most Fours",
        "50s": "Most Fifties",
        "100s": "Most Hundreds",
        "mom_awards": "Most Player of the Match"
    }
    
    sort_col = st.selectbox("Rank by Metric", options=list(metric_options.keys()), 
                            format_func=lambda x: metric_options[x])
    
    # Sort and Clean
    df = df.sort_values(by=sort_col, ascending=False).reset_index(drop=True)
    df.index += 1  # Start rank at 1
    
    # 4. Top 3 Highlight Cards
    top_3 = df.head(3)
    cols = st.columns(3)
    
    for i, (idx, player) in enumerate(top_3.iterrows()):
        with cols[i]:
            st.metric(label=f"#{i+1} {player['player']}", 
                      value=player[sort_col], 
                      delta=player['team'])

    st.markdown("### Full Batting Rankings")
    st.dataframe(df, use_container_width=True)

else:
    df = get_leaderboard_data("view_bowler_master")
    
    # Bowling Metrics
    metric_options = {
        "wkts": "Most Wickets (Purple Cap)",
        "econ": "Best Economy (Low is Better)",
        "dots": "Most Dot Balls",
        "4w": "Most 4-Wicket Hauls",
        "5w": "Most 5-Wicket Hauls"
    }
    
    sort_col = st.selectbox("Rank by Metric", options=list(metric_options.keys()), 
                            format_func=lambda x: metric_options[x])
    
    # Logic: Economy is better when lower, others are better when higher
    is_ascending = True if sort_col == "econ" else False
    
    # Sort and Clean
    df = df.sort_values(by=sort_col, ascending=is_ascending).reset_index(drop=True)
    df.index += 1
    
    # 4. Top 3 Highlight Cards
    top_3 = df.head(3)
    cols = st.columns(3)
    
    for i, (idx, player) in enumerate(top_3.iterrows()):
        with cols[i]:
            st.metric(label=f"#{i+1} {player['player']}", 
                      value=player[sort_col], 
                      delta=player['team'])

    st.markdown("### Full Bowling Rankings")
    st.dataframe(df, use_container_width=True)