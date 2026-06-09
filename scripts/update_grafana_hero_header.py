"""Replace the main THC Grafana header with a richer HTML hero."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


GRAFANA_URL = "http://127.0.0.1:3001"
AUTH_HEADER = "Basic YWRtaW46YWRtaW4="
DASHBOARD_UID = "76b66a2d-ef24-4135-8b5c-9d6e9c9ad39e"
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "evidencias"


LOGO_HTML = """
<div style="height:calc(100% - 8px);margin:4px;box-sizing:border-box;position:relative;overflow:hidden;border-radius:10px;border:1px solid rgba(123,190,103,.40);background:radial-gradient(circle at 20% 15%,rgba(115,191,105,.28),transparent 34%),linear-gradient(135deg,#08110b 0%,#101816 54%,#050806 100%);box-shadow:inset 0 0 0 1px rgba(255,255,255,.04),0 0 22px rgba(115,191,105,.12);">
  <div style="position:absolute;left:-34px;top:-46px;width:112px;height:112px;border-radius:999px;background:rgba(255,120,10,.20);filter:blur(2px);"></div>
  <div style="position:absolute;right:-30px;bottom:-42px;width:130px;height:130px;border-radius:999px;background:rgba(115,191,105,.16);"></div>
  <div style="height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:8px 6px;position:relative;overflow:hidden;">
    <div style="font-size:10px;font-weight:900;color:#f4fff2;line-height:.9;letter-spacing:.2px;">the</div>
    <div style="font-size:20px;font-weight:950;color:#ff780a;line-height:.95;text-shadow:0 0 12px rgba(255,120,10,.28);">Hunter</div>
    <div style="font-size:8px;font-weight:900;color:#f4fff2;letter-spacing:2px;line-height:1;margin-top:2px;">CLASSIC</div>
    <div style="margin-top:6px;padding:3px 6px;border-radius:999px;border:1px solid rgba(255,120,10,.46);background:rgba(255,120,10,.11);color:#ffb46e;font-size:8px;font-weight:900;letter-spacing:.5px;line-height:1;white-space:nowrap;">THC</div>
    <div style="font-size:7px;color:#b9c7bc;margin-top:4px;line-height:1;white-space:nowrap;">COMMAND</div>
  </div>
</div>
"""


PROFILE_HTML = """
<div style="height:calc(100% - 8px);margin:4px;box-sizing:border-box;position:relative;overflow:hidden;border-radius:10px;border:1px solid rgba(122,184,95,.45);background:linear-gradient(135deg,#0b1510 0%,#111c17 42%,#070b09 100%);box-shadow:inset 0 0 0 1px rgba(255,255,255,.045),0 0 32px rgba(115,191,105,.10);color:#edf8ea;">
  <div style="position:absolute;inset:0;background:linear-gradient(90deg,rgba(255,120,10,.10),transparent 28%,rgba(115,191,105,.12));"></div>
  <div style="position:absolute;left:0;top:0;height:3px;width:100%;background:linear-gradient(90deg,#ff780a,#f2cc0c,#73bf69);"></div>
  <div style="position:absolute;right:10px;top:9px;font-size:7px;font-weight:900;letter-spacing:1px;color:#8fa497;text-transform:uppercase;">Perfil activo</div>
  <div style="height:100%;display:flex;align-items:center;gap:8px;padding:9px 10px 8px 10px;position:relative;overflow:hidden;">
    <div style="position:relative;flex:0 0 auto;width:62px;height:62px;">
      <div style="position:absolute;inset:-4px;border-radius:999px;background:conic-gradient(from 180deg,#73bf69,#f2cc0c,#ff780a,#73bf69);filter:drop-shadow(0 0 16px rgba(115,191,105,.45));"></div>
      <img src="https://avatar.thehunter.com/uploads/thumb/242x242/29509787.jpg?8248d314576f5f1e6ef82590be099031e1c6382e" style="position:absolute;inset:2px;width:58px;height:58px;border-radius:50%;object-fit:cover;border:2px solid #101813;" />
    </div>
    <div style="height:64px;width:42px;display:flex;align-items:center;justify-content:center;border-radius:8px;background:linear-gradient(180deg,rgba(255,255,255,.10),rgba(255,255,255,.035));border:1px solid rgba(255,255,255,.12);box-shadow:0 10px 24px rgba(0,0,0,.28);flex:0 0 auto;">
      <img src="https://static.wikia.nocookie.net/thehuntergame/images/b/b6/Achievement_badge_4.png/revision/latest?cb=20170326180505" style="height:58px;width:38px;display:block;object-fit:contain;filter:drop-shadow(0 8px 12px rgba(0,0,0,.45));" />
    </div>
    <div style="min-width:0;display:flex;flex-direction:column;justify-content:center;overflow:hidden;">
      <div style="font-size:22px;font-weight:950;line-height:1;white-space:nowrap;color:#ffffff;text-shadow:0 0 16px rgba(115,191,105,.34);">Nefastix13</div>
      <div style="margin-top:7px;font-size:11px;color:#b7ddc7;white-space:nowrap;">Miembro desde 20/03/2021</div>
      <div style="margin-top:8px;display:flex;gap:5px;flex-wrap:wrap;max-height:22px;overflow:hidden;">
        <span style="padding:3px 7px;border-radius:999px;background:rgba(115,191,105,.13);border:1px solid rgba(115,191,105,.35);color:#b8f2aa;font-size:8px;font-weight:800;letter-spacing:.4px;white-space:nowrap;">CAZADOR</span>
        <span style="padding:3px 7px;border-radius:999px;background:rgba(255,120,10,.12);border:1px solid rgba(255,120,10,.34);color:#ffc18a;font-size:8px;font-weight:800;letter-spacing:.4px;white-space:nowrap;">CLASSIC</span>
      </div>
    </div>
  </div>
</div>
"""


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


def main() -> None:
    EVIDENCE_DIR.mkdir(exist_ok=True)
    current = request_json(f"/api/dashboards/uid/{DASHBOARD_UID}")
    dashboard = current["dashboard"]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = EVIDENCE_DIR / f"grafana_header_before_{timestamp}.json"
    backup_path.write_text(json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8")

    for panel in dashboard["panels"]:
        if panel.get("id") == 1 and panel.get("type") == "text":
            panel["options"]["content"] = LOGO_HTML
            panel["gridPos"] = {"h": 4, "w": 2, "x": 0, "y": 1}
        if panel.get("id") == 22 and panel.get("type") == "text":
            panel["options"]["content"] = PROFILE_HTML
            panel["gridPos"] = {"h": 4, "w": 8, "x": 2, "y": 1}

    result = request_json(
        "/api/dashboards/db",
        method="POST",
        payload={"dashboard": dashboard, "overwrite": True, "message": "Mejorar cabecera visual THC"},
    )

    print(json.dumps({"backup": str(backup_path), "result": result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
