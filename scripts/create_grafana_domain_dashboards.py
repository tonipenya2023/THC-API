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
            ("Expediciones", "SELECT * FROM api.vw_grafana_expeditions ORDER BY start_at DESC NULLS LAST LIMIT 100;"),
            ("Abates por expedición", "SELECT * FROM api.vw_grafana_expedition_kills ORDER BY confirm_at DESC NULLS LAST LIMIT 200;"),
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


def build_dashboard(template: dict, spec: dict) -> dict:
    dashboard = copy.deepcopy(template)
    dashboard["id"] = None
    dashboard["uid"] = spec["uid"]
    dashboard["title"] = spec["title"]
    dashboard["version"] = 0
    dashboard["editable"] = True

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
