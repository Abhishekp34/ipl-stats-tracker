import streamlit as st
import pandas as pd
import os
import plotly.express as px
from supabase import create_client
from dotenv import load_dotenv

# 1. Page Configuration
st.set_page_config(page_title="Player Profile | IPL Tracker", layout="wide")

@st.cache_resource
def init_connection():
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    return create_client(url, key)

supabase = init_connection()

# 2. Fast Name Loader (Prevents Timeout)
@st.cache_data(ttl=86400)
def list_all_players():
    # We fetch from the View which is much smaller than the deliveries table
    try:
        res = supabase.table('batter_stats_advanced').select('batter').execute()
        return sorted([r['batter'] for r in res.data])
    except Exception:
        # Fallback list if the database is timing out
        return ["V Kohli", "MS Dhoni", "RG Sharma", "DA Warner", "S Dhawan", "AB de Villiers"]

all_names = list_all_players()

# 3. Targeted Data Fetching
@st.cache_data(ttl=3600)
def get_player_full_data(name):
    # Fetch ball-by-ball for the specific player only
    d_res = supabase.table('deliveries').select('*').or_(f'batter.eq."{name}",bowler.eq."{name}"').execute()
    d_df = pd.DataFrame(d_res.data)
    
    if d_df.empty: return pd.DataFrame()
    
    # Fetch specific Match years for this player's games
    m_ids = d_df['match_id'].unique().tolist()
    m_res = supabase.table('matches').select('match_id, match_date').in_('match_id', m_ids).execute()
    m_df = pd.DataFrame(m_res.data)
    m_df['year'] = pd.to_datetime(m_df['match_date']).dt.year
    
    return d_df.merge(m_df, on='match_id')

# 4. Main UI
st.title("👤 Player Resume")
st.markdown("Enter a player's name to see their IPL career journey.")

# Aesthetic Search Box (Starts blank)
player_name = st.selectbox(
    "Search Player:", 
    options=all_names, 
    index=None, 
    placeholder="e.g. V Kohli",
    help="Type to filter the list of all-time IPL players."
)

if player_name:
    # Comparison Toggle
    compare_on = st.sidebar.checkbox("⚔️ Enable Comparison Mode")
    p2_name = None
    if compare_on:
        p2_name = st.sidebar.selectbox("Compare with:", [n for n in all_names if n != player_name], index=None)

    def render_profile(name, target_container):
        with st.spinner(f"Loading {name}'s career stats..."):
            df = get_player_full_data(name)
            
            if df.empty:
                target_container.warning(f"No match data found for {name}.")
                return

            # --- CALCULATIONS ---
            batting_df = df[df['batter'] == name]
            total_runs = int(batting_df['runs_batter'].sum())
            fours = int(len(batting_df[batting_df['runs_batter'] == 4]))
            sixes = int(len(batting_df[batting_df['runs_batter'] == 6]))
            
            # Wickets logic
            bowling_wkts = ['bowled', 'caught', 'lbw', 'stumped', 'caught and bowled']
            total_wkts = len(df[(df['bowler'] == name) & (df['wicket_type'].isin(bowling_wkts))])

            # --- UI: METRIC CARDS ---
            with target_container.container(border=True):
                st.subheader(f"🏆 {name}")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Runs", f"{total_runs:,}")
                m2.metric("Wickets", total_wkts)
                m3.metric("Fours", fours)
                m4.metric("Sixes", sixes)

            # --- UI: SEASON & OPPONENT CHARTS ---
            st.divider()
            col_a, col_b = st.columns(2)
            
            with col_a:
                if total_runs > 50:
                    st.write("### 📈 Runs by Season")
                    season_stats = batting_df.groupby('year')['runs_batter'].sum().reset_index()
                    fig_season = px.bar(
                        season_stats, x='year', y='runs_batter', text='runs_batter',
                        template="plotly_dark", color_discrete_sequence=['#E74C3C']
                    )
                    fig_season.update_traces(width=0.8, textposition='outside', cliponaxis=False)
                    fig_season.update_layout(xaxis=dict(type='category'), yaxis_visible=False)
                    st.plotly_chart(fig_season, use_container_width=True)
            
            with col_b:
                if total_runs > 50:
                    st.write("### ⚔️ Runs by Opponent")
                    # Group by bowling_team to see who they score against most
                    opp_stats = batting_df.groupby('bowling_team')['runs_batter'].sum().reset_index()
                    opp_stats = opp_stats.sort_values('runs_batter', ascending=False)
                    
                    fig_opp = px.bar(
                        opp_stats, x='bowling_team', y='runs_batter', text='runs_batter',
                        template="plotly_dark", color_discrete_sequence=['#3498DB']
                    )
                    fig_opp.update_traces(width=0.8, textposition='outside', cliponaxis=False)
                    fig_opp.update_layout(yaxis_visible=False)
                    st.plotly_chart(fig_opp, use_container_width=True)

        # --- UI: CONSISTENCY ---
        st.divider()
        if total_runs > 0:
            st.write("### 🎯 Score Consistency (Innings Scores)")
            inn_scores = batting_df.groupby('match_id')['runs_batter'].sum()
            ranges = pd.cut(inn_scores, bins=[-1, 20, 50, 100, 300], labels=['0-20', '20-50', '50-100', '100+']).value_counts()
            fig_pie = px.pie(values=ranges.values, names=ranges.index, hole=.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_pie, use_container_width=True)

    # 5. Dynamic Layout
    if not compare_on:
        render_profile(player_name, st)
    elif p2_name:
        c1, c2 = st.columns(2)
        with c1: render_profile(player_name, st)
        with c2: render_profile(p2_name, st)
    else:
        # Hero state before search
        st.info("Start typing a name in the box above (like 'V Kohli') to begin.")