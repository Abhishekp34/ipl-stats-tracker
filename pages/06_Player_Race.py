import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

st.set_page_config(page_title="IPL Matrix Race", layout="wide")

@st.cache_data
def get_matrix_data():
    # Fetch the 600 rows (one per player)
    response = supabase.table("view_player_race_matrix").select("*").execute()
    raw_data = response.data
    
    # We want to create the "Top 10" for every match
    num_matches = len(raw_data[0]['history'])
    frames = []

    # Step through every 5th match to keep it smooth (approx 117 frames)
    for m_idx in range(0, num_matches, 5):
        current_frame_players = []
        for p in raw_data:
            current_frame_players.append({
                'player': p['player'],
                'cumulative_runs': p['history'][m_idx],
                'match_num': m_idx + 1
            })
        
        # Sort and take top 10 for this frame
        temp_df = pd.DataFrame(current_frame_players)
        top_10 = temp_df.nlargest(10, 'cumulative_runs')
        frames.append(top_10)
        
    return pd.concat(frames)

df = get_matrix_data()

if not df.empty:
    st.title("🏆 The Ultimate IPL Run Race")

    # 1. Stable Color Map
    unique_players = df['player'].unique()
    color_map = {p: px.colors.qualitative.Alphabet[i % 26] for i, p in enumerate(unique_players)}

    # 2. CREATE THE BASE CHART
    fig = px.bar(
        df,
        x="cumulative_runs",
        y="player",
        animation_frame="match_num",
        animation_group="player",
        color="player",
        color_discrete_map=color_map,
        orientation='h',
        range_x=[0, 9000],
        template="plotly_dark",
        height=600,
        # This is the secret: include player in the hover so Plotly tracks it better
        hover_name="player" 
    )

    # 3. FIX LABELS & STOP THE "STUCK" NAMES
    fig.update_layout(
        yaxis={
            'categoryorder': 'total ascending',
            'title': '',
            'automargin': True
        },
        xaxis={'title': 'Total Career Runs'},
        showlegend=False,
        margin=dict(l=150, r=100, t=50, b=50),
        
        # FIX: Remove manual 'updatemenus' to fix the double button.
        # Plotly's default button is safer. We only customize the speed here.
    )

    # FIX: Force the labels to refresh by setting redraw=True in the animation settings
    # This is why your names were sticking!
    fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 100
    fig.layout.updatemenus[0].buttons[0].args[1]['frame']['redraw'] = True # CRITICAL
    fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 50

    # 4. SHOW NUMBERS ON THE RIGHT
    fig.update_traces(
        texttemplate='%{x}', 
        textposition='outside',
        cliponaxis=False
    )

    st.plotly_chart(fig, use_container_width=True)