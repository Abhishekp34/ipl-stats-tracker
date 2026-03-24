import streamlit as st
import pandas as pd
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# 1. Page Config
st.set_page_config(page_title="Team Rivalry | IPL Tracker", layout="wide")

@st.cache_resource
def init_connection():
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    return create_client(url, key)

supabase = init_connection()

st.title("⚔️ Team Rivalry: The Deep Dive")

# 2. Selection UI
@st.cache_data(ttl=3600)
def get_teams():
    res = supabase.table('matches').select('team1').execute()
    teams = sorted(list(set([row['team1'] for row in res.data if row['team1']])))
    return teams

all_teams = get_teams()

col_a, col_vs, col_b = st.columns([4, 1, 4])
with col_a:
    t1 = st.selectbox("Team 1", all_teams, index=0)
with col_vs:
    st.markdown("<h2 style='text-align: center; padding-top: 20px;'>VS</h2>", unsafe_allow_html=True)
with col_b:
    default_idx = 1 if len(all_teams) > 1 else 0
    t2 = st.selectbox("Team 2", all_teams, index=default_idx)

if t1 == t2:
    st.warning("Select two different teams to compare.")
else:
    # 3. Fetch Data
    @st.cache_data(ttl=3600)
    def get_rivalry_data(team_a, team_b):
        # Match Query - using double quotes for names with spaces
        m_res = supabase.table('matches').select('*').or_(f'and(team1.eq."{team_a}",team2.eq."{team_b}"),and(team1.eq."{team_b}",team2.eq."{team_a}")').execute()
        m_df = pd.DataFrame(m_res.data)
        
        if m_df.empty:
            return m_df, pd.DataFrame()
        
        m_ids = m_df['match_id'].tolist()
        
        # Note: I removed 'team_batting' and used '*' to avoid column name errors. 
        # We will find the correct column name in the next step.
        d_res = supabase.table('deliveries').select('*').in_('match_id', m_ids).execute()
        d_df = pd.DataFrame(d_res.data)
        
        return m_df, d_df

    m_df, d_df = get_rivalry_data(t1, t2)

    if m_df.empty:
        st.info(f"No historic matches found between {t1} and {t2}.")
    else:
        # --- HEAD TO HEAD ---
        st.divider()
        wins = m_df['winner'].value_counts()
        
        c1, c2, c3 = st.columns(3)
        c1.metric(f"{t1} Wins", wins.get(t1, 0))
        c2.metric("Total Played", len(m_df))
        c3.metric(f"{t2} Wins", wins.get(t2, 0))

        # --- HOME VENUE PERFORMANCE ---
        st.subheader("🏟️ Record at Each Venue")
        venue_wins = m_df.groupby(['venue', 'winner']).size().unstack(fill_value=0)
        st.dataframe(venue_wins, use_container_width=True)

        if not d_df.empty:
            # Check for the correct batting team column name
            bat_col = 'batting_team' if 'batting_team' in d_df.columns else 'team_batting'
            if bat_col not in d_df.columns: # Fallback search
                possible_cols = [col for col in d_df.columns if 'team' in col.lower()]
                bat_col = possible_cols[0] if possible_cols else None

            # --- TOP 5 STATS ---
            st.divider()
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("🔥 Top 5 Run Scorers")
                top_runs = d_df.groupby('batter')['runs_batter'].sum().sort_values(ascending=False).head(5)
                st.table(top_runs)

                st.subheader("📈 Top 5 Highest Team Totals")
                # Grouping by match and innings to get team scores
                team_scores = d_df.groupby(['match_id', bat_col])['runs_total'].sum().reset_index()
                top_scores = team_scores.sort_values('runs_total', ascending=False).head(5)
                # Merge with winner info
                top_scores = top_scores.merge(m_df[['match_id', 'winner']], on='match_id')
                st.dataframe(top_scores[[bat_col, 'runs_total', 'winner']], hide_index=True)

            with col2:
                st.subheader("🎯 Top 5 Wicket Takers")
                valid_wkts = ['bowled', 'caught', 'lbw', 'stumped', 'caught and bowled']
                d_df['is_wicket'] = d_df['wicket_type'].isin(valid_wkts)
                top_wkts = d_df[d_df['is_wicket']].groupby('bowler').size().sort_values(ascending=False).head(5)
                st.table(top_wkts)

                st.subheader("🏏 Top 5 Highest Individual Innings")
                indiv_innings = d_df.groupby(['match_id', 'batter'])['runs_batter'].sum().sort_values(ascending=False).head(5)
                st.table(indiv_innings)