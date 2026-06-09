

CREATE OR REPLACE VIEW api.v_LogrosFaltantesProximoRango AS
WITH achievement_status AS (
    SELECT
        COUNT(t.scalar_value)::numeric AS logros_totales,
        SUM(
            CASE
                WHEN g.field_value IS NOT NULL
                 AND api.safe_numeric(g.field_value) >= api.safe_numeric(t.scalar_value)
                THEN 1
                ELSE 0
            END
        )::numeric AS logros_conseguidos
    FROM api.query_catalog_achievements c
    JOIN api.query_catalog_achievements_triggers t
        ON t.parent_record_id = c.record_id
    LEFT JOIN api.query_achievements_general g
        ON g.field_id = c.field_id
       AND g.field_category_id = c.field_category
),
rank_status AS (
    SELECT
        logros_conseguidos,
        logros_totales,
        (logros_conseguidos * 100.0 / NULLIF(logros_totales, 0)) AS porcentaje_logros
    FROM achievement_status
),
rank_calc AS (
    SELECT
        logros_conseguidos,
        logros_totales,
        porcentaje_logros,

        CASE
            WHEN porcentaje_logros >= 90 THEN 'Turkey'
            WHEN porcentaje_logros >= 75 THEN 'Red Fox'
            WHEN porcentaje_logros >= 50 THEN 'Black Bear'
            WHEN porcentaje_logros >= 25 THEN 'Roosevelt Elk'
            ELSE 'Moose'
        END AS rango_actual,

        CASE
            WHEN porcentaje_logros < 25 THEN 'Roosevelt Elk'
            WHEN porcentaje_logros < 50 THEN 'Black Bear'
            WHEN porcentaje_logros < 75 THEN 'Red Fox'
            WHEN porcentaje_logros < 90 THEN 'Turkey'
            ELSE NULL
        END AS proximo_rango,

        CASE
            WHEN porcentaje_logros < 25 THEN 25
            WHEN porcentaje_logros < 50 THEN 50
            WHEN porcentaje_logros < 75 THEN 75
            WHEN porcentaje_logros < 90 THEN 90
            ELSE NULL
        END AS porcentaje_necesario_proximo_rango
    FROM rank_status
)
SELECT
    rango_actual,
    proximo_rango,
    logros_conseguidos::bigint AS logros_conseguidos,
    logros_totales::bigint AS logros_totales,
    ROUND(porcentaje_logros, 2) AS porcentaje_logros,
    porcentaje_necesario_proximo_rango,
    CASE
        WHEN proximo_rango IS NULL THEN 0
        ELSE GREATEST(
            CEIL(logros_totales * porcentaje_necesario_proximo_rango / 100.0)::bigint
            - logros_conseguidos::bigint,
            0
        )
    END AS logros_faltantes
FROM rank_calc;


CREATE OR REPLACE VIEW api.v_rangos_cazador AS
    WITH total_logros AS (
    SELECT COUNT(t.scalar_value)::numeric AS total
    FROM api.query_catalog_achievements c
    JOIN api.query_catalog_achievements_triggers t
      ON t.parent_record_id = c.record_id
)
SELECT
    rango AS "Rango",
    porcentaje AS "% Logros",
    CEIL(total * porcentaje / 100.0)::bigint AS "Nº Logros"
FROM total_logros
CROSS JOIN (
    VALUES
        ('Moose', 5),
        ('Roosevelt Elk', 25),
        ('Black Bear', 50),
        ('Red Fox', 75),
        ('Turkey', 90)
) AS r(rango, porcentaje)
ORDER BY porcentaje;
