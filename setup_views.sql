-- ======================================================
-- IPL MASTER CLEANUP & OPTIMIZED MATERIALIZED VIEWS (2026)
-- ======================================================

-- 1. STANDARDIZE TEAM NAMES (Directly in Raw Tables)
UPDATE matches
SET 
    team1 = CASE 
        WHEN team1 = 'DC' AND match_date < '2013-01-01' THEN 'Deccan Chargers'
        WHEN team1 = 'DC' AND match_date >= '2019-01-01' THEN 'Delhi Capitals'
        WHEN team1 IN ('Royal Challengers Bangalore', 'R C Bangalore', 'RCB') THEN 'Royal Challengers Bengaluru'
        WHEN team1 IN ('Kings XI Punjab', 'KXIP') THEN 'Punjab Kings'
        WHEN team1 = 'Delhi Daredevils' THEN 'Delhi Capitals'
        WHEN team1 IN ('Rising Pune Supergiants', 'Rising Pune Supergiant') THEN 'Rising Pune Supergiant'
        ELSE team1 
    END,
    team2 = CASE 
        WHEN team2 = 'DC' AND match_date < '2013-01-01' THEN 'Deccan Chargers'
        WHEN team2 = 'DC' AND match_date >= '2019-01-01' THEN 'Delhi Capitals'
        WHEN team2 IN ('Royal Challengers Bangalore', 'R C Bangalore', 'RCB') THEN 'Royal Challengers Bengaluru'
        WHEN team2 IN ('Kings XI Punjab', 'KXIP') THEN 'Punjab Kings'
        WHEN team2 = 'Delhi Daredevils' THEN 'Delhi Capitals'
        WHEN team2 IN ('Rising Pune Supergiants', 'Rising Pune Supergiant') THEN 'Rising Pune Supergiant'
        ELSE team2 
    END,
    winner = CASE 
        WHEN winner = 'DC' AND match_date < '2013-01-01' THEN 'Deccan Chargers'
        WHEN winner = 'DC' AND match_date >= '2019-01-01' THEN 'Delhi Capitals'
        WHEN winner IN ('Royal Challengers Bangalore', 'R C Bangalore', 'RCB') THEN 'Royal Challengers Bengaluru'
        WHEN winner IN ('Kings XI Punjab', 'KXIP') THEN 'Punjab Kings'
        WHEN winner = 'Delhi Daredevils' THEN 'Delhi Capitals'
        WHEN winner IN ('Rising Pune Supergiants', 'Rising Pune Supergiant') THEN 'Rising Pune Supergiant'
        ELSE winner 
    END;

UPDATE deliveries
SET 
    batting_team = CASE 
        WHEN batting_team = 'DC' AND match_id IN (SELECT match_id FROM matches WHERE team1 = 'Deccan Chargers' OR team2 = 'Deccan Chargers') THEN 'Deccan Chargers'
        WHEN batting_team = 'DC' AND match_id IN (SELECT match_id FROM matches WHERE team1 = 'Delhi Capitals' OR team2 = 'Delhi Capitals') THEN 'Delhi Capitals'
        WHEN batting_team IN ('Royal Challengers Bangalore', 'R C Bangalore', 'RCB') THEN 'Royal Challengers Bengaluru'
        WHEN batting_team IN ('Kings XI Punjab', 'KXIP') THEN 'Punjab Kings'
        WHEN batting_team = 'Delhi Daredevils' THEN 'Delhi Capitals'
        WHEN batting_team IN ('Rising Pune Supergiants', 'Rising Pune Supergiant') THEN 'Rising Pune Supergiant'
        ELSE batting_team 
    END,
    bowling_team = CASE 
        WHEN bowling_team = 'DC' AND match_id IN (SELECT match_id FROM matches WHERE team1 = 'Deccan Chargers' OR team2 = 'Deccan Chargers') THEN 'Deccan Chargers'
        WHEN bowling_team = 'DC' AND match_id IN (SELECT match_id FROM matches WHERE team1 = 'Delhi Capitals' OR team2 = 'Delhi Capitals') THEN 'Delhi Capitals'
        WHEN bowling_team IN ('Royal Challengers Bangalore', 'R C Bangalore', 'RCB') THEN 'Royal Challengers Bengaluru'
        WHEN bowling_team IN ('Kings XI Punjab', 'KXIP') THEN 'Punjab Kings'
        WHEN bowling_team = 'Delhi Daredevils' THEN 'Delhi Capitals'
        WHEN bowling_team IN ('Rising Pune Supergiants', 'Rising Pune Supergiant') THEN 'Rising Pune Supergiant'
        ELSE bowling_team 
    END;

-- 2. STANDARDIZE VENUE NAMES
UPDATE matches
SET venue = CASE 
    WHEN venue ILIKE '%Wankhede%' THEN 'Wankhede Stadium, Mumbai'
    WHEN venue ILIKE '%Chinnaswamy%' THEN 'M. Chinnaswamy Stadium, Bengaluru'
    WHEN venue ILIKE '%Chidambaram%' OR venue ILIKE '%Chepauk%' THEN 'M. A. Chidambaram Stadium, Chennai'
    WHEN venue ILIKE '%Arun Jaitley%' OR venue ILIKE '%Feroz Shah Kotla%' THEN 'Arun Jaitley Stadium, Delhi'
    WHEN venue ILIKE '%Rajiv Gandhi%' THEN 'Rajiv Gandhi International Stadium, Hyderabad'
    WHEN venue ILIKE '%Narendra Modi%' OR venue ILIKE '%Motera%' THEN 'Narendra Modi Stadium, Ahmedabad'
    WHEN venue ILIKE '%Eden Gardens%' THEN 'Eden Gardens, Kolkata'
    WHEN venue ILIKE '%IS Bindra%' OR venue ILIKE '%Punjab Cricket Association%' THEN 'IS Bindra Stadium, Mohali'
    ELSE venue 
END;


-- 3. BATTING MASTER VIEW (Metrics for Player Profile & Comparison)
DROP MATERIALIZED VIEW IF EXISTS view_batter_master CASCADE;
CREATE MATERIALIZED VIEW view_batter_master AS
WITH player_latest_team AS (
    SELECT DISTINCT ON (batter) batter, batting_team as current_team, m.match_date
    FROM deliveries d JOIN matches m ON d.match_id = m.match_id
    ORDER BY batter, m.match_date DESC, m.match_id DESC
),
match_scores AS (
    SELECT batter, match_id, SUM(runs_batter) as runs_in_match,
    MAX(CASE WHEN player_out = batter THEN 1 ELSE 0 END) as was_dismissed
    FROM deliveries GROUP BY batter, match_id
),
true_hs AS (
    SELECT DISTINCT ON (batter) batter, runs_in_match,
    CASE WHEN was_dismissed = 0 THEN runs_in_match::text || '*' ELSE runs_in_match::text END as hs_final
    FROM match_scores ORDER BY batter, runs_in_match DESC, was_dismissed ASC
),
potm_counts AS (
    SELECT player_of_match as player, COUNT(*) as potm_total
    FROM matches GROUP BY player_of_match
),
dismissals AS (
    SELECT player_out as player, COUNT(*) as total_outs
    FROM deliveries WHERE player_out IS NOT NULL GROUP BY player_out
)
SELECT 
    d.batter AS player, lt.current_team AS team, MAX(lt.match_date) AS last_match_date,
    COUNT(DISTINCT d.match_id) AS mat,
    (COUNT(DISTINCT d.match_id) - COALESCE(dis.total_outs, 0)) AS not_outs,
    COALESCE(p.potm_total, 0) AS potm,
    SUM(d.runs_batter) AS runs, ths.hs_final AS hs, 
    ROUND(SUM(d.runs_batter)::numeric / NULLIF(COALESCE(dis.total_outs, 0), 0), 2) AS avg,
    ROUND((SUM(d.runs_batter)::numeric / NULLIF(COUNT(CASE WHEN extra_type NOT IN ('wides') OR extra_type IS NULL THEN 1 END), 0)) * 100, 2) AS sr,
    SUM(CASE WHEN d.runs_batter = 4 THEN 1 ELSE 0 END) AS "4s",
    SUM(CASE WHEN d.runs_batter = 6 THEN 1 ELSE 0 END) AS "6s",
    COUNT(DISTINCT CASE WHEN ms.runs_in_match >= 100 THEN d.match_id END) AS "100s",
    COUNT(DISTINCT CASE WHEN ms.runs_in_match >= 50 AND ms.runs_in_match < 100 THEN d.match_id END) AS "50s"
FROM deliveries d
JOIN player_latest_team lt ON d.batter = lt.batter
JOIN true_hs ths ON d.batter = ths.batter
LEFT JOIN dismissals dis ON d.batter = dis.player
LEFT JOIN potm_counts p ON d.batter = p.player
LEFT JOIN match_scores ms ON d.batter = ms.batter AND d.match_id = ms.match_id
GROUP BY d.batter, lt.current_team, ths.hs_final, dis.total_outs, p.potm_total;

CREATE UNIQUE INDEX idx_unique_batter_master ON view_batter_master (player);


-- 4. BOWLING MASTER VIEW
DROP MATERIALIZED VIEW IF EXISTS view_bowler_master CASCADE;
CREATE MATERIALIZED VIEW view_bowler_master AS
WITH player_latest_team AS (
    SELECT DISTINCT ON (bowler) bowler, bowling_team as current_team, m.match_date
    FROM deliveries d JOIN matches m ON d.match_id = m.match_id
    ORDER BY bowler, m.match_date DESC, m.match_id DESC
),
match_wickets AS (
    SELECT bowler, match_id, COUNT(CASE WHEN wicket_type IN ('bowled', 'caught', 'lbw', 'stumped', 'caught and bowled') THEN 1 END) as w_in_match
    FROM deliveries GROUP BY bowler, match_id
)
SELECT 
    d.bowler AS player, lt.current_team AS team, MAX(lt.match_date) AS last_match_date,
    COUNT(DISTINCT d.match_id) AS mat,
    COUNT(CASE WHEN d.wicket_type IN ('bowled', 'caught', 'lbw', 'stumped', 'caught and bowled') THEN 1 END) AS wkts,
    ROUND((SUM(d.runs_total)::numeric / NULLIF(COUNT(d.ball), 0)) * 6, 2) AS econ,
    COUNT(CASE WHEN d.runs_batter = 0 AND (d.runs_extras = 0 OR d.extra_type IN ('byes', 'legbyes')) THEN 1 END) AS dots,
    COUNT(DISTINCT CASE WHEN mw.w_in_match = 4 THEN d.match_id END) AS "4w",
    COUNT(DISTINCT CASE WHEN mw.w_in_match >= 5 THEN d.match_id END) AS "5w"
FROM deliveries d
JOIN player_latest_team lt ON d.bowler = lt.bowler
LEFT JOIN match_wickets mw ON d.bowler = mw.bowler AND d.match_id = mw.match_id
GROUP BY d.bowler, lt.current_team;

CREATE UNIQUE INDEX idx_unique_bowler_master ON view_bowler_master (player);


-- 5. SEASON-BY-SEASON PERFORMANCE VIEW
DROP MATERIALIZED VIEW IF EXISTS view_player_season_stats;
CREATE MATERIALIZED VIEW view_player_season_stats AS
SELECT 
    d.batter AS player, 
    m.season, 
    SUM(d.runs_batter) AS season_runs
FROM deliveries d
JOIN matches m ON d.match_id = m.match_id
GROUP BY d.batter, m.season;

CREATE UNIQUE INDEX idx_season_stats ON view_player_season_stats (player, season);


-- 6. TEAM RIVALRY VIEW
DROP MATERIALIZED VIEW IF EXISTS view_team_rivalry_master CASCADE;
CREATE MATERIALIZED VIEW view_team_rivalry_master AS
WITH match_summaries AS (
    SELECT 
        CASE WHEN team1 < team2 THEN team1 ELSE team2 END as side_a,
        CASE WHEN team1 < team2 THEN team2 ELSE team1 END as side_b,
        COUNT(*) as total_matches,
        COUNT(CASE WHEN winner = team1 THEN 1 END) as team1_wins,
        COUNT(CASE WHEN winner = team2 THEN 1 END) as team2_wins
    FROM matches GROUP BY side_a, side_b
),
batting_riv AS (
    SELECT CASE WHEN batting_team < bowling_team THEN batting_team ELSE bowling_team END as sa,
           CASE WHEN batting_team < bowling_team THEN bowling_team ELSE batting_team END as sb,
           batter, SUM(runs_batter) as tr FROM deliveries GROUP BY sa, sb, batter
),
bowling_riv AS (
    SELECT CASE WHEN batting_team < bowling_team THEN batting_team ELSE bowling_team END as sa,
           CASE WHEN batting_team < bowling_team THEN bowling_team ELSE batting_team END as sb,
           bowler, COUNT(CASE WHEN wicket_type IN ('bowled', 'caught', 'lbw', 'stumped', 'caught and bowled') THEN 1 END) as tw FROM deliveries GROUP BY sa, sb, bowler
)
SELECT m.*,
    (SELECT batter FROM batting_riv br WHERE br.sa = m.side_a AND br.sb = m.side_b ORDER BY tr DESC LIMIT 1) as top_batter,
    (SELECT tr FROM batting_riv br WHERE br.sa = m.side_a AND br.sb = m.side_b ORDER BY tr DESC LIMIT 1) as max_runs,
    (SELECT bowler FROM bowling_riv bw WHERE bw.sa = m.side_a AND br.sb = m.side_b ORDER BY tw DESC LIMIT 1) as top_bowler,
    (SELECT tw FROM bowling_riv bw WHERE bw.sa = m.side_a AND br.sb = m.side_b ORDER BY tw DESC LIMIT 1) as max_wickets
FROM match_summaries m;

CREATE UNIQUE INDEX idx_unique_team_rivalry ON view_team_rivalry_master (side_a, side_b);


-- 7. BATTING RACE MATRICES (With Postgres Forward-Fill for Colors)
DROP MATERIALIZED VIEW IF EXISTS view_top_30_batting_race CASCADE;
DROP MATERIALIZED VIEW IF EXISTS view_player_race_matrix CASCADE;

CREATE MATERIALIZED VIEW view_player_race_matrix AS
WITH all_m AS (
    SELECT match_id, ROW_NUMBER() OVER (ORDER BY match_date, match_id) as global_num FROM matches
),
player_match_teams AS (
    SELECT DISTINCT ON (match_id, batter) match_id, batter, batting_team FROM deliveries
),
m_scores AS (
    SELECT batter as p, match_id, SUM(runs_batter) as r FROM deliveries GROUP BY batter, match_id
),
base_data AS (
    SELECT 
        p.batter as player, 
        m.global_num, 
        pmt.batting_team as raw_team,
        SUM(COALESCE(ms.r, 0)) OVER (PARTITION BY p.batter ORDER BY m.global_num) as cumulative_runs,
        COUNT(pmt.batting_team) OVER (PARTITION BY p.batter ORDER BY m.global_num) as team_grp
    FROM (SELECT DISTINCT batter FROM deliveries) p 
    CROSS JOIN all_m m 
    LEFT JOIN m_scores ms ON p.batter = ms.p AND m.match_id = ms.match_id
    LEFT JOIN player_match_teams pmt ON p.batter = pmt.batter AND m.match_id = pmt.match_id
),
filled_data AS (
    SELECT player, global_num, cumulative_runs,
    FIRST_VALUE(raw_team) OVER (PARTITION BY player, team_grp ORDER BY global_num) as team
    FROM base_data
)
SELECT player, 
       array_agg(cumulative_runs ORDER BY global_num) as history,
       array_agg(team ORDER BY global_num) as team_history
FROM filled_data GROUP BY player;

CREATE UNIQUE INDEX idx_unique_player_race ON view_player_race_matrix (player);

CREATE MATERIALIZED VIEW view_top_30_batting_race AS
WITH unnested_history AS (
    SELECT player, unnest(history) as cumulative_runs, unnest(team_history) as team,
           generate_series(1, array_length(history, 1)) as match_seq
    FROM view_player_race_matrix
),
ranked_history AS (
    SELECT match_seq, player, team, cumulative_runs, 
           DENSE_RANK() OVER (PARTITION BY match_seq ORDER BY cumulative_runs DESC) as rank
    FROM unnested_history
)
SELECT * FROM ranked_history WHERE rank <= 30;

CREATE UNIQUE INDEX idx_unique_top30_bat ON view_top_30_batting_race (match_seq, player);


-- 8. BOWLING RACE MATRICES (With Postgres Forward-Fill for Colors)
DROP MATERIALIZED VIEW IF EXISTS view_top_30_bowling_race CASCADE;
DROP MATERIALIZED VIEW IF EXISTS view_bowler_race_matrix CASCADE;

CREATE MATERIALIZED VIEW view_bowler_race_matrix AS
WITH all_m AS (
    SELECT match_id, ROW_NUMBER() OVER (ORDER BY match_date, match_id) as global_num FROM matches
),
player_match_teams_bowl AS (
    SELECT DISTINCT ON (match_id, bowler) match_id, bowler, bowling_team FROM deliveries
),
m_wkts AS (
    SELECT bowler as p, match_id, 
    COUNT(CASE WHEN wicket_type IN ('bowled', 'caught', 'lbw', 'stumped', 'caught and bowled') THEN 1 END) as w FROM deliveries GROUP BY bowler, match_id
),
base_data_bowl AS (
    SELECT 
        p.bowler as player, 
        m.global_num, 
        pmt.bowling_team as raw_team,
        SUM(COALESCE(mw.w, 0)) OVER (PARTITION BY p.bowler ORDER BY m.global_num) as cumulative_wkts,
        COUNT(pmt.bowling_team) OVER (PARTITION BY p.bowler ORDER BY m.global_num) as team_grp
    FROM (SELECT DISTINCT bowler FROM deliveries) p 
    CROSS JOIN all_m m 
    LEFT JOIN m_wkts mw ON p.bowler = mw.p AND m.match_id = mw.match_id
    LEFT JOIN player_match_teams_bowl pmt ON p.bowler = pmt.bowler AND m.match_id = pmt.match_id
),
filled_data_bowl AS (
    SELECT player, global_num, cumulative_wkts,
    FIRST_VALUE(raw_team) OVER (PARTITION BY player, team_grp ORDER BY global_num) as team
    FROM base_data_bowl
)
SELECT player, 
       array_agg(cumulative_wkts ORDER BY global_num) as history,
       array_agg(team ORDER BY global_num) as team_history
FROM filled_data_bowl GROUP BY player;

CREATE UNIQUE INDEX idx_unique_bowler_race ON view_bowler_race_matrix (player);

CREATE MATERIALIZED VIEW view_top_30_bowling_race AS
WITH unnested_bowling AS (
    SELECT player, unnest(history) as cumulative_wickets, unnest(team_history) as team,
           generate_series(1, array_length(history, 1)) as match_seq
    FROM view_bowler_race_matrix
),
ranked_bowling AS (
    SELECT match_seq, player, team, cumulative_wickets, 
           DENSE_RANK() OVER (PARTITION BY match_seq ORDER BY cumulative_wickets DESC) as rank
    FROM unnested_bowling
)
SELECT * FROM ranked_bowling WHERE rank <= 30;

CREATE UNIQUE INDEX idx_unique_top30_bowl ON view_top_30_bowling_race (match_seq, player);


-- 9. AUTOMATION: CONCURRENT REFRESH FUNCTION
CREATE OR REPLACE FUNCTION refresh_all_ipl_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY view_batter_master;
    REFRESH MATERIALIZED VIEW CONCURRENTLY view_bowler_master;
    REFRESH MATERIALIZED VIEW CONCURRENTLY view_player_season_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY view_team_rivalry_master;
    REFRESH MATERIALIZED VIEW CONCURRENTLY view_player_race_matrix;
    REFRESH MATERIALIZED VIEW CONCURRENTLY view_top_30_batting_race;
    REFRESH MATERIALIZED VIEW CONCURRENTLY view_bowler_race_matrix;
    REFRESH MATERIALIZED VIEW CONCURRENTLY view_top_30_bowling_race;
END;
$$ LANGUAGE plpgsql;

-- Final Refresh
SELECT refresh_all_ipl_views();