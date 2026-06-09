/*

-- Ejemplos de uso - Hall of Fame
-- 1. Borrar y recargar una temporada concreta
DELETE FROM api.hall_of_fame_records WHERE season_id = 46;
-- Después insertar los TOP 1 de score/range de esa temporada.
-- 2. Insertar manualmente un registro de ejemplo
INSERT INTO api.hall_of_fame_records (season_id, species_id, species_name, leaderboard_type, rank_no, player_id, player_name, animal_id, score, score_type, source) VALUES (46, 2, 'Pavo', 'range', 1, NULL, 'Nefastix13', NULL, 370.480, 'range', 'manual');
-- 3. Excluir una marca imposible por jugador y especie
INSERT INTO api.hall_of_fame_exclusions (species_id, species_name, leaderboard_type, player_name, min_score, reason) VALUES (2, 'Pavo', 'range', 'JugadorTramposo', 1000, 'Distancia imposible no corregida por el juego');
-- 4. Excluir un animal concreto
INSERT INTO api.hall_of_fame_exclusions (animal_id, reason) VALUES (1234567890, 'Animal marcado como tramposo');
-- 5. Excluir una marca por temporada
INSERT INTO api.hall_of_fame_exclusions (season_id, species_id, leaderboard_type, player_name, reason) VALUES (31, 2, 'range', 'JugadorTramposo', 'TOP 1 inválido en temporada 31');
-- 6. Ver TOP 1 limpio por temporada
SELECT season_id, species_name, leaderboard_type, player_name, score FROM api.vw_hall_of_fame_top1_clean ORDER BY season_id DESC, species_name, leaderboard_type;
-- 7. Ver mejores marcas históricas absolutas
SELECT species_name, leaderboard_type, season_id, player_name, score FROM api.vw_hall_of_fame_all_time_clean ORDER BY species_name, leaderboard_type;
-- 8. Ver records de Nefastix13 en Salón de la Fama
SELECT season_id, species_name, leaderboard_type, score FROM api.vw_hall_of_fame_nefastix13 ORDER BY season_id DESC, species_name, leaderboard_type;
-- 9. Ranking de jugadores con más records históricos
SELECT player_name, SUM(records_count) AS total_records, SUM(CASE WHEN leaderboard_type = 'range' THEN records_count ELSE 0 END) AS range_records, SUM(CASE WHEN leaderboard_type = 'score' THEN records_count ELSE 0 END) AS score_records FROM api.vw_hall_of_fame_player_summary GROUP BY player_name ORDER BY total_records DESC, player_name;
-- 10. Control de exclusiones activas
SELECT * FROM api.hall_of_fame_exclusions WHERE active = true ORDER BY created_at DESC;
*/