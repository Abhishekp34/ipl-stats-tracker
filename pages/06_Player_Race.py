import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

st.set_page_config(page_title="IPL Race Timeline", layout="wide")

# UI Toggle for Category
st.title("🏆 The Ultimate IPL Race")
category = st.selectbox("Select Race Category:", ["Runs (Batters)", "Wickets (Bowlers)"])

@st.cache_data(show_spinner=False)
def get_matrix_data(table_name, col_name):
    response = supabase.table(table_name).select("*").execute()
    raw_data = response.data
    
    if not raw_data:
        return pd.DataFrame()

    num_matches = len(raw_data[0]['history'])
    frames = []

    # Every 10th match for smooth performance
    for m_idx in range(0, num_matches, 10):
        current_frame = []
        for p in raw_data:
            current_frame.append({
                'player': p['player'],
                'value': p['history'][m_idx],
                'match_num': m_idx + 1
            })
        
        temp_df = pd.DataFrame(current_frame)
        top_10 = temp_df.nlargest(10, 'value')
        frames.append(top_10)
        
    return pd.concat(frames)

# Logic to switch data source
if category == "Runs (Batters)":
    table = "view_player_race_matrix"
    label = "Total Career Runs"
    max_val = 9000
else:
    table = "view_bowler_race_matrix"
    label = "Total Career Wickets"
    max_val = 300

df = get_matrix_data(table, label)

if not df.empty:
    # Stable Color Map
    unique_players = df['player'].unique()
    color_map = {p: px.colors.qualitative.Alphabet[i % 26] for i, p in enumerate(unique_players)}

    fig = px.bar(
        df,
        x="value",
        y="player",
        animation_frame="match_num",
        animation_group="player",
        color="player",
        color_discrete_map=color_map,
        orientation='h',
        range_x=[0, max_val],
        template="plotly_dark",
        height=650,
        hover_name="player"
    )

    # UI Cleanup & Fix "Stuck Names"
    fig.update_layout(
        yaxis={'categoryorder': 'total ascending', 'title': '', 'automargin': True},
        xaxis={'title': label},
        showlegend=False,
        margin=dict(l=150, r=100, t=50, b=50),
    )

    # Force Animation Settings
    fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 100
    fig.layout.updatemenus[0].buttons[0].args[1]['frame']['redraw'] = True # Forces labels to update
    fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 50

    # Show numbers outside bars
    fig.update_traces(
        texttemplate='%{x}', 
        textposition='outside',
        cliponaxis=False
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.error(f"Please run the {category} SQL Materialized View in Supabase.")