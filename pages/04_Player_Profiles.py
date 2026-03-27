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

# 2. Name Loader (Unified list from both Master Views)
@st.cache_data(ttl=86400)
def list_all_players():
    b_res = supabase.table('view_batter_master').select('player').execute()
    bw_res = supabase.table('view_bowler_master').select('player').execute()
    names = set([r['player'] for r in b_res.data] + [r['player'] for r in bw_res.data])
    return sorted(list(names))

all_names = list_all_players()

# 3. UI Header
st.title("👤 Player Resume")
st.markdown("Your IPL career journey, powered by optimized historical data.")

player_name = st.selectbox(
    "Search Player:", options=all_names, index=None, placeholder="Type a name..."
)

if player_name:
    # Fetch pre-computed stats from Master Views
    def get_summary_stats(name):
        bat = supabase.table('view_batter_master').select('*').eq('player', name).execute()
        bowl = supabase.table('view_bowler_master').select('*').eq('player', name).execute()
        return (bat.data[0] if bat.data else None, bowl.data[0] if bowl.data else None)

    bat_stats, bowl_stats = get_summary_stats(player_name)
    
    # --- UI: STATS OVERVIEW ---
    if bat_stats or bowl_stats:
        current_team = (bat_stats or bowl_stats)['team']
        st.subheader(f"🏆 {player_name} | Current/Last Team: {current_team}")
        
        col1, col2 = st.columns(2)
        with col1:
            if bat_stats:
                st.write("#### 🏏 Batting Stats")
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Runs", f"{int(bat_stats['runs']):,}")
                m2.metric("Average", bat_stats['avg'])
                m3.metric("Highest Score", bat_stats['hs'])
        
        with col2:
            if bowl_stats:
                st.write("#### ⚾ Bowling Stats")
                m4, m5, m6 = st.columns(3)
                m4.metric("Wickets", int(bowl_stats['wkts']))
                m5.metric("Economy", bowl_stats['econ'])
                m6.metric("Dots Bowled", f"{int(bowl_stats['dots']):,}")

    # --- UI: SEASONAL BAR CHART (The Fix) ---
    @st.cache_data(ttl=3600)
    def get_seasonal_history(name):
        # Fetching only what we need for the charts
        res = supabase.table('deliveries').select('match_id, batter, runs_batter, bowling_team').eq('batter', name).execute()
        d_df = pd.DataFrame(res.data)
        if d_df.empty: return pd.DataFrame()
        
        m_ids = d_df['match_id'].unique().tolist()
        m_res = supabase.table('matches').select('match_id, match_date').in_('match_id', m_ids).execute()
        m_df = pd.DataFrame(m_res.data)
        m_df['year'] = pd.to_datetime(m_df['match_date']).dt.year
        return d_df.merge(m_df, on='match_id')

    df = get_seasonal_history(player_name)
    
    if not df.empty:
        st.divider()
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.write("### 📊 Runs Scored Per Season")
            season_data = df.groupby('year')['runs_batter'].sum().reset_index()
            # CORRECTED: Changed from px.line to px.bar
            fig_season = px.bar(
                season_data, 
                x='year', 
                y='runs_batter', 
                text='runs_batter',
                template="plotly_dark",
                color_discrete_sequence=['#FFD700'] # Gold theme
            )
            fig_season.update_layout(xaxis=dict(type='category'), yaxis_visible=False)
            fig_season.update_traces(textposition='outside')
            st.plotly_chart(fig_season, use_container_width=True)
            
        with col_right:
            st.write("### ⚔️ Dominance by Opponent")
            opp_data = df.groupby('bowling_team')['runs_batter'].sum().reset_index().sort_values('runs_batter', ascending=False)
            fig_opp = px.bar(
                opp_data.head(8), 
                x='runs_batter', 
                y='bowling_team', 
                orientation='h',
                template="plotly_dark",
                color_discrete_sequence=['#3498DB']
            )
            fig_opp.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_opp, use_container_width=True)