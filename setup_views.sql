-- ==========================================
-- IPL MASTER CLEANUP & VIEW RECREATION
-- ==========================================

-- 1. STANDARDIZE TEAM NAMES (Historical & Inconsistencies)
UPDATE matches
SET 
    team1 = CASE 
        WHEN team1 IN ('Royal Challengers Bangalore', 'R C Bangalore') THEN 'Royal Challengers Bengaluru'
        WHEN team1 IN ('Kings XI Punjab', 'KXIP') THEN 'Punjab Kings'
        WHEN team1 = 'Delhi Daredevils' THEN 'Delhi Capitals'
        WHEN team1 = 'Deccan Chargers' THEN 'Sunrisers Hyderabad' -- Optional: depending on if you want to merge them
        WHEN team1 = 'Rising Pune Supergiants' THEN 'Rising Pune Supergiant'
        ELSE team1 
    END,
    team2 = CASE 
        WHEN team2 IN ('Royal Challengers Bangalore', 'R C Bangalore') THEN 'Royal Challengers Bengaluru'
        WHEN team2 IN ('Kings XI Punjab', 'KXIP') THEN 'Punjab Kings'
        WHEN team2 = 'Delhi Daredevils' THEN 'Delhi Capitals'
        WHEN team2 = 'Deccan Chargers' THEN 'Sunrisers Hyderabad'
        WHEN team2 = 'Rising Pune Supergiants' THEN 'Rising Pune Supergiant'
        ELSE team2 
    END,
    winner = CASE 
        WHEN winner IN ('Royal Challengers Bangalore', 'R C Bangalore') THEN 'Royal Challengers Bengaluru'
        WHEN winner IN ('Kings XI Punjab', 'KXIP') THEN 'Punjab Kings'
        WHEN winner = 'Delhi Daredevils' THEN 'Delhi Capitals'
        WHEN winner = 'Deccan Chargers' THEN 'Sunrisers Hyderabad'
        WHEN winner = 'Rising Pune Supergiants' THEN 'Rising Pune Supergiant'
        ELSE winner 
    END;

UPDATE deliveries
SET 
    batting_team = CASE 
        WHEN batting_team IN ('Royal Challengers Bangalore', 'R C Bangalore') THEN 'Royal Challengers Bengaluru'
        WHEN batting_team = 'Kings XI Punjab' THEN 'Punjab Kings'
        WHEN batting_team = 'Delhi Daredevils' THEN 'Delhi Capitals'
        WHEN batting_team = 'Deccan Chargers' THEN 'Sunrisers Hyderabad'
        WHEN batting_team = 'Rising Pune Supergiants' THEN 'Rising Pune Supergiant'
        ELSE batting_team 
    END,
    bowling_team = CASE 
        WHEN bowling_team IN ('Royal Challengers Bangalore', 'R C Bangalore') THEN 'Royal Challengers Bengaluru'
        WHEN bowling_team = 'Kings XI Punjab' THEN 'Punjab Kings'
        WHEN bowling_team = 'Delhi Daredevils' THEN 'Delhi Capitals'
        WHEN bowling_team = 'Deccan Chargers' THEN 'Sunrisers Hyderabad'
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
    WHEN venue ILIKE '%Dharamsala%' OR venue ILIKE '%Himachal Pradesh%' THEN 'HPCA Stadium, Dharamsala'
    ELSE venue 
END;

-- 3. RECREATE MASTER VIEWS
-- We use CASCADE to ensure that any old dependent views are also refreshed
DROP VIEW IF EXISTS view_batter_master CASCADE;
DROP VIEW IF EXISTS view_bowler_master CASCADE;
DROP VIEW IF EXISTS leaderboard_awards CASCADE;

-- Awards View
CREATE VIEW leaderboard_awards AS
SELECT player_of_match AS player, COUNT(*) AS mom_awards
FROM matches
GROUP BY player_of_match;

-- Master Batting View
CREATE VIEW view_batter_master AS
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
    COUNT(DISTINCT CASE WHEN ms.runs_in_match >= 50 AND ms.runs_in_match < 100 THEN d.match_id END) AS "50s",
    COALESCE(a.mom_awards, 0) AS mom_awards
FROM deliveries d
LEFT JOIN match_stats ms ON d.batter = ms.batter AND d.match_id = ms.match_id
LEFT JOIN leaderboard_awards a ON d.batter = a.player
GROUP BY d.batter, d.batting_team, a.mom_awards;

-- Master Bowling View
CREATE VIEW view_bowler_master AS
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