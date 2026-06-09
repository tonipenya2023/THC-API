-- THC Hall of Fame layer
-- Objetivo:
-- 1) Guardar el Salón de la Fama histórico por temporada.
-- 2) Mantener una tabla bruta con todo lo recibido.
-- 3) Filtrar marcas imposibles/tramposos mediante una tabla de exclusiones.
-- 4) Exponer vistas limpias para Metabase.
-- Conceptos:
-- - Hall of Fame: TOP 1 cerrado por temporada, especie y tipo.
-- - Leaderboards actuales: temporada activa, se reinician al cambiar temporada.
-- - Mejores marcas: records personales del jugador.
CREATE TABLE IF NOT EXISTS api.hall_of_fame_records (
    hall_of_fame_record_id bigserial PRIMARY KEY,
    season_id integer NOT NULL,
    species_id integer NOT NULL,
    species_name text NULL,
    leaderboard_type text NOT NULL,
    rank_no integer NOT NULL DEFAULT 1,
    player_id text NULL,
    player_name text NULL,
    animal_id bigint NULL,
    score numeric NULL,
    score_type text NULL,
    source text NOT NULL DEFAULT 'api',
    synced_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT hall_of_fame_records_type_check CHECK (leaderboard_type IN ('score','range')),
    CONSTRAINT hall_of_fame_records_rank_check CHECK (rank_no >= 1)
);
CREATE INDEX IF NOT EXISTS idx_hof_records_season ON api.hall_of_fame_records(season_id);
CREATE INDEX IF NOT EXISTS idx_hof_records_species ON api.hall_of_fame_records(species_id);
CREATE INDEX IF NOT EXISTS idx_hof_records_type ON api.hall_of_fame_records(leaderboard_type);
CREATE INDEX IF NOT EXISTS idx_hof_records_player ON api.hall_of_fame_records(lower(player_name));
CREATE INDEX IF NOT EXISTS idx_hof_records_lookup ON api.hall_of_fame_records(season_id, species_id, leaderboard_type, rank_no);
CREATE TABLE IF NOT EXISTS api.hall_of_fame_exclusions (
    exclusion_id bigserial PRIMARY KEY,
    season_id integer NULL,
    species_id integer NULL,
    species_name text NULL,
    leaderboard_type text NULL,
    player_id text NULL,
    player_name text NULL,
    animal_id bigint NULL,
    min_score numeric NULL,
    max_score numeric NULL,
    reason text NOT NULL,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT hall_of_fame_exclusions_type_check CHECK (leaderboard_type IS NULL OR leaderboard_type IN ('score','range'))
);
CREATE INDEX IF NOT EXISTS idx_hof_exclusions_active ON api.hall_of_fame_exclusions(active);
CREATE INDEX IF NOT EXISTS idx_hof_exclusions_season ON api.hall_of_fame_exclusions(season_id);
CREATE INDEX IF NOT EXISTS idx_hof_exclusions_species ON api.hall_of_fame_exclusions(species_id);
CREATE INDEX IF NOT EXISTS idx_hof_exclusions_type ON api.hall_of_fame_exclusions(leaderboard_type);
CREATE INDEX IF NOT EXISTS idx_hof_exclusions_player ON api.hall_of_fame_exclusions(lower(player_name));
DROP VIEW IF EXISTS api.vw_hall_of_fame_clean CASCADE;
CREATE VIEW api.vw_hall_of_fame_clean AS SELECT r.* FROM api.hall_of_fame_records r WHERE NOT EXISTS (SELECT 1 FROM api.hall_of_fame_exclusions e WHERE e.active = true AND (e.season_id IS NULL OR e.season_id = r.season_id) AND (e.species_id IS NULL OR e.species_id = r.species_id) AND (e.species_name IS NULL OR lower(e.species_name) = lower(r.species_name)) AND (e.leaderboard_type IS NULL OR e.leaderboard_type = r.leaderboard_type) AND (e.player_id IS NULL OR e.player_id = r.player_id) AND (e.player_name IS NULL OR lower(e.player_name) = lower(r.player_name)) AND (e.animal_id IS NULL OR e.animal_id = r.animal_id) AND (e.min_score IS NULL OR r.score >= e.min_score) AND (e.max_score IS NULL OR r.score <= e.max_score));
DROP VIEW IF EXISTS api.vw_hall_of_fame_top1_clean CASCADE;
CREATE VIEW api.vw_hall_of_fame_top1_clean AS SELECT * FROM (SELECT r.*, row_number() OVER (PARTITION BY r.season_id, r.species_id, r.leaderboard_type ORDER BY r.rank_no ASC, r.score DESC NULLS LAST, r.hall_of_fame_record_id ASC) AS clean_rank FROM api.vw_hall_of_fame_clean r) x WHERE clean_rank = 1;
DROP VIEW IF EXISTS api.vw_hall_of_fame_all_time_clean CASCADE;
CREATE VIEW api.vw_hall_of_fame_all_time_clean AS SELECT * FROM (SELECT r.*, row_number() OVER (PARTITION BY r.species_id, r.leaderboard_type ORDER BY r.score DESC NULLS LAST, r.season_id DESC, r.hall_of_fame_record_id ASC) AS all_time_rank FROM api.vw_hall_of_fame_clean r) x WHERE all_time_rank = 1;
DROP VIEW IF EXISTS api.vw_hall_of_fame_player_summary CASCADE;
CREATE VIEW api.vw_hall_of_fame_player_summary AS SELECT player_name, leaderboard_type, COUNT(*) AS records_count, COUNT(DISTINCT species_id) AS species_count, MIN(season_id) AS first_season, MAX(season_id) AS last_season FROM api.vw_hall_of_fame_top1_clean WHERE player_name IS NOT NULL GROUP BY player_name, leaderboard_type;
DROP VIEW IF EXISTS api.vw_hall_of_fame_nefastix13 CASCADE;
CREATE VIEW api.vw_hall_of_fame_nefastix13 AS SELECT * FROM api.vw_hall_of_fame_top1_clean WHERE lower(player_name) = lower('Nefastix13');
