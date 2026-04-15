import streamlit as st
import pandas as pd
import os
import plotly.graph_objects as go
from supabase import create_client
from dotenv import load_dotenv
from ui_utils import inject_custom_css, styled_stat_card

st.set_page_config(page_title="Team Rivalry | IPL Tracker", layout="wide")
inject_custom_css()

@st.cache_resource
def init_connection():
    load_dotenv()
    return create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

supabase = init_connection()

st.title("⚔️ Team Rivalry: Head-to-Head")
st.markdown("Select two franchises to see their historical dominance and legendary performers.")

# 1. Fetch Unique Teams (Updated to use the CLEAN view)
@st.cache_data
def get_teams():
    # Using the master view ensures we only see cleaned, standardized names
    res = supabase.table('view_batter_master').select('team').execute()
    return sorted(list(set([r['team'] for r in res.data if r['team']])))

teams = get_teams()

# 2. Selection UI
c1, c2 = st.columns(2)
team_a = c1.selectbox("Select Team 1:", teams, index=0)
team_b = c2.selectbox("Select Team 2:", [t for t in teams if t != team_a], index=0)

# 3. Fetch Rivalry Data
@st.cache_data
def fetch_rivalry(t1, t2):
    a, b = sorted([t1, t2])
    res = supabase.table('view_team_rivalry_master').select('*').eq('side_a', a).eq('side_b', b).execute()
    return res.data[0] if res.data else None

data = fetch_rivalry(team_a, team_b)

if data:
    is_a_first = team_a == data['side_a']
    t1_wins = data['team1_wins'] if is_a_first else data['team2_wins']
    t2_wins = data['team2_wins'] if is_a_first else data['team1_wins']

    # --- IMPROVED HEAD-TO-HEAD BATTLE BAR ---
    st.subheader(f"Total Matches: {data['total_matches']}")
    total = data['total_matches']

    fig = go.Figure()

    # Team 1 Bar
    fig.add_trace(go.Bar(
        y=['Rivalry'], x=[t1_wins], name=team_a, orientation='h',
        marker=dict(color='#F1C40F', line=dict(color='white', width=1)),
        text=f"<b>{team_a}</b><br>{t1_wins} Wins",
        textposition='inside',
        insidetextanchor='middle',  # <--- FIXED: Changed 'center' to 'middle'
        textfont=dict(size=16, color='black'),
        hoverinfo='none'
    ))

    # Team 2 Bar
    fig.add_trace(go.Bar(
        y=['Rivalry'], x=[t2_wins], name=team_b, orientation='h',
        marker=dict(color='#2C3E50', line=dict(color='white', width=1)),
        text=f"<b>{team_b}</b><br>{t2_wins} Wins",
        textposition='inside',
        insidetextanchor='middle',  # <--- FIXED: Changed 'center' to 'middle'
        textfont=dict(size=16, color='white'),
        hoverinfo='none'
    ))

    fig.update_layout(
        barmode='stack',
        height=120,
        showlegend=False,
        margin=dict(l=0, r=0, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(visible=False, range=[0, total]),
        yaxis=dict(visible=False),
        bargap=0.05
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # --- KEY PERFORMERS ---
    st.divider()
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.write("### 🏏 Top Run Getter")
        top_batter = data.get('top_batter') or "N/A"
        max_runs = int(data.get('max_runs') or 0)
        st.info(f"**{top_batter}** has scored **{max_runs}** runs in this rivalry.")
        
    with col_p2:
        st.write("### 🎯 Leading Wicket Taker")
        top_bowler = data.get('top_bowler') or "N/A"
        max_wickets = int(data.get('max_wickets') or 0)
        st.error(f"**{top_bowler}** has taken **{max_wickets}** wickets in these clashes.")

    # --- RECENT MATCHES ---
    st.write("### 📝 Recent Encounters")
    # Wrap team names in double quotes to handle spaces (e.g., "Deccan Chargers")
    matches_res = supabase.table('matches').select('*').or_(
        f'and(team1.eq."{team_a}",team2.eq."{team_b}"),and(team1.eq."{team_b}",team2.eq."{team_a}")'
    ).order('match_date', desc=True).limit(5).execute()
    
    m_df = pd.DataFrame(matches_res.data)
    if not m_df.empty:
        st.table(m_df[['match_date', 'venue', 'winner']])

else:
    st.warning("No historical matches found between these two teams.")