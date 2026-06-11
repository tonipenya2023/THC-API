DROP VIEW IF EXISTS api.vw_grafana_competitions CASCADE;
-- api.vw_grafana_competitions source

CREATE OR REPLACE VIEW api.vw_grafana_competitions
AS WITH refresh_request AS MATERIALIZED (
         SELECT *
           FROM api.request_dashboard_refresh('grafana_competitions', interval '10 minutes')
        ), species AS (
         SELECT x.parent_record_id,
            string_agg(x.species_name, ', '::text ORDER BY x.item_index) AS species_names,
            string_agg((x.species_name || ': '::text) || COALESCE(x.reserve_names, 'Unknown'::text), ' | '::text ORDER BY x.item_index) AS species_reserves
           FROM ( SELECT cis.parent_record_id,
                    min(cis.item_index) AS item_index,
                    safe_bigint(cis.scalar_value) AS species_id,
                    COALESCE(NULLIF(cs.field_name, ''::text), 'Species '::text || cis.scalar_value) AS species_name,
                    string_agg(DISTINCT COALESCE(NULLIF(cr.field_name, ''::text), 'Reserve '::text || cr.field_id), ', '::text) AS reserve_names
                   FROM query_competitions_info_species cis
                     LEFT JOIN query_catalog_species cs ON safe_bigint(cs.field_id) = safe_bigint(cis.scalar_value)
                     LEFT JOIN query_catalog_reserves_species crs ON safe_bigint(crs.scalar_value) = safe_bigint(cis.scalar_value)
                     LEFT JOIN query_catalog_reserves cr ON cr.record_id = crs.parent_record_id
                  GROUP BY cis.parent_record_id, (safe_bigint(cis.scalar_value)), (COALESCE(NULLIF(cs.field_name, ''::text), 'Species '::text || cis.scalar_value))) x
          GROUP BY x.parent_record_id
        ), prizes AS (
         SELECT p_1.parent_record_id,
            string_agg(concat_ws(' '::text, NULLIF(r.field_amount, ''::text), NULLIF(r.field_define, ''::text), NULLIF(r.field_type, ''::text)), ', '::text ORDER BY r.item_index) AS prize_summary
           FROM query_competitions_info_prizes p_1
             LEFT JOIN query_competitions_info_prizes_rewards r ON r.parent_record_id = p_1.record_id
          GROUP BY p_1.parent_record_id
        ), entrants AS (
         SELECT query_competitions_entrants.parent_record_id,
            count(*) AS entrants_loaded,
            min(safe_numeric(query_competitions_entrants.field_points)) AS min_points,
            max(safe_numeric(query_competitions_entrants.field_points)) AS max_points
           FROM query_competitions_entrants
          GROUP BY query_competitions_entrants.parent_record_id
        )
 SELECT safe_bigint(i.field_id) AS competition_id,
    i.field_type_field_name AS competition_name,
    i.field_type_field_descriptionshort AS description_short,
    i.field_type_field_pointtype AS point_type,
    safe_timestamptz(i.field_start) AS start_at,
    safe_timestamptz(i.field_end) AS end_at,
        CASE
            WHEN i.field_finished = ANY (ARRAY['1'::text, 'true'::text, 'True'::text]) THEN true
            ELSE false
        END AS finished,
    safe_bigint(c.field_competitions_total) AS competitions_total,
    safe_bigint(c.field_entrants_total) AS entrants_total,
    e.entrants_loaded,
    e.min_points,
    e.max_points,
    s.species_names,
    s.species_reserves,
    p.prize_summary,
    rr.status AS refresh_status,
    rr.requested_at AS refresh_requested_at,
    rr.last_completed_at AS refresh_completed_at
   FROM query_competitions_info i
     LEFT JOIN query_competitions c ON c.record_id = i.parent_record_id
     LEFT JOIN species s ON s.parent_record_id = i.record_id
     LEFT JOIN prizes p ON p.parent_record_id = i.record_id
     LEFT JOIN entrants e ON e.parent_record_id = i.record_id
     CROSS JOIN refresh_request rr;

DROP VIEW IF EXISTS api.vw_grafana_statistics_summary CASCADE;
CREATE VIEW api.vw_grafana_statistics_summary AS
 SELECT handle as "Cazador",
    hunter_score as "Hunter Score",
    rank_no as "Rank #",
    lifetime_kills as "Muertes",
    lifetime_ethical_kills as "Muertes Éticas",
    lifetime_spots as "Marcajes",
    lifetime_tracks as "Seguimientos",
    lifetime_hours as "Horas",
    lifetime_km as "Km",
    round(lifetime_ethical_kills / NULLIF(lifetime_kills, 0::numeric) * 100::numeric, 2) as "% Muertes Eticas"
   FROM vw_hunter_overview;

DROP VIEW IF EXISTS api.vw_grafana_statistics_species CASCADE;
CREATE VIEW api.vw_grafana_statistics_species AS
SELECT species_icon_url_by_define(species_define) AS animal_icon_url,
    species_id ,
    species_name "Especie",
    kills "Muertes",
    ethical_kills "Éticas",
    ethical_pct "% Éticas",
    spots "Marcajes",
    tracks "Seguimientos",
    spots_per_kill "Marcajes/Muertes",
    tracks_per_kill "Seguientos/Muertes",
    kill_share_pct "% Especie/Total Muertes"
   FROM vw_species_analytics;

DROP VIEW IF EXISTS api.vw_grafana_statistics_weapons CASCADE;
CREATE VIEW api.vw_grafana_statistics_weapons AS
SELECT weapon_id,
    weapon_icon_url "Icono Munición",
    weapon_name "Munición",
    weapon_type "Tipo Munición",
    weapon_type_description "Descripción Tipo Arma",
    hits "Disparos",
    kills "Muertes",
    misses "Fallidos",
    ethical_kills "Muertes Éticas",
    accuracy_pct "% Precisión",
    ethical_pct "% Eticas",
    lethality_pct "% Muertes/Disparo",
    avg_distance_per_kill "Media Distancia/Muerte",
    usage_kill_share_pct "% Arma/Total Muertes"
   FROM vw_weapon_analytics;

DROP VIEW IF EXISTS api.vw_grafana_expedition_kills_full CASCADE;
DROP VIEW IF EXISTS api.vw_grafana_expeditions CASCADE;
CREATE VIEW api.vw_grafana_expeditions AS
SELECT
    api.safe_bigint(e.field_id) AS expedition_id,
    COALESCE(NULLIF(r.field_name, ''), NULLIF(e.field_reserve, ''), 'Unknown') AS reserve_name,
    e.field_map AS map_name,
    api.safe_timestamptz(e.field_start_ts) AS start_at,
    api.safe_timestamptz(e.field_end_ts) AS end_at,
    ROUND(EXTRACT(EPOCH FROM (api.safe_timestamptz(e.field_end_ts) - api.safe_timestamptz(e.field_start_ts))) / 3600, 2) AS hours,
    api.safe_bigint(e.field_kills) AS kills,
    api.safe_bigint(e.field_collectables) AS collectables,
    CASE WHEN e.field_singleplayer IN ('1', 'true', 'True') THEN true ELSE false END AS singleplayer
FROM api.query_statistics_history_expeditions e
LEFT JOIN api.query_catalog_reserves r
    ON r.field_id = e.field_reserve;

DROP VIEW IF EXISTS api.vw_grafana_expedition_kills CASCADE;
CREATE VIEW api.vw_grafana_expedition_kills AS
SELECT
    api.safe_bigint(k.field_expeditionid) AS expedition_id,
    api.safe_bigint(k.field_id) AS animal_id,
    api.animal_profile_url((SELECT field_handle FROM api.query_user_by_hostname ORDER BY record_id LIMIT 1), api.safe_bigint(k.field_id)) AS animal_profile_url,
    k.field_speciesname AS species_name,
    api.species_icon_url(k.field_speciesname) AS animal_icon_url,
    k.field_gender AS gender,
    k.field_texture AS texture,
    api.safe_numeric(k.field_kill_field_score) AS score,
    k.field_kill_field_scoretype AS score_type,
    api.safe_numeric(k.field_weight) AS weight,
    CASE WHEN k.field_kill_field_ethical IN ('1', 'true', 'True') THEN true ELSE false END AS ethical,
    k.field_kill_field_photo AS photo_url,
    api.safe_timestamptz(k.field_kill_field_confirmts) AS confirm_at
FROM api.query_statistics_expeditions_details_kills k;

CREATE VIEW api.vw_grafana_expedition_kills_full AS
SELECT
    e.expedition_id,
    e.reserve_name,
    e.map_name,
    e.start_at,
    e.end_at,
    e.hours,
    e.kills,
    e.collectables,
    e.singleplayer,
    k.animal_id,
    k.animal_profile_url,
    k.species_name,
    k.animal_icon_url,
    k.gender,
    k.texture,
    k.score,
    k.score_type,
    k.weight,
    k.ethical,
    k.photo_url,
    k.confirm_at
FROM api.vw_grafana_expeditions e
LEFT JOIN api.vw_grafana_expedition_kills k
    ON k.expedition_id = e.expedition_id;

DROP VIEW IF EXISTS api.vw_grafana_gallery_photos CASCADE;
CREATE VIEW api.vw_grafana_gallery_photos AS
SELECT
    api.safe_bigint(field_id) AS photo_id,
    field_thumbnail AS thumbnail_url,
    field_url AS photo_url,
    COALESCE(NULLIF(field_label, ''), NULLIF(field_animal_field_species, ''), 'Photo') AS label,
    field_type AS photo_type,
    api.safe_bigint(field_animal_field_id) AS animal_id,
    field_animal_field_species AS species_name,
    api.species_icon_url(field_animal_field_species) AS animal_icon_url,
    api.safe_numeric(field_animal_field_score) AS score,
    field_animal_field_scoretype AS score_type
FROM api.query_gallery_photos;

DROP VIEW IF EXISTS api.vw_grafana_personal_best CASCADE;
CREATE VIEW api.vw_grafana_personal_best AS
SELECT
    record_type,
    api.species_icon_url(species_name) AS animal_icon_url,
    species_id,
    species_name,
    animal_id,
    animal_profile_url((SELECT field_handle FROM api.query_user_by_hostname ORDER BY record_id LIMIT 1), animal_id) AS animal_profile_url,
    score,
    distance,
    weapon_id,
    weapon_name,
    confirm_at,
    gender,
    texture
FROM api.vw_personal_records;

DROP VIEW IF EXISTS api.vw_grafana_trophies CASCADE;
CREATE VIEW api.vw_grafana_trophies AS
SELECT
    api.safe_bigint(field_id) AS record_id,
    api.safe_bigint(field_trophy_id) AS trophy_id,
    field_image AS trophy_icon_url,
    field_name AS trophy_name,
    field_competition_name AS competition_name,
    api.safe_bigint(field_competition_id) AS competition_id,
    api.safe_timestamptz(field_ts) AS awarded_at
FROM api.query_trophies_trophies;

DROP VIEW IF EXISTS api.vw_grafana_classification_tables CASCADE;
CREATE VIEW api.vw_grafana_classification_tables AS
SELECT
    leaderboard_type,
    animal_icon_url,
    species_name,
    medal_icon_url,
    rank_no,
    avatar_url,
    handle AS hunter,
    score,
    score_type,
    animal_id,
    animal_profile_url
FROM api.vw_leaderboard_top100;
