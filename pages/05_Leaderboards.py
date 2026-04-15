import streamlit as st
import pandas as pd
import os
from supabase import create_client
from dotenv import load_dotenv
from ui_utils import inject_custom_css, styled_stat_card

# 1. Page Configuration
st.set_page_config(page_title="IPL Leaderboards", layout="wide")
inject_custom_css()

@st.cache_resource
def init_connection():
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    return create_client(url, key)

supabase = init_connection()

# 2. Data Fetching (Directly from Materialized Views)
@st.cache_data(ttl=3600)
def get_leaderboard(category):
    table = 'view_batter_master' if category == "Batting" else 'view_bowler_master'
    # Sort by primary metric (Runs or Wickets) automatically
    order_col = 'runs' if category == "Batting" else 'wkts'
    
    res = supabase.table(table).select('*').order(order_col, desc=True).execute()
    return pd.DataFrame(res.data)

# 3. Sidebar Filters
st.sidebar.header("Filter Leaderboard")
category = st.sidebar.radio("Select Category:", ["Batting", "Bowling"])

df = get_leaderboard(category)

# 4. UI: Podium (Top 3 Players)
st.title(f"🏆 IPL All-Time {category} Leaderboard")

if not df.empty:
    top_3 = df.head(3)
    cols = st.columns(3)
    
    # Custom Labels based on Category
    metric_label = "Total Runs" if category == "Batting" else "Total Wickets"
    metric_key = "runs" if category == "Batting" else "wkts"
    
    for i, (col, (_, player)) in enumerate(zip(cols, top_3.iterrows())):
        with col:
            st.markdown(f"### #{i+1} {player['player']}")
            st.metric(metric_label, f"{int(player[metric_key]):,}")
            st.caption(f"🏃 **Team:** {player['team']}")
            if category == "Batting":
                st.write(f"**Avg:** {player['avg']} | **SR:** {player['sr']}")
            else:
                st.write(f"**Econ:** {player['econ']} | **Mat:** {player['mat']}")

    # 5. Full Rankings Table
    st.divider()
    st.subheader(f"Full {category} Rankings")
    
    # Search functionality
    search_query = st.text_input("🔍 Search Player:", placeholder="e.g. MS Dhoni")
    
    if search_query:
        df_display = df[df['player'].str.contains(search_query, case=False, na=False)]
    else:
        df_display = df

    # Formatting for better readability
    if category == "Batting":
        # Ensure 'hs' (Highest Score) remains a string to keep the '*'
        df_display = df_display[['player', 'team', 'mat', 'runs', 'hs', 'avg', 'sr', '4s', '6s', '100s', '50s']]
    else:
        df_display = df_display[['player', 'team', 'mat', 'wkts', 'econ', 'dots', '4w', '5w']]

    st.dataframe(
        df_display.reset_index(drop=True), 
        use_container_width=True,
        height=600
    )

else:
    st.error("Data not found. Please ensure the Materialized Views are created in Supabase.")