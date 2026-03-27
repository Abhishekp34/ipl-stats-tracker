import streamlit as st
import pandas as pd
import os
import plotly.graph_objects as go
from supabase import create_client
from dotenv import load_dotenv

st.set_page_config(page_title="Team Rivalry | IPL Tracker", layout="wide")

@st.cache_resource
def init_connection():
    load_dotenv()
    return create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

supabase = init_connection()

st.title("⚔️ Team Rivalry: Head-to-Head")
st.markdown("Select two franchises to see their historical dominance and legendary performers.")

# 1. Fetch Unique Teams
@st.cache_data
def get_teams():
    res = supabase.table('matches').select('team1').execute()
    return sorted(list(set([r['team1'] for r in res.data])))

teams = get_teams()

# 2. Selection UI
c1, c2 = st.columns(2)
team_a = c1.selectbox("Select Team 1:", teams, index=0)
team_b = c2.selectbox("Select Team 2:", [t for t in teams if t != team_a], index=0)

# 3. Fetch Rivalry Data
@st.cache_data
def fetch_rivalry(t1, t2):
    # Sort names to match the alphabetical 'side_a, side_b' logic in SQL
    a, b = sorted([t1, t2])
    res = supabase.table('view_team_rivalry_master').select('*').eq('side_a', a).eq('side_b', b).execute()
    return res.data[0] if res.data else None

data = fetch_rivalry(team_a, team_b)

if data:
    # Determine which team is which for the UI
    is_a_first = team_a == data['side_a']
    t1_wins = data['team1_wins'] if is_a_first else data['team2_wins']
    t2_wins = data['team2_wins'] if is_a_first else data['team1_wins']

    # --- HEAD-TO-HEAD BATTLE BAR ---
    st.subheader(f"Total Matches: {data['total_matches']}")
    
    # Custom CSS for the win bar
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=['Rivalry'], x=[t1_wins], name=team_a, orientation='h',
        marker=dict(color='#F1C40F'), text=f"{team_a}: {t1_wins}"
    ))
    fig.add_trace(go.Bar(
        y=['Rivalry'], x=[t2_wins], name=team_b, orientation='h',
        marker=dict(color='#2C3E50'), text=f"{team_b}: {t2_wins}"
    ))
    fig.update_layout(
        barmode='stack', height=150, showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)', xaxis_visible=False, yaxis_visible=False
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- KEY PERFORMERS ---
    st.divider()
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.write("### 🏏 Top Run Getter")
        st.info(f"**{data['top_batter']}** has scored **{int(data['max_runs'])}** runs in this rivalry.")
        
    with col_p2:
        st.write("### 🎯 Leading Wicket Taker")
        st.error(f"**{data['top_bowler']}** has taken **{int(data['max_wickets'])}** wickets in these clashes.")

    # --- RECENT MATCHES ---
    st.write("### 📝 Recent Encounters")
    matches_res = supabase.table('matches').select('*').or_(
        f"and(team1.eq.{team_a},team2.eq.{team_b}),and(team1.eq.{team_b},team2.eq.{team_a})"
    ).order('match_date', desc=True).limit(5).execute()
    
    m_df = pd.DataFrame(matches_res.data)
    if not m_df.empty:
        st.table(m_df[['match_date', 'venue', 'winner']])

else:
    st.warning("No historical matches found between these two teams.")