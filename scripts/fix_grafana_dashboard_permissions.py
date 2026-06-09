"""Apply TEST dashboard Viewer/Editor permissions to THC Grafana dashboards."""

from __future__ import annotations

import json
import urllib.error
import urllib.request


GRAFANA_URL = "http://127.0.0.1:3001"
AUTH_HEADER = "Basic YWRtaW46YWRtaW4="
DASHBOARD_UIDS = [
    "thc-home",
    "thc-competiciones",
    "thc-estadisticas",
    "thc-expediciones",
    "thc-galeria-fotos",
    "thc-mejores-marcas",
    "thc-trofeos",
    "thc-tablas-clasificacion",
]


def request_json(path: str, method: str = "GET", payload: dict | None = None) -> dict | list:
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
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed with HTTP {exc.code}: {body}") from exc


def main() -> None:
    results = []
    payload = {
        "items": [
            {"role": "Editor", "permission": 2},
            {"role": "Viewer", "permission": 1},
        ]
    }
    for uid in DASHBOARD_UIDS:
        dashboard = request_json(f"/api/dashboards/uid/{uid}")["dashboard"]
        dashboard_id = dashboard["id"]
        request_json(f"/api/dashboards/id/{dashboard_id}/permissions", method="POST", payload=payload)
        permissions = request_json(f"/api/dashboards/uid/{uid}/permissions")
        results.append(
            {
                "uid": uid,
                "id": dashboard_id,
                "title": dashboard["title"],
                "permissions": [
                    {
                        "role": item.get("role"),
                        "permission": item.get("permission"),
                        "permissionName": item.get("permissionName"),
                    }
                    for item in permissions
                    if item.get("role") in {"Viewer", "Editor"}
                ],
            }
        )
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
