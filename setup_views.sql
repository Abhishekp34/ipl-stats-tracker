-- ==========================================
-- IPL MASTER CLEANUP & OPTIMIZED VIEWS
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

-- 3. GLOBAL BATTING MASTER (Corrected Formulas)
DROP MATERIALIZED VIEW IF EXISTS view_batter_master CASCADE;

CREATE MATERIALIZED VIEW view_batter_master AS
WITH player_latest_team AS (
    SELECT DISTINCT ON (batter) 
        batter, 
        batting_team as current_team
    FROM deliveries d
    JOIN matches m ON d.match_id = m.match_id
    ORDER BY batter, m.match_date DESC, m.match_id DESC
),
match_by_match_scores AS (
    SELECT 
        batter, 
        match_id, 
        SUM(runs_batter) as total_runs_in_match,
        MAX(CASE WHEN player_out = batter THEN 1 ELSE 0 END) as was_out_in_match
    FROM deliveries 
    GROUP BY batter, match_id
),
highest_score_per_player AS (
    SELECT DISTINCT ON (batter)
        batter,
        total_runs_in_match,
        CASE WHEN was_out_in_match = 0 THEN total_runs_in_match::text || '*' ELSE total_runs_in_match::text END as hs_formatted
    FROM match_by_match_scores
    ORDER BY batter, total_runs_in_match DESC
)
SELECT 
    d.batter AS player,
    lt.current_team AS team,
    COUNT(DISTINCT d.match_id) AS mat,
    SUM(d.runs_batter) AS runs,
    hsp.hs_formatted AS hs, 
    ROUND(SUM(d.runs_batter)::numeric / NULLIF(SUM(ms.was_out_in_match), 0), 2) AS avg,
    ROUND((SUM(d.runs_batter)::numeric / NULLIF(COUNT(CASE WHEN extra_type NOT IN ('wides') OR extra_type IS NULL THEN 1 END), 0)) * 100, 2) AS sr,
    SUM(CASE WHEN d.runs_batter = 4 THEN 1 ELSE 0 END) AS "4s",
    SUM(CASE WHEN d.runs_batter = 6 THEN 1 ELSE 0 END) AS "6s",
    COUNT(DISTINCT CASE WHEN ms.total_runs_in_match >= 100 THEN d.match_id END) AS "100s",
    COUNT(DISTINCT CASE WHEN ms.total_runs_in_match >= 50 AND ms.total_runs_in_match < 100 THEN d.match_id END) AS "50s"
FROM deliveries d
JOIN player_latest_team lt ON d.batter = lt.batter
JOIN highest_score_per_player hsp ON d.batter = hsp.batter
LEFT JOIN match_by_match_scores ms ON d.batter = ms.batter AND d.match_id = ms.match_id
GROUP BY d.batter, lt.current_team, hsp.hs_formatted;

-- 4. GLOBAL BOWLING MASTER
DROP MATERIALIZED VIEW IF EXISTS view_bowler_master CASCADE;

CREATE MATERIALIZED VIEW view_bowler_master AS
WITH player_latest_team AS (
    SELECT DISTINCT ON (bowler) 
        bowler, 
        bowling_team as current_team
    FROM deliveries d
    JOIN matches m ON d.match_id = m.match_id
    ORDER BY bowler, m.match_date DESC, m.match_id DESC
),
match_wickets AS (
    SELECT bowler, match_id, 
           COUNT(CASE WHEN wicket_type IN ('bowled', 'caught', 'lbw', 'stumped', 'caught and bowled') THEN 1 END) as w_in_match
    FROM deliveries GROUP BY bowler, match_id
)
SELECT 
    d.bowler AS player,
    lt.current_team AS team,
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

-- 5. BATTING RACE MATRIX
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
    SELECT 
        p.batter as player,
        m.global_num,
        SUM(COALESCE(ms.runs, 0)) OVER (PARTITION BY p.batter ORDER BY m.global_num) as total
    FROM (SELECT DISTINCT batter FROM deliveries) p
    CROSS JOIN all_matches m
    LEFT JOIN match_scores ms ON p.batter = ms.player AND m.match_id = ms.match_id
)
SELECT player, array_agg(total ORDER BY global_num) as history
FROM cumulative_scores GROUP BY player;

-- 6. BOWLING RACE MATRIX
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
SELECT player, array_agg(total ORDER BY global_num) as history
FROM cumulative_wickets GROUP BY player;

-- 7. REFRESH & INDEXING
REFRESH MATERIALIZED VIEW view_batter_master;
REFRESH MATERIALIZED VIEW view_bowler_master;
REFRESH MATERIALIZED VIEW view_player_race_matrix;
REFRESH MATERIALIZED VIEW view_bowler_race_matrix;

CREATE INDEX idx_batter_player ON view_batter_master(player);
CREATE INDEX idx_bowler_player ON view_bowler_master(player);