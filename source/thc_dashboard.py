"""Dashboard data access for the local THC frontend."""

from __future__ import annotations

import datetime
import decimal
import json
import os
from typing import Any

import psycopg2
import psycopg2.extras


ITEM_IMAGE_BASE_URL = "https://static.thehunter.com/static/img/items/256"
ACHIEVEMENT_ICON_BASE_URL = "https://static.thehunter.com/static/img/achievements"


class DashboardEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)


def _table_columns(cursor: Any, table_name: str) -> set[str]:
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'api'
          AND table_name = %s
        """,
        (table_name,),
    )
    return {row["column_name"] for row in cursor.fetchall()}


def _item_image_url_sql(alias: str) -> str:
    return (
        f"CASE WHEN NULLIF({alias}.field_image, '') IS NOT NULL "
        f"THEN '{ITEM_IMAGE_BASE_URL}/' || btrim({alias}.field_image, '/') || '.png' END"
    )


def _achievement_icon_url_sql(alias: str) -> str:
    return (
        f"CASE WHEN NULLIF({alias}.field_icon_url, '') IS NOT NULL "
        f"THEN '{ACHIEVEMENT_ICON_BASE_URL}/' || btrim({alias}.field_icon_url, '/') END"
    )


def get_dashboard_data() -> dict[str, Any]:
    try:
        conn = psycopg2.connect(
            host=os.environ.get("THC_DB_HOST", "127.0.0.1"),
            port=int(os.environ.get("THC_DB_PORT", "5432")),
            dbname=os.environ.get("THC_DB_NAME", "thc_api"),
            user=os.environ.get("THC_DB_USER", "postgres"),
            password="system"
        )
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        item_columns = _table_columns(cursor, "query_catalog_items")
        achievement_columns = _table_columns(cursor, "query_catalog_achievements")
        has_item_image = "field_image" in item_columns
        has_achievement_icon = "field_icon_url" in achievement_columns
        
        cursor.execute("SELECT * FROM api.vw_hunter_overview")
        overview = dict(cursor.fetchone() or {})
        
        cursor.execute("SELECT * FROM api.vw_expedition_weekly ORDER BY week_start")
        expeditions_weekly = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM api.vw_reserve_performance ORDER BY kills DESC")
        reserves = [dict(row) for row in cursor.fetchall()]
        
        if has_item_image:
            cursor.execute(f"""
                SELECT
                    w.*,
                    {_item_image_url_sql("ci")} AS weapon_image_url
                FROM api.vw_weapon_analytics w
                LEFT JOIN api.query_catalog_items ci ON api.safe_bigint(ci.field_id) = w.weapon_id
                ORDER BY w.kills DESC
            """)
        else:
            cursor.execute("SELECT * FROM api.vw_weapon_analytics ORDER BY kills DESC")
        weapons = [dict(row) for row in cursor.fetchall()]
        
        
        cursor.execute("SELECT * FROM api.vw_species_analytics ORDER BY kills DESC")
        species = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM api.vw_personal_records ORDER BY score DESC NULLS LAST")
        records = [dict(row) for row in cursor.fetchall()]

        cursor.execute("""
            SELECT 
                api.safe_timestamptz(e.field_start_ts) AS start_ts, 
                e.field_reserve, 
                COALESCE(NULLIF(r.field_name, ''), e.field_reserve, 'Desconocida') AS reserve_name,
                e.field_kills, 
                EXTRACT(EPOCH FROM (api.safe_timestamptz(e.field_end_ts) - api.safe_timestamptz(field_start_ts))) AS duration_seconds,
                api.safe_numeric(d.field_stats_field_distance) AS distance,
                COALESCE(SUM(api.safe_bigint(a.field_spots)), 0) AS spots,
                COALESCE(SUM(api.safe_bigint(a.field_tracks)), 0) AS tracks
            FROM api.query_statistics_history_expeditions e
            LEFT JOIN api.query_catalog_reserves r ON r.field_id = e.field_reserve
            LEFT JOIN api.query_statistics_expeditions_details d ON d.field_expedition_field_id = e.field_id
            LEFT JOIN api.query_statistics_expeditions_details_animal a ON a.parent_record_id = d.record_id
            GROUP BY e.field_id, e.field_start_ts, e.field_reserve, r.field_name, e.field_kills, e.field_end_ts, d.field_stats_field_distance
            ORDER BY api.safe_timestamptz(e.field_start_ts) DESC
        """)
        recent_expeditions = [dict(row) for row in cursor.fetchall()]
        
        # New queries for leaderboards and recent records
        cursor.execute("SELECT COUNT(*) FROM api.vw_leaderboard_top100 WHERE rank_no = 1 AND lower(handle) = 'nefastix13'")
        top1_count = cursor.fetchone()['count'] or 0
        
        cursor.execute("SELECT COUNT(*) FROM api.vw_leaderboard_top100 WHERE lower(handle) = 'nefastix13'")
        top100_count = cursor.fetchone()['count'] or 0

        if has_item_image:
            cursor.execute(f"""
                SELECT
                    pr.species_name,
                    pr.record_type,
                    pr.score,
                    pr.distance,
                    pr.confirm_at,
                    pr.weapon_name,
                    {_item_image_url_sql("ci")} AS weapon_image_url
                FROM api.vw_personal_records pr
                LEFT JOIN api.query_catalog_items ci ON api.safe_bigint(ci.field_id) = pr.weapon_id
                ORDER BY pr.confirm_at DESC
            """)
        else:
            cursor.execute("""
                SELECT species_name, record_type, score, distance, confirm_at, weapon_name
                FROM api.vw_personal_records
                ORDER BY confirm_at DESC
            """)
        recent_records = [dict(row) for row in cursor.fetchall()]
        
        # 8 KPIs queries for the footer
        cursor.execute("SELECT COUNT(DISTINCT item_key) FROM api.query_statistics_lifetime_animal WHERE api.safe_bigint(field_kills) > 0")
        kpi_species_kills = cursor.fetchone()['count'] or 0
        cursor.execute("SELECT COUNT(*) FROM api.query_catalog_species")
        kpi_species_total = cursor.fetchone()['count'] or 0

        cursor.execute("SELECT COUNT(DISTINCT weapon_id) FROM api.query_statistics_lifetime_weapon_stats WHERE kills > 0")
        kpi_weapons_kills = cursor.fetchone()['count'] or 0
        cursor.execute("SELECT COUNT(*) FROM api.query_catalog_items WHERE field_type IN ('1', '22')")
        kpi_weapons_total = cursor.fetchone()['count'] or 0

        cursor.execute("SELECT COUNT(*) FROM api.query_statistics_history_expeditions")
        kpi_expeditions = cursor.fetchone()['count'] or 0

        cursor.execute("SELECT COUNT(DISTINCT date_trunc('day', api.safe_timestamptz(field_start_ts))) FROM api.query_statistics_history_expeditions")
        kpi_days = cursor.fetchone()['count'] or 0

        cursor.execute("""
            SELECT 
                COUNT(t.scalar_value) AS total,
                SUM(CASE WHEN g.field_value IS NOT NULL AND g.field_value::numeric >= t.scalar_value::numeric THEN 1 ELSE 0 END) AS completed
            FROM api.query_catalog_achievements c
            JOIN api.query_catalog_achievements_triggers t ON t.parent_record_id = c.record_id
            LEFT JOIN api.query_achievements_general g ON g.field_id = c.field_id AND g.field_category_id = c.field_category
        """)
        ach_res = cursor.fetchone()
        kpi_achievements_completed = ach_res['completed'] or 0
        kpi_achievements_total = ach_res['total'] or 0
        achievement_badge = {}
        if has_achievement_icon:
            cursor.execute(f"""
                SELECT
                    c.field_title AS title,
                    {_achievement_icon_url_sql("c")} AS icon_url
                FROM api.query_catalog_achievements c
                JOIN api.query_catalog_achievements_triggers t ON t.parent_record_id = c.record_id
                LEFT JOIN api.query_achievements_general g ON g.field_id = c.field_id AND g.field_category_id = c.field_category
                WHERE NULLIF(c.field_icon_url, '') IS NOT NULL
                  AND g.field_value IS NOT NULL
                  AND api.safe_numeric(g.field_value) >= api.safe_numeric(t.scalar_value)
                ORDER BY api.safe_bigint(c.field_id) DESC NULLS LAST
                LIMIT 1
            """)
            achievement_badge = dict(cursor.fetchone() or {})
            if not achievement_badge:
                cursor.execute(f"""
                    SELECT
                        c.field_title AS title,
                        {_achievement_icon_url_sql("c")} AS icon_url
                    FROM api.query_catalog_achievements c
                    WHERE NULLIF(c.field_icon_url, '') IS NOT NULL
                    ORDER BY api.safe_bigint(c.field_id) DESC NULLS LAST
                    LIMIT 1
                """)
                achievement_badge = dict(cursor.fetchone() or {})

        cursor.execute("SELECT COUNT(*) FROM api.query_achievements_daily_missions")
        kpi_daily_missions = cursor.fetchone()['count'] or 0

        cursor.execute("SELECT COUNT(*) FROM api.query_competitions_info_prizes")
        kpi_events_won = cursor.fetchone()['count'] or 0

        cursor.execute("SELECT COALESCE(SUM(api.safe_bigint(field_total)), 0) FROM api.query_trophies")
        kpi_trophies = cursor.fetchone()['coalesce'] or 0

        last_expedition_animals = []
        last_hunt_details = {"capturas": 0, "marcados": 0, "seguidos": 0, "distance": 0, "duration": 0}
        try:
            cursor.execute("SELECT api.safe_numeric(field_stats_field_distance) AS distance, api.safe_numeric(field_stats_field_duration) AS duration FROM api.query_statistics_last_hunt")
            row = cursor.fetchone()
            if row:
                last_hunt_details["distance"] = float(row["distance"] or 0)
                last_hunt_details["duration"] = int(float(row["duration"] or 0))
                
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'api' AND table_name = 'query_statistics_last_hunt_animal'")
            cols = {r["column_name"] for r in cursor.fetchall()}
            
            select_parts = []
            if 'field_kills' in cols:
                select_parts.append("SUM(api.safe_bigint(field_kills)) AS kills")
            else:
                select_parts.append("0 AS kills")
                
            if 'field_spots' in cols:
                select_parts.append("SUM(api.safe_bigint(field_spots)) AS spots")
            else:
                select_parts.append("0 AS spots")
                
            if 'field_tracks' in cols:
                select_parts.append("SUM(api.safe_bigint(field_tracks)) AS tracks")
            else:
                select_parts.append("0 AS tracks")
                
            query = f"SELECT {', '.join(select_parts)} FROM api.query_statistics_last_hunt_animal"
            cursor.execute(query)
            row_animal = cursor.fetchone()
            if row_animal:
                last_hunt_details["capturas"] = int(row_animal["kills"] or 0)
                last_hunt_details["marcados"] = int(row_animal["spots"] or 0)
                last_hunt_details["seguidos"] = int(row_animal["tracks"] or 0)
                
            cursor.execute("""
                SELECT 
                    a.item_key AS species_id,
                    COALESCE(s.field_name, 'Especie ' || a.item_key) AS name,
                    api.safe_bigint(a.field_kills) AS count
                FROM api.query_statistics_last_hunt_animal a
                LEFT JOIN api.query_catalog_species s ON api.safe_bigint(s.field_id) = api.safe_bigint(a.item_key)
                WHERE api.safe_bigint(a.field_kills) > 0
            """)
            last_expedition_animals = [dict(row) for row in cursor.fetchall()]
        except Exception:
            conn.rollback()
        
        cursor.close()
        conn.close()
        
        return {
            "overview": overview,
            "expeditions_weekly": expeditions_weekly,
            "reserves": reserves,
            "weapons": weapons,
            "species": species,
            "records": records,
            "recent_expeditions": recent_expeditions,
            "top1_count": top1_count,
            "top100_count": top100_count,
            "recent_records": recent_records,
            "achievement_badge": achievement_badge,
            "last_expedition_animals": last_expedition_animals,
            "last_hunt_details": last_hunt_details,
            "kpis": {
                "species_kills": kpi_species_kills,
                "species_total": kpi_species_total,
                "weapons_kills": kpi_weapons_kills,
                "weapons_total": kpi_weapons_total,
                "expeditions": kpi_expeditions,
                "days": kpi_days,
                "achievements_completed": kpi_achievements_completed,
                "achievements_total": kpi_achievements_total,
                "daily_missions": kpi_daily_missions,
                "events_won": kpi_events_won,
                "trophies": kpi_trophies
            }
        }
    except Exception as e:
        print("Error fetching dashboard data:", e)
        return {}
