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

-- 3. GLOBAL BATTING MASTER (Corrected Formulas for Avg & HS)
DROP MATERIALIZED VIEW IF EXISTS view_batter_master CASCADE;

CREATE MATERIALIZED VIEW view_batter_master AS
WITH player_latest_team AS (
    SELECT DISTINCT ON (batter) batter, batting_team as current_team
    FROM deliveries d JOIN matches m ON d.match_id = m.match_id
    ORDER BY batter, m.match_date DESC, m.match_id DESC
),
match_scores AS (
    SELECT 
        batter, match_id, SUM(runs_batter) as runs_in_match,
        MAX(CASE WHEN player_out = batter THEN 1 ELSE 0 END) as was_dismissed
    FROM deliveries GROUP BY batter, match_id
),
true_hs AS (
    SELECT DISTINCT ON (batter)
        batter, runs_in_match,
        CASE WHEN was_dismissed = 0 THEN runs_in_match::text || '*' ELSE runs_in_match::text END as hs_final
    FROM match_scores
    ORDER BY batter, runs_in_match DESC, was_dismissed ASC
),
dismissals AS (
    SELECT player_out as player, COUNT(*) as total_outs
    FROM deliveries WHERE player_out IS NOT NULL GROUP BY player_out
)
SELECT 
    d.batter AS player,
    lt.current_team AS team,
    COUNT(DISTINCT d.match_id) AS mat,
    SUM(d.runs_batter) AS runs,
    ths.hs_final AS hs, 
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
LEFT JOIN match_scores ms ON d.batter = ms.batter AND d.match_id = ms.match_id
GROUP BY d.batter, lt.current_team, ths.hs_final, dis.total_outs;

-- 4. GLOBAL BOWLING MASTER
DROP MATERIALIZED VIEW IF EXISTS view_bowler_master CASCADE;

CREATE MATERIALIZED VIEW view_bowler_master AS
WITH player_latest_team AS (
    SELECT DISTINCT ON (bowler) bowler, bowling_team as current_team
    FROM deliveries d JOIN matches m ON d.match_id = m.match_id
    ORDER BY bowler, m.match_date DESC, m.match_id DESC
),
match_wickets AS (
    SELECT bowler, match_id, COUNT(CASE WHEN wicket_type IN ('bowled', 'caught', 'lbw', 'stumped', 'caught and bowled') THEN 1 END) as w_in_match
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

-- 5. TEAM RIVALRY MASTER
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
    (SELECT bowler FROM bowling_riv bw WHERE bw.sa = m.side_a AND bw.sb = m.side_b ORDER BY tw DESC LIMIT 1) as top_bowler,
    (SELECT tw FROM bowling_riv bw WHERE bw.sa = m.side_a AND bw.sb = m.side_b ORDER BY tw DESC LIMIT 1) as max_wickets
FROM match_summaries m;

-- 6. RACE MATRICES
DROP MATERIALIZED VIEW IF EXISTS view_player_race_matrix;
CREATE MATERIALIZED VIEW view_player_race_matrix AS
WITH all_m AS (SELECT match_id, ROW_NUMBER() OVER (ORDER BY match_date, match_id) as global_num FROM matches),
m_scores AS (SELECT batter as p, match_id, SUM(runs_batter) as r FROM deliveries GROUP BY batter, match_id)
SELECT p.batter as player, array_agg(SUM(COALESCE(ms.r, 0)) OVER (PARTITION BY p.batter ORDER BY m.global_num) ORDER BY m.global_num) as history
FROM (SELECT DISTINCT batter FROM deliveries) p CROSS JOIN all_m m LEFT JOIN m_scores ms ON p.batter = ms.p AND m.match_id = ms.match_id GROUP BY p.batter;

DROP MATERIALIZED VIEW IF EXISTS view_bowler_race_matrix;
CREATE MATERIALIZED VIEW view_bowler_race_matrix AS
WITH all_m AS (SELECT match_id, ROW_NUMBER() OVER (ORDER BY match_date, match_id) as global_num FROM matches),
m_wkts AS (SELECT bowler as p, match_id, COUNT(CASE WHEN wicket_type IN ('bowled', 'caught', 'lbw', 'stumped', 'caught and bowled') THEN 1 END) as w FROM deliveries GROUP BY bowler, match_id)
SELECT p.bowler as player, array_agg(SUM(COALESCE(mw.w, 0)) OVER (PARTITION BY p.bowler ORDER BY m.global_num) ORDER BY m.global_num) as history
FROM (SELECT DISTINCT bowler FROM deliveries) p CROSS JOIN all_m m LEFT JOIN m_wkts mw ON p.bowler = mw.p AND m.match_id = mw.match_id GROUP BY p.bowler;

-- 7. REFRESH & INDEXING
REFRESH MATERIALIZED VIEW view_batter_master;
REFRESH MATERIALIZED VIEW view_bowler_master;
REFRESH MATERIALIZED VIEW view_team_rivalry_master;
REFRESH MATERIALIZED VIEW view_player_race_matrix;
REFRESH MATERIALIZED VIEW view_bowler_race_matrix;

CREATE INDEX idx_batter_player ON view_batter_master(player);
CREATE INDEX idx_bowler_player ON view_bowler_master(player);
CREATE INDEX idx_riv_teams ON view_team_rivalry_master(side_a, side_b);