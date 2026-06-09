CREATE SCHEMA IF NOT EXISTS api;

CREATE TABLE IF NOT EXISTS api.catalog_sync_runs (
    sync_run_id bigserial PRIMARY KEY,
    lang text NOT NULL,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    status text NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
    catalogs_count integer NOT NULL DEFAULT 0,
    entries_count integer NOT NULL DEFAULT 0,
    error_message text
);

CREATE TABLE IF NOT EXISTS api.catalog_entries (
    catalog_name text NOT NULL,
    external_id text NOT NULL,
    lang text NOT NULL,
    payload jsonb NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    synced_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (catalog_name, external_id, lang)
);

CREATE TABLE IF NOT EXISTS api.item_categories (
    category_id text NOT NULL,
    lang text NOT NULL,
    title text,
    default_subcategory_id text,
    payload jsonb NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (category_id, lang)
);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'api'
          AND table_name = 'item_categories'
          AND column_name = 'is_default'
    ) THEN
        ALTER TABLE api.item_categories
            RENAME COLUMN is_default TO default_subcategory_id;
        ALTER TABLE api.item_categories
            ALTER COLUMN default_subcategory_id TYPE text
            USING default_subcategory_id::text;
    END IF;
END
$$;

CREATE TABLE IF NOT EXISTS api.item_subcategories (
    subcategory_id text NOT NULL,
    category_id text NOT NULL,
    lang text NOT NULL,
    title text,
    payload jsonb NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (subcategory_id, lang),
    FOREIGN KEY (category_id, lang)
        REFERENCES api.item_categories(category_id, lang)
);

CREATE TABLE IF NOT EXISTS api.items (
    item_id bigint NOT NULL,
    lang text NOT NULL,
    define text,
    name text,
    category_id text,
    subcategory_id text,
    item_type text,
    payload jsonb NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (item_id, lang)
);

CREATE TABLE IF NOT EXISTS api.species (
    species_id bigint NOT NULL,
    lang text NOT NULL,
    define text,
    name text,
    short_name text,
    payload jsonb NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (species_id, lang)
);

CREATE TABLE IF NOT EXISTS api.reserves (
    reserve_id bigint NOT NULL,
    lang text NOT NULL,
    define text,
    name text,
    payload jsonb NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (reserve_id, lang)
);

CREATE TABLE IF NOT EXISTS api.reserve_species (
    reserve_id bigint NOT NULL,
    species_id bigint NOT NULL,
    lang text NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (reserve_id, species_id, lang),
    FOREIGN KEY (reserve_id, lang) REFERENCES api.reserves(reserve_id, lang),
    FOREIGN KEY (species_id, lang) REFERENCES api.species(species_id, lang)
);

CREATE TABLE IF NOT EXISTS api.locations (
    location_id bigint NOT NULL,
    lang text NOT NULL,
    reserve_id bigint,
    define text,
    name text,
    location_type text,
    payload jsonb NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (location_id, lang)
);

CREATE TABLE IF NOT EXISTS api.missions (
    mission_id bigint NOT NULL,
    lang text NOT NULL,
    title text,
    description text,
    payload jsonb NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (mission_id, lang)
);

CREATE TABLE IF NOT EXISTS api.mission_species (
    mission_id bigint NOT NULL,
    species_id bigint NOT NULL,
    lang text NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (mission_id, species_id, lang),
    FOREIGN KEY (mission_id, lang) REFERENCES api.missions(mission_id, lang)
);

CREATE TABLE IF NOT EXISTS api.mission_weapons (
    mission_id bigint NOT NULL,
    item_id bigint NOT NULL,
    lang text NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (mission_id, item_id, lang),
    FOREIGN KEY (mission_id, lang) REFERENCES api.missions(mission_id, lang)
);

CREATE TABLE IF NOT EXISTS api.mission_reserves (
    mission_id bigint NOT NULL,
    reserve_id bigint NOT NULL,
    lang text NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (mission_id, reserve_id, lang),
    FOREIGN KEY (mission_id, lang) REFERENCES api.missions(mission_id, lang)
);

CREATE TABLE IF NOT EXISTS api.mission_dependencies (
    mission_id bigint NOT NULL,
    dependency_mission_id bigint NOT NULL,
    lang text NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (mission_id, dependency_mission_id, lang),
    FOREIGN KEY (mission_id, lang) REFERENCES api.missions(mission_id, lang)
);

CREATE TABLE IF NOT EXISTS api.mission_groups (
    mission_group_id bigint NOT NULL,
    lang text NOT NULL,
    title text,
    description text,
    payload jsonb NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (mission_group_id, lang)
);

CREATE TABLE IF NOT EXISTS api.mission_group_missions (
    mission_group_id bigint NOT NULL,
    mission_id bigint NOT NULL,
    lang text NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (mission_group_id, mission_id, lang),
    FOREIGN KEY (mission_group_id, lang)
        REFERENCES api.mission_groups(mission_group_id, lang)
);

CREATE TABLE IF NOT EXISTS api.mission_group_species (
    mission_group_id bigint NOT NULL,
    species_id bigint NOT NULL,
    lang text NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (mission_group_id, species_id, lang),
    FOREIGN KEY (mission_group_id, lang)
        REFERENCES api.mission_groups(mission_group_id, lang)
);

CREATE TABLE IF NOT EXISTS api.mission_group_weapons (
    mission_group_id bigint NOT NULL,
    item_id bigint NOT NULL,
    lang text NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (mission_group_id, item_id, lang),
    FOREIGN KEY (mission_group_id, lang)
        REFERENCES api.mission_groups(mission_group_id, lang)
);

CREATE TABLE IF NOT EXISTS api.mission_group_reserves (
    mission_group_id bigint NOT NULL,
    reserve_id bigint NOT NULL,
    lang text NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (mission_group_id, reserve_id, lang),
    FOREIGN KEY (mission_group_id, lang)
        REFERENCES api.mission_groups(mission_group_id, lang)
);

CREATE TABLE IF NOT EXISTS api.collectables (
    collectable_id bigint NOT NULL,
    lang text NOT NULL,
    define text,
    name text,
    category text,
    species_define text,
    payload jsonb NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (collectable_id, lang)
);

CREATE TABLE IF NOT EXISTS api.achievements (
    achievement_id bigint NOT NULL,
    lang text NOT NULL,
    title text,
    category_id text,
    group_id text,
    payload jsonb NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (achievement_id, lang)
);

CREATE TABLE IF NOT EXISTS api.achievement_categories (
    achievement_category_id text NOT NULL,
    lang text NOT NULL,
    title text,
    payload jsonb NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (achievement_category_id, lang)
);

CREATE TABLE IF NOT EXISTS api.rank_categories (
    rank_category_id text NOT NULL,
    lang text NOT NULL,
    title text,
    rank_key text,
    payload jsonb NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (rank_category_id, lang)
);

CREATE TABLE IF NOT EXISTS api.dog_skills (
    dog_skill_id bigint NOT NULL,
    lang text NOT NULL,
    level integer,
    xp integer,
    payload jsonb NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (dog_skill_id, lang)
);

CREATE TABLE IF NOT EXISTS api.bundles (
    bundle_id bigint NOT NULL,
    lang text NOT NULL,
    define text,
    name text,
    payload jsonb NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (bundle_id, lang)
);

CREATE TABLE IF NOT EXISTS api.bundle_items (
    bundle_id bigint NOT NULL,
    item_id bigint NOT NULL,
    lang text NOT NULL,
    quantity integer NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (bundle_id, item_id, lang),
    FOREIGN KEY (bundle_id, lang) REFERENCES api.bundles(bundle_id, lang)
);

ALTER TABLE api.bundle_items
    ADD COLUMN IF NOT EXISTS quantity integer NOT NULL DEFAULT 1;

CREATE TABLE IF NOT EXISTS api.tutorials (
    tutorial_id bigint NOT NULL,
    lang text NOT NULL,
    reserve_id bigint,
    name text,
    payload jsonb NOT NULL,
    sync_run_id bigint NOT NULL REFERENCES api.catalog_sync_runs(sync_run_id),
    PRIMARY KEY (tutorial_id, lang)
);

CREATE OR REPLACE VIEW api.v_items AS
SELECT
    i.item_id,
    i.lang,
    i.define,
    i.name,
    i.category_id,
    c.title AS category_title,
    i.subcategory_id,
    s.title AS subcategory_title,
    i.item_type,
    i.payload
FROM api.items i
LEFT JOIN api.item_categories c
    ON c.category_id = i.category_id AND c.lang = i.lang
LEFT JOIN api.item_subcategories s
    ON s.subcategory_id = i.subcategory_id AND s.lang = i.lang;

CREATE OR REPLACE VIEW api.v_locations AS
SELECT
    l.location_id,
    l.lang,
    l.define,
    l.name,
    l.location_type,
    l.reserve_id,
    r.name AS reserve_name,
    l.payload
FROM api.locations l
LEFT JOIN api.reserves r
    ON r.reserve_id = l.reserve_id AND r.lang = l.lang;

CREATE OR REPLACE VIEW api.v_mission_species AS
SELECT
    ms.mission_id,
    m.title AS mission_title,
    ms.species_id,
    s.name AS species_name,
    ms.lang
FROM api.mission_species ms
JOIN api.missions m
    ON m.mission_id = ms.mission_id AND m.lang = ms.lang
LEFT JOIN api.species s
    ON s.species_id = ms.species_id AND s.lang = ms.lang;

CREATE OR REPLACE VIEW api.v_mission_weapons AS
SELECT
    mw.mission_id,
    m.title AS mission_title,
    mw.item_id,
    i.name AS item_name,
    mw.lang
FROM api.mission_weapons mw
JOIN api.missions m
    ON m.mission_id = mw.mission_id AND m.lang = mw.lang
LEFT JOIN api.items i
    ON i.item_id = mw.item_id AND i.lang = mw.lang;

CREATE TABLE IF NOT EXISTS api.query_sync_runs (
    query_sync_run_id bigserial PRIMARY KEY,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    status text NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
    functions_count integer NOT NULL DEFAULT 0,
    error_message text
);

CREATE TABLE IF NOT EXISTS api.query_table_stats (
    query_sync_run_id bigint NOT NULL REFERENCES api.query_sync_runs(query_sync_run_id),
    function_name text NOT NULL,
    root_table text NOT NULL,
    derived_table text NOT NULL,
    root_records integer NOT NULL,
    derived_records integer NOT NULL,
    PRIMARY KEY (query_sync_run_id, function_name)
);
