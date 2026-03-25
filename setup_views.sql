-- ==========================================
-- IPL MASTER CLEANUP & MATERIALIZED VIEWS
-- ==========================================

-- 1. STANDARDIZE TEAM NAMES
UPDATE matches
SET 
    team1 = CASE 
        WHEN team1 IN ('Royal Challengers Bangalore', 'R C Bangalore') THEN 'Royal Challengers Bengaluru'
        WHEN team1 IN ('Kings XI Punjab', 'KXIP') THEN 'Punjab Kings'
        WHEN team1 = 'Delhi Daredevils' THEN 'Delhi Capitals'
        WHEN team1 = 'Rising Pune Supergiants' THEN 'Rising Pune Supergiant'
        ELSE team1 
    END,
    team2 = CASE 
        WHEN team2 IN ('Royal Challengers Bangalore', 'R C Bangalore') THEN 'Royal Challengers Bengaluru'
        WHEN team2 IN ('Kings XI Punjab', 'KXIP') THEN 'Punjab Kings'
        WHEN team2 = 'Delhi Daredevils' THEN 'Delhi Capitals'
        WHEN team2 = 'Rising Pune Supergiants' THEN 'Rising Pune Supergiant'
        ELSE team2 
    END,
    winner = CASE 
        WHEN winner IN ('Royal Challengers Bangalore', 'R C Bangalore') THEN 'Royal Challengers Bengaluru'
        WHEN winner IN ('Kings XI Punjab', 'KXIP') THEN 'Punjab Kings'
        WHEN winner = 'Delhi Daredevils' THEN 'Delhi Capitals'
        WHEN winner = 'Rising Pune Supergiants' THEN 'Rising Pune Supergiant'
        ELSE winner 
    END;

UPDATE deliveries
SET 
    batting_team = CASE 
        WHEN batting_team IN ('Royal Challengers Bangalore', 'R C Bangalore') THEN 'Royal Challengers Bengaluru'
        WHEN batting_team = 'Kings XI Punjab' THEN 'Punjab Kings'
        WHEN batting_team = 'Delhi Daredevils' THEN 'Delhi Capitals'
        WHEN batting_team = 'Rising Pune Supergiants' THEN 'Rising Pune Supergiant'
        ELSE batting_team 
    END,
    bowling_team = CASE 
        WHEN bowling_team IN ('Royal Challengers Bangalore', 'R C Bangalore') THEN 'Royal Challengers Bengaluru'
        WHEN bowling_team = 'Kings XI Punjab' THEN 'Punjab Kings'
        WHEN bowling_team = 'Delhi Daredevils' THEN 'Delhi Capitals'
        WHEN bowling_team = 'Rising Pune Supergiants' THEN 'Rising Pune Supergiant'
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

-- 3. RECREATE MASTER VIEWS (MATERIALIZED FOR PERFORMANCE)
DROP MATERIALIZED VIEW IF EXISTS view_batter_master CASCADE;
DROP MATERIALIZED VIEW IF EXISTS view_bowler_master CASCADE;

-- Master Batting Materialized View
CREATE MATERIALIZED VIEW view_batter_master AS
WITH match_stats AS (
    SELECT batter, match_id, SUM(runs_batter) as runs_in_match
    FROM deliveries GROUP BY batter, match_id
)
SELECT 
    d.batter AS player,
    d.batting_team AS team,
    COUNT(DISTINCT d.match_id) AS mat,
    SUM(d.runs_batter) AS runs,
    MAX(d.runs_batter) AS hs,
    ROUND(SUM(d.runs_batter)::numeric / NULLIF(COUNT(DISTINCT d.match_id) - COUNT(CASE WHEN d.player_out = d.batter THEN 1 END), 0), 2) AS avg,
    ROUND((SUM(d.runs_batter)::numeric / NULLIF(COUNT(d.ball), 0)) * 100, 2) AS sr,
    SUM(CASE WHEN d.runs_batter = 4 THEN 1 ELSE 0 END) AS "4s",
    SUM(CASE WHEN d.runs_batter = 6 THEN 1 ELSE 0 END) AS "6s",
    COUNT(DISTINCT CASE WHEN ms.runs_in_match >= 100 THEN d.match_id END) AS "100s",
    COUNT(DISTINCT CASE WHEN ms.runs_in_match >= 50 AND ms.runs_in_match < 100 THEN d.match_id END) AS "50s"
FROM deliveries d
LEFT JOIN match_stats ms ON d.batter = ms.batter AND d.match_id = ms.match_id
GROUP BY d.batter, d.batting_team;

-- Master Bowling Materialized View
CREATE MATERIALIZED VIEW view_bowler_master AS
WITH match_wickets AS (
    SELECT bowler, match_id, 
           COUNT(CASE WHEN wicket_type IN ('bowled', 'caught', 'lbw', 'stumped', 'caught and bowled') THEN 1 END) as w_in_match
    FROM deliveries GROUP BY bowler, match_id
)
SELECT 
    d.bowler AS player,
    d.bowling_team AS team,
    COUNT(DISTINCT d.match_id) AS mat,
    COUNT(CASE WHEN d.wicket_type IN ('bowled', 'caught', 'lbw', 'stumped', 'caught and bowled') THEN 1 END) AS wkts,
    ROUND((SUM(d.runs_total)::numeric / NULLIF(COUNT(d.ball), 0)) * 6, 2) AS econ,
    COUNT(CASE WHEN d.runs_batter = 0 AND (d.runs_extras = 0 OR d.extra_type IN ('byes', 'legbyes')) THEN 1 END) AS dots,
    COUNT(DISTINCT CASE WHEN mw.w_in_match = 4 THEN d.match_id END) AS "4w",
    COUNT(DISTINCT CASE WHEN mw.w_in_match >= 5 THEN d.match_id END) AS "5w"
FROM deliveries d
LEFT JOIN match_wickets mw ON d.bowler = mw.bowler AND d.match_id = mw.match_id
GROUP BY d.bowler, d.bowling_team;

-- 4. ADD INDEXES FOR LIGHTNING SPEED
CREATE INDEX idx_mv_batter_name ON view_batter_master(player);
CREATE INDEX idx_mv_bowler_name ON view_bowler_master(player);

-- 5. INITIAL REFRESH
REFRESH MATERIALIZED VIEW view_batter_master;
REFRESH MATERIALIZED VIEW view_bowler_master;


DROP MATERIALIZED VIEW IF EXISTS view_player_race_matrix;

CREATE MATERIALIZED VIEW view_player_race_matrix AS
WITH all_matches AS (
    SELECT match_id, ROW_NUMBER() OVER (ORDER BY match_date, match_id) as global_num
    FROM matches
),
match_scores AS (
    SELECT batter as player, match_id, SUM(runs_batter) as runs
    FROM deliveries GROUP BY batter, match_id
),
cumulative_scores AS (
    -- Calculate the running total for every player for every match
    SELECT 
        p.batter as player,
        m.global_num,
        SUM(COALESCE(ms.runs, 0)) OVER (PARTITION BY p.batter ORDER BY m.global_num) as total
    FROM (SELECT DISTINCT batter FROM deliveries) p
    CROSS JOIN all_matches m
    LEFT JOIN match_scores ms ON p.batter = ms.player AND m.match_id = ms.match_id
)
-- "Pivot" the data: One row per player, one array containing all 1,169 match totals
SELECT 
    player,
    array_agg(total ORDER BY global_num) as history
FROM cumulative_scores
GROUP BY player;

REFRESH MATERIALIZED VIEW view_player_race_matrix;

DROP MATERIALIZED VIEW IF EXISTS view_bowler_race_matrix;

CREATE MATERIALIZED VIEW view_bowler_race_matrix AS
WITH all_matches AS (
    SELECT match_id, ROW_NUMBER() OVER (ORDER BY match_date, match_id) as global_num
    FROM matches
),
match_wickets AS (
    SELECT bowler as player, match_id, 
           COUNT(CASE WHEN wicket_type IN ('bowled', 'caught', 'lbw', 'stumped', 'caught and bowled') THEN 1 END) as wkts
    FROM deliveries GROUP BY bowler, match_id
),
cumulative_wickets AS (
    SELECT 
        p.bowler as player,
        m.global_num,
        SUM(COALESCE(mw.wkts, 0)) OVER (PARTITION BY p.bowler ORDER BY m.global_num) as total
    FROM (SELECT DISTINCT bowler FROM deliveries) p
    CROSS JOIN all_matches m
    LEFT JOIN match_wickets mw ON p.bowler = mw.player AND m.match_id = mw.match_id
)
SELECT 
    player,
    array_agg(total ORDER BY global_num) as history
FROM cumulative_wickets
GROUP BY player;

REFRESH MATERIALIZED VIEW view_bowler_race_matrix;