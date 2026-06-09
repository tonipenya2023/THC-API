-- 01 KPI Hunter Overview
SELECT handle, hostname, hunter_score, rank_no, lifetime_hours, lifetime_km, lifetime_kills, lifetime_ethical_kills, ROUND(lifetime_ethical_kills::numeric / NULLIF(lifetime_kills, 0) * 100, 2) AS ethical_pct FROM api.vw_hunter_overview;
-- 02 Weekly Activity
SELECT week_start, expeditions, kills, collectables, hours, kills_per_hour FROM api.vw_expedition_weekly ORDER BY week_start;
-- 03 Top Weapons by Kills
SELECT weapon_name, kills, hits, misses, accuracy_pct, ethical_pct, lethality_pct, avg_distance_per_kill FROM api.vw_weapon_analytics WHERE kills > 0 ORDER BY kills DESC;
-- 04 Weapon Accuracy Scatter
SELECT weapon_name, hits, kills, misses, accuracy_pct, ethical_pct, avg_distance_per_kill FROM api.vw_weapon_analytics WHERE hits > 0 ORDER BY hits DESC;
-- 05 Species Distribution
SELECT species_name, kills, ethical_kills, spots, tracks, ethical_pct, kill_share_pct FROM api.vw_species_analytics WHERE kills > 0 ORDER BY kills DESC;
-- 06 Hardest Species
SELECT species_name, kills, tracks, spots, tracks_per_kill, spots_per_kill FROM api.vw_species_analytics WHERE kills > 0 ORDER BY tracks_per_kill DESC NULLS LAST;
-- 07 Reserve Performance
SELECT reserve_name, expeditions, kills, collectables, hours, kills_per_expedition, kills_per_hour, first_seen_at, last_seen_at FROM api.vw_reserve_performance ORDER BY kills DESC;
-- 08 Personal Score Records
SELECT species_name, animal_id, score, distance, weapon_name, confirm_at, gender, texture FROM api.vw_personal_records WHERE record_type = 'score' ORDER BY score DESC NULLS LAST;
-- 09 Personal Distance Records
SELECT species_name, animal_id, distance, score, weapon_name, confirm_at, gender, texture FROM api.vw_personal_records WHERE record_type = 'distance' ORDER BY distance DESC NULLS LAST;
-- 10 Leaderboard Top 100 Score
SELECT species_name, animal_id, rank_no, handle, score, score_type FROM api.vw_leaderboard_top100 WHERE leaderboard_type = 'score' ORDER BY species_name, rank_no;
-- 11 Leaderboard Top 100 Range
SELECT species_name, animal_id, rank_no, handle, score, score_type FROM api.vw_leaderboard_top100 WHERE leaderboard_type = 'range' ORDER BY species_name, rank_no;
-- 12 Hunter vs Leaderboard Placement
SELECT l.leaderboard_type, l.species_name, l.rank_no, l.handle, l.score FROM api.vw_leaderboard_top100 l JOIN api.vw_hunter_overview h ON lower(l.handle) = lower(h.handle) ORDER BY l.leaderboard_type, l.rank_no;
-- 13 Leaderboard Control
SELECT leaderboard_type, COUNT(DISTINCT species_name) AS species_count, COUNT(*) AS rows_count FROM api.vw_leaderboard_top100 GROUP BY leaderboard_type ORDER BY leaderboard_type;
