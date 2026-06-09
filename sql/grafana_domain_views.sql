DROP VIEW IF EXISTS api.vw_grafana_competitions CASCADE;
CREATE VIEW api.vw_grafana_competitions AS
WITH species AS (
    SELECT
        cis.parent_record_id,
        string_agg(
            COALESCE(NULLIF(cs.field_name, ''), 'Species ' || cis.scalar_value),
            ', '
            ORDER BY cis.item_index
        ) AS species_names,
        string_agg(
            DISTINCT COALESCE(NULLIF(r.field_name, ''), 'Unknown'),
            ', '
        ) AS reserve_names
    FROM query_competitions_info_species cis
    LEFT JOIN query_catalog_species cs
        ON safe_bigint(cs.field_id) = safe_bigint(cis.scalar_value)
    LEFT JOIN query_catalog_reserves_species rs
        ON safe_bigint(rs.scalar_value) = safe_bigint(cis.scalar_value)
    LEFT JOIN query_catalog_reserves r
        ON r.record_id = rs.parent_record_id
    GROUP BY cis.parent_record_id
),
prizes AS (
    SELECT
        p_1.parent_record_id,
        string_agg(
            concat_ws(' ', NULLIF(r.field_amount, ''), NULLIF(r.field_define, ''), NULLIF(r.field_type, '')),
            ', '
            ORDER BY r.item_index
        ) AS prize_summary
    FROM query_competitions_info_prizes p_1
    LEFT JOIN query_competitions_info_prizes_rewards r
        ON r.parent_record_id = p_1.record_id
    GROUP BY p_1.parent_record_id
),
entrants AS (
    SELECT
        parent_record_id,
        count(*) AS entrants_loaded,
        min(safe_numeric(field_points)) AS min_points,
        max(safe_numeric(field_points)) AS max_points
    FROM query_competitions_entrants
    GROUP BY parent_record_id
)
SELECT
    safe_bigint(i.field_id) AS competition_id,
    i.field_type_field_name AS competition_name,
    i.field_type_field_descriptionshort AS description_short,
    i.field_type_field_pointtype AS point_type,
    safe_timestamptz(i.field_start) AS start_at,
    safe_timestamptz(i.field_end) AS end_at,
    CASE
        WHEN i.field_finished = ANY (ARRAY['1', 'true', 'True']) THEN true
        ELSE false
    END AS finished,
    safe_bigint(c.field_competitions_total) AS competitions_total,
    safe_bigint(c.field_entrants_total) AS entrants_total,
    e.entrants_loaded,
    e.min_points,
    e.max_points,
    s.species_names,
    s.reserve_names,
    p.prize_summary
FROM query_competitions_info i
LEFT JOIN query_competitions c
    ON c.record_id = i.parent_record_id
LEFT JOIN species s
    ON s.parent_record_id = i.record_id
LEFT JOIN prizes p
    ON p.parent_record_id = i.record_id
LEFT JOIN entrants e
    ON e.parent_record_id = i.record_id;

DROP VIEW IF EXISTS api.vw_grafana_statistics_summary CASCADE;
CREATE VIEW api.vw_grafana_statistics_summary AS
SELECT
    handle,
    hunter_score,
    rank_no,
    lifetime_kills,
    lifetime_ethical_kills,
    lifetime_spots,
    lifetime_tracks,
    lifetime_hours,
    lifetime_km,
    ROUND(lifetime_ethical_kills::numeric / NULLIF(lifetime_kills, 0) * 100, 2) AS ethical_pct
FROM api.vw_hunter_overview;

DROP VIEW IF EXISTS api.vw_grafana_statistics_species CASCADE;
CREATE VIEW api.vw_grafana_statistics_species AS
SELECT
    api.species_icon_url(species_name) AS animal_icon_url,
    species_id,
    species_name,
    kills,
    ethical_kills,
    ethical_pct,
    spots,
    tracks,
    spots_per_kill,
    tracks_per_kill,
    kill_share_pct
FROM api.vw_species_analytics;

DROP VIEW IF EXISTS api.vw_grafana_statistics_weapons CASCADE;
CREATE VIEW api.vw_grafana_statistics_weapons AS
SELECT
    weapon_id,
    weapon_name,
    weapon_type,
    hits,
    kills,
    misses,
    ethical_kills,
    accuracy_pct,
    ethical_pct,
    lethality_pct,
    avg_distance_per_kill,
    usage_kill_share_pct
FROM api.vw_weapon_analytics;

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
