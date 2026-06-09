-- Control general
SELECT COUNT(*) FROM api.vw_hunter_overview;
SELECT COUNT(*) FROM api.vw_weapon_analytics;
SELECT COUNT(*) FROM api.vw_species_analytics;
SELECT COUNT(*) FROM api.vw_expedition_weekly;
SELECT COUNT(*) FROM api.vw_reserve_performance;
SELECT COUNT(*) FROM api.vw_personal_records;
SELECT COUNT(*) FROM api.vw_leaderboard_top100;
-- Control leaderboards
SELECT leaderboard_type, COUNT(DISTINCT species_name) AS species_count, COUNT(*) AS rows_count FROM api.vw_leaderboard_top100 GROUP BY leaderboard_type ORDER BY leaderboard_type;
-- Top armas
SELECT weapon_name, kills, accuracy_pct, ethical_pct FROM api.vw_weapon_analytics WHERE kills > 0 ORDER BY kills DESC;
-- Top especies
SELECT species_name, kills, ethical_pct, tracks_per_kill FROM api.vw_species_analytics WHERE kills > 0 ORDER BY kills DESC;
-- Records
SELECT record_type, species_name, animal_id, score, distance, weapon_name FROM api.vw_personal_records ORDER BY record_type, score DESC NULLS LAST;
