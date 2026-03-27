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

# 2. Updated Name Loader (Points to new View)
@st.cache_data(ttl=86400)
def list_all_players():
    try:
        # Changed from 'batter_stats_advanced' to 'view_batter_master'
        # Changed column from 'batter' to 'player'
        res = supabase.table('view_batter_master').select('player').execute()
        return sorted([r['player'] for r in res.data])
    except Exception as e:
        st.error(f"Database Error: {e}")
        return ["V Kohli", "MS Dhoni", "RG Sharma", "DA Warner", "S Dhawan", "AB de Villiers"]

all_names = list_all_players()

# 3. Optimized Data Fetching (Using Standardized Columns)
@st.cache_data(ttl=3600)
def get_player_full_data(name):
    # Fetch from deliveries using the standardized player name
    d_res = supabase.table('deliveries').select('*').or_(f'batter.eq."{name}",bowler.eq."{name}"').execute()
    d_df = pd.DataFrame(d_res.data)
    
    if d_df.empty: return pd.DataFrame()
    
    # Fetch Match years
    m_ids = d_df['match_id'].unique().tolist()
    m_res = supabase.table('matches').select('match_id, match_date').in_('match_id', m_ids).execute()
    m_df = pd.DataFrame(m_res.data)
    m_df['year'] = pd.to_datetime(m_df['match_date']).dt.year
    
    return d_df.merge(m_df, on='match_id')

# 4. Main UI
st.title("👤 Player Resume")
st.markdown("Enter a player's name to see their IPL career journey.")

player_name = st.selectbox(
    "Search Player:", 
    options=all_names, 
    index=None, 
    placeholder="Type to search...",
    help="Search from all players in IPL history."
)

if player_name:
    # Fetch the high-level stats from our new master view for the metric cards
    @st.cache_data(ttl=600)
    def get_summary_stats(name):
        res = supabase.table('view_batter_master').select('*').eq('player', name).execute()
        return res.data[0] if res.data else None

    stats = get_summary_stats(player_name)
    
    if stats:
        # --- UI: METRIC CARDS (Using New Schema) ---
        with st.container(border=True):
            st.subheader(f"🏆 {player_name} ({stats['team']})")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Runs", f"{int(stats['runs']):,}")
            m2.metric("Batting Avg", stats['avg'])
            m3.metric("Strike Rate", stats['sr'])
            m4.metric("Highest Score", stats['hs'])

        # --- UI: DRILL DOWN (Season/Opponent) ---
        df = get_player_full_data(player_name)
        if not df.empty:
            batting_df = df[df['batter'] == player_name]
            
            st.divider()
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.write("### 📈 Runs by Season")
                season_stats = batting_df.groupby('year')['runs_batter'].sum().reset_index()
                fig_season = px.bar(
                    season_stats, x='year', y='runs_batter', text='runs_batter',
                    template="plotly_dark", color_discrete_sequence=['#E74C3C']
                )
                fig_season.update_layout(xaxis=dict(type='category'), yaxis_visible=False)
                st.plotly_chart(fig_season, use_container_width=True)
            
            with col_b:
                st.write("### ⚔️ Runs by Opponent")
                opp_stats = batting_df.groupby('bowling_team')['runs_batter'].sum().reset_index().sort_values('runs_batter', ascending=False)
                fig_opp = px.bar(
                    opp_stats, x='bowling_team', y='runs_batter', text='runs_batter',
                    template="plotly_dark", color_discrete_sequence=['#3498DB']
                )
                fig_opp.update_layout(yaxis_visible=False)
                st.plotly_chart(fig_opp, use_container_width=True)

            # --- Score Consistency ---
            st.divider()
            st.write("### 🎯 Score Consistency")
            inn_scores = batting_df.groupby('match_id')['runs_batter'].sum()
            ranges = pd.cut(inn_scores, bins=[-1, 20, 50, 100, 300], labels=['0-20', '20-50', '50-100', '100+']).value_counts()
            fig_pie = px.pie(values=ranges.values, names=ranges.index, hole=.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)