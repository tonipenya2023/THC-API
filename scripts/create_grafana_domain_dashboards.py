"""Create THC domain dashboards in Grafana by cloning the TEST dashboard style."""

from __future__ import annotations

import copy
import json
import re
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


GRAFANA_URL = "http://127.0.0.1:3001"
TEST_UID = "adv42n7"
AUTH_HEADER = "Basic YWRtaW46c3lzdGVt"
DATASOURCE = {"type": "grafana-postgresql-datasource", "uid": "afodoaxjtubr4e"}
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "evidencias"
COMPETITION_LINK = {
    "title": "Abrir competicion",
    "url": "https://www.thehunter.com/#competitions/details/${__value.raw}",
    "targetBlank": True,
}
PHOTO_LINK = {
    "title": "Abrir foto",
    "url": "${__value.raw}",
    "targetBlank": True,
}
EXPEDITION_KILL_ICON_SQL = """CASE
    WHEN gender = '1' AND species_name = 'Alpine Ibex' THEN 'https://static.wikia.nocookie.net/thehunter/images/e/e8/Alpine_ibex_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021810&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Axis Deer' THEN 'https://static.wikia.nocookie.net/thehunter/images/e/ec/Axis_deer_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021809&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Banteng' THEN 'https://static.wikia.nocookie.net/thehunter/images/a/a3/Banteng_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021810&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Bighorn Sheep' THEN 'https://static.wikia.nocookie.net/thehunter/images/7/7c/Bighorn_sheep_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021810&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Blacktail Deer' THEN 'https://static.wikia.nocookie.net/thehunter/images/4/43/Blacktail_deer_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021810&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Dall Sheep' THEN 'https://static.wikia.nocookie.net/thehunter/images/9/92/Dall_sheep_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021811&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Fallow Deer' THEN 'https://static.wikia.nocookie.net/thehunter/images/5/5b/Fallow_deer_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021810&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Feral Hog' THEN 'https://static.wikia.nocookie.net/thehunter/images/6/6b/Feral_hog_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021812&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Moose' THEN 'https://static.wikia.nocookie.net/thehunter/images/1/19/Moose_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021813&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Mule Deer' THEN 'https://static.wikia.nocookie.net/thehunter/images/c/c0/Mule_deer_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021813&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Pheasant' THEN 'https://static.wikia.nocookie.net/thehunter/images/6/65/Pheasant_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021813&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Puma' THEN 'https://static.wikia.nocookie.net/thehunter/images/1/12/Puma_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021814&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Red Deer' THEN 'https://static.wikia.nocookie.net/thehunter/images/6/69/Red_deer_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021814&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Red Kangaroo' THEN 'https://static.wikia.nocookie.net/thehunter/images/d/d7/Red_kangaroo_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021814&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Rock Ptarmigan' THEN 'https://static.wikia.nocookie.net/thehunter/images/c/cf/Rock_ptarmigan_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021814&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Rocky Mountain Elk' THEN 'https://static.wikia.nocookie.net/thehunter/images/4/47/Rocky_mountain_elk_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021814&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Roe Deer' THEN 'https://static.wikia.nocookie.net/thehunter/images/4/48/Roe_deer_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021814&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Roosevelt Elk' THEN 'https://static.wikia.nocookie.net/thehunter/images/8/86/Roosevelt_elk_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021815&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Sitka Deer' THEN 'https://static.wikia.nocookie.net/thehunter/images/f/f0/Sitka_deer_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021813&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Turkey' THEN 'https://static.wikia.nocookie.net/thehunter/images/f/fa/Turkey_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021816&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Water Buffalo' THEN 'https://static.wikia.nocookie.net/thehunter/images/3/3c/Water_buffalo_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021817&path-prefix=es'
    WHEN gender = '1' AND species_name = 'White-tailed Ptarmigan' THEN 'https://static.wikia.nocookie.net/thehunter/images/d/de/White-tailed_ptarmigan_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021817&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Whitetail Deer' THEN 'https://static.wikia.nocookie.net/thehunter/images/2/2d/Whitetail_deer_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021815&path-prefix=es'
    WHEN gender = '1' AND species_name = 'Wood Grouse' THEN 'https://static.wikia.nocookie.net/thehunter/images/e/e6/Wood_grouse_female_common.png/revision/latest/scale-to-width-down/60?cb=20240427021817&path-prefix=es'
    ELSE animal_icon_url
END"""


DASHBOARDS = [
    {
        "uid": "thc-home",
        "title": "THC - Home",
        "panels": [
            ("Resumen del cazador", "SELECT * FROM api.vw_grafana_statistics_summary LIMIT 50;"),
            ("Últimas mejores marcas", "SELECT * FROM api.vw_grafana_personal_best ORDER BY confirm_at DESC NULLS LAST LIMIT 50;"),
            ("Podios recientes", "SELECT * FROM api.vw_grafana_classification_tables WHERE rank_no < 4 ORDER BY leaderboard_type, species_name, rank_no LIMIT 100;"),
        ],
    },
    {
        "uid": "thc-competiciones",
        "title": "THC - Competiciones",
        "panels": [
            ("Competiciones", "SELECT * FROM api.vw_grafana_competitions ORDER BY start_at DESC NULLS LAST LIMIT 100;"),
            ("Participantes", "SELECT * FROM api.vw_grafana_competition_entrants ORDER BY competition_id DESC NULLS LAST, position_no LIMIT 200;"),
        ],
    },
    {
        "uid": "thc-estadisticas",
        "title": "THC - Estadísticas",
        "panels": [
            ("Resumen", "SELECT * FROM api.vw_grafana_statistics_summary LIMIT 50;"),
            ("Por especie", "SELECT * FROM api.vw_grafana_statistics_species ORDER BY kills DESC NULLS LAST LIMIT 100;"),
            ("Por arma", "SELECT * FROM api.vw_grafana_statistics_weapons ORDER BY kills DESC NULLS LAST LIMIT 100;"),
        ],
    },
    {
        "uid": "thc-expediciones",
        "title": "THC - Expediciones",
        "panels": [
            ("Resumen expediciones", "SELECT expedition_id AS \"Expedicion\", start_at AS \"Inicio\", end_at AS \"Fin\", hours AS \"Horas\", reserve_name AS \"Reserva\", kills AS \"Muertes\", collectables AS \"Coleccionables\", CASE WHEN singleplayer THEN '✓' ELSE '✕' END AS \"Solo\" FROM api.vw_grafana_expeditions ORDER BY start_at DESC NULLS LAST LIMIT 100;"),
            ("Muertes con contexto de expedicion", f"SELECT expedition_id AS \"expedition id\", reserve_name AS \"Reserva\", start_at AS \"Inicio\", hours AS \"Horas exp.\", kills AS \"Muertes exp.\", animal_id AS \"animal id\", animal_profile_url AS \"Ficha animal\", {EXPEDITION_KILL_ICON_SQL} AS \"Icono\", species_name AS \"Especie\", CASE WHEN gender = '0' THEN '♂' WHEN gender = '1' THEN '♀' ELSE gender END AS \"Genero\", CASE WHEN ethical THEN '✓' ELSE '✕' END AS \"Etico\", score AS \"Puntuacion\", score_type AS \"Tipo score\", weight / 1000 AS \"Peso Kg\", photo_url AS \"Foto\", confirm_at AS \"Muerte\" FROM api.vw_grafana_expedition_kills_full WHERE animal_id IS NOT NULL ORDER BY confirm_at DESC NULLS LAST, start_at DESC NULLS LAST LIMIT 500;"),
        ],
    },
    {
        "uid": "thc-galeria-fotos",
        "title": "THC - Galería de Fotos",
        "panels": [
            ("Fotos", "SELECT * FROM api.vw_grafana_gallery_photos ORDER BY photo_id DESC NULLS LAST LIMIT 100;"),
        ],
    },
    {
        "uid": "thc-mejores-marcas",
        "title": "THC - Mejores Marcas",
        "panels": [
            ("Mejores marcas", "SELECT * FROM api.vw_grafana_personal_best ORDER BY species_name, record_type, score DESC NULLS LAST LIMIT 200;"),
        ],
    },
    {
        "uid": "thc-trofeos",
        "title": "THC - Trofeos",
        "panels": [
            ("Trofeos", "SELECT * FROM api.vw_grafana_trophies ORDER BY awarded_at DESC NULLS LAST LIMIT 200;"),
        ],
    },
    {
        "uid": "thc-tablas-clasificacion",
        "title": "THC - Tablas de Clasificación",
        "panels": [
            ("Clasificación por distancia", "SELECT * FROM api.vw_grafana_classification_tables WHERE leaderboard_type = 'range' ORDER BY species_name, rank_no LIMIT 200;"),
            ("Clasificación por puntuación", "SELECT * FROM api.vw_grafana_classification_tables WHERE leaderboard_type = 'score' ORDER BY species_name, rank_no LIMIT 200;"),
        ],
    },
]


def request_json(path: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{GRAFANA_URL}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": AUTH_HEADER,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed with HTTP {exc.code}: {body}") from exc


def slugify(title: str) -> str:
    text = title.lower()
    replacements = str.maketrans("áéíóúñ", "aeioun")
    text = text.translate(replacements)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def base_panel(template: dict, panel_id: int, title: str, raw_sql: str, x: int, y: int, w: int) -> dict:
    panel = copy.deepcopy(template)
    panel["id"] = panel_id
    panel["title"] = title
    panel["gridPos"] = {"h": 8, "w": w, "x": x, "y": y}
    panel["datasource"] = DATASOURCE
    panel["targets"][0]["datasource"] = DATASOURCE
    panel["targets"][0]["rawSql"] = raw_sql
    panel["targets"][0]["rawQuery"] = True
    panel["targets"][0]["format"] = "table"
    panel["targets"][0]["editorMode"] = "code"
    panel["targets"][0]["dataset"] = "thc_api"
    return panel


def add_competition_id_link(panel: dict) -> None:
    if panel.get("type") != "table":
        return

    overrides = panel.setdefault("fieldConfig", {}).setdefault("overrides", [])
    competition_override = None
    for override in overrides:
        matcher = override.get("matcher", {})
        if matcher.get("id") == "byName" and matcher.get("options") == "competition_id":
            competition_override = override
            break

    if competition_override is None:
        competition_override = {
            "matcher": {"id": "byName", "options": "competition_id"},
            "properties": [],
        }
        overrides.append(competition_override)

    properties = competition_override.setdefault("properties", [])
    properties[:] = [item for item in properties if item.get("id") != "links"]
    properties.append({"id": "links", "value": [COMPETITION_LINK]})


def field_override(field_name: str, properties: list[dict]) -> dict:
    return {
        "matcher": {"id": "byName", "options": field_name},
        "properties": properties,
    }


def width(value: int) -> dict:
    return {"id": "custom.width", "value": value}


def align(value: str) -> dict:
    return {"id": "custom.align", "value": value}


def decimals(value: int) -> dict:
    return {"id": "decimals", "value": value}


def cell_options(value: dict) -> dict:
    return {"id": "custom.cellOptions", "value": value}


def links(value: list[dict]) -> dict:
    return {"id": "links", "value": value}


def hidden(value: bool = True) -> dict:
    return {"id": "custom.hidden", "value": value}


def configure_expedition_table(panel: dict, title: str) -> None:
    if panel.get("type") != "table":
        return

    if title == "Muertes con contexto de expedicion":
        panel["gridPos"] = {"h": 18, "w": 24, "x": 0, "y": 10}
        panel.setdefault("options", {})["showHeader"] = True
        panel.setdefault("fieldConfig", {})["overrides"] = [
            field_override("expedition id", [width(104), align("center")]),
            field_override("animal id", [width(108), align("center"), links([{"title": "Abrir ficha animal", "url": "${__data.fields[\"Ficha animal\"]}", "targetBlank": True}])]),
            field_override("Ficha animal", [hidden()]),
            field_override("Reserva", [width(150)]),
            field_override("Inicio", [width(159)]),
            field_override("Horas exp.", [width(90), decimals(2), align("right")]),
            field_override("Muertes exp.", [width(95), align("right")]),
            field_override("Icono", [width(62), cell_options({"type": "image"})]),
            field_override("Especie", [width(190)]),
            field_override("Genero", [width(78), align("center")]),
            field_override("Etico", [width(70), align("center")]),
            field_override("Puntuacion", [width(102), decimals(3), align("right"), cell_options({"type": "color-text"})]),
            field_override("Tipo score", [width(96), align("center")]),
            field_override("Peso Kg", [width(88), decimals(2), align("right")]),
            field_override("Foto", [width(82), cell_options({"type": "image"}), links([PHOTO_LINK])]),
            field_override("Muerte", [width(159)]),
        ]
    elif title == "Resumen expediciones":
        panel["gridPos"] = {"h": 8, "w": 24, "x": 0, "y": 1}
        panel.setdefault("options", {})["showHeader"] = True
        panel.setdefault("fieldConfig", {})["overrides"] = [
            field_override("Expedicion", [width(104), align("center")]),
            field_override("Inicio", [width(159)]),
            field_override("Fin", [width(159)]),
            field_override("Horas", [width(75), decimals(2), align("right")]),
            field_override("Reserva", [width(170)]),
            field_override("Muertes", [width(80), align("right")]),
            field_override("Coleccionables", [width(126), align("right")]),
            field_override("Solo", [width(62), align("center")]),
        ]


def build_dashboard(template: dict, spec: dict) -> dict:
    dashboard = copy.deepcopy(template)
    dashboard["id"] = None
    dashboard["uid"] = spec["uid"]
    dashboard["title"] = spec["title"]
    dashboard["version"] = 0
    dashboard["editable"] = True
    if spec["uid"] == "thc-expediciones":
        dashboard["templating"] = {"list": []}

    table_template = next(panel for panel in template["panels"] if panel.get("type") == "table")
    panels = [
        {
            "collapsed": False,
            "gridPos": {"h": 1, "w": 24, "x": 0, "y": 0},
            "id": 1,
            "panels": [],
            "title": spec["title"],
            "type": "row",
        }
    ]

    for index, (title, raw_sql) in enumerate(spec["panels"], start=1):
        columns = 1 if len(spec["panels"]) == 1 else 2
        w = 24 if columns == 1 else 12
        x = 0 if (index - 1) % columns == 0 else 12
        y = 1 + ((index - 1) // columns) * 8
        panel = base_panel(table_template, index + 1, title, raw_sql, x, y, w)
        if spec["uid"] == "thc-competiciones" and title == "Competiciones":
            add_competition_id_link(panel)
        if spec["uid"] == "thc-expediciones":
            configure_expedition_table(panel, title)
        panels.append(panel)

    dashboard["panels"] = panels
    return dashboard


def main() -> None:
    EVIDENCE_DIR.mkdir(exist_ok=True)
    source = request_json(f"/api/dashboards/uid/{TEST_UID}")["dashboard"]
    results = []

    for spec in DASHBOARDS:
        dashboard = build_dashboard(source, spec)
        result = request_json(
            "/api/dashboards/db",
            method="POST",
            payload={"dashboard": dashboard, "overwrite": True, "message": "Clone TEST as THC domain dashboard"},
        )
        results.append(
            {
                "title": spec["title"],
                "uid": spec["uid"],
                "url": f"{GRAFANA_URL}{result.get('url', f'/d/{spec['uid']}/{slugify(spec['title'])}')}",
                "status": result.get("status"),
                "version": result.get("version"),
            }
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    evidence_path = EVIDENCE_DIR / f"grafana_domain_dashboards_created_{timestamp}.json"
    evidence_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(evidence_path)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
