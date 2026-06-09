"""Basic local frontend for the reusable theHunter Classic API client."""

from __future__ import annotations

import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from .thc_client import ThcApiError, call_function_with_requests, list_functions
from .thc_dashboard import DashboardEncoder, get_dashboard_data


HOST = "127.0.0.1"
PORT = int(os.environ.get("THC_API_PORT", "8080"))
BASE_DIR = Path(__file__).resolve().parents[1]
INDEX_HTML_PATH = BASE_DIR / "assets" / "index.html"
GRAFANA_HTML_PATH = BASE_DIR / "assets" / "grafana_dashboard.html"
GRAFANA_DASHBOARD_PATH = BASE_DIR / "docs" / "grafana_dashboard_thc_hunter_v2.json"


def load_index_html() -> str:
    return INDEX_HTML_PATH.read_text(encoding="utf-8")


def load_grafana_html() -> str:
    dashboard_url = os.environ.get("GRAFANA_DASHBOARD_URL", "").strip()
    grafana_url = os.environ.get("GRAFANA_URL", "http://127.0.0.1:3001").strip()
    return (
        GRAFANA_HTML_PATH.read_text(encoding="utf-8")
        .replace("__GRAFANA_DASHBOARD_URL__", dashboard_url)
        .replace("__GRAFANA_URL__", grafana_url.rstrip("/"))
    )


def load_grafana_dashboard_json() -> str:
    return GRAFANA_DASHBOARD_PATH.read_text(encoding="utf-8")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format_string: str, *args: Any) -> None:
        print(f"[HTTP] {self.command} {urlparse(self.path).path}")

    def _send_json(self, payload: Any, status: int = 200, cls: Any = None) -> None:
        data = json.dumps(payload, ensure_ascii=True, cls=cls).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_html(self, html: str, status: int = 200) -> None:
        data = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_raw_json(self, payload: str, status: int = 200) -> None:
        data = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, path: Path) -> None:
        resolved = path.resolve()
        assets_root = (BASE_DIR / "assets").resolve()
        if not resolved.is_file() or assets_root not in resolved.parents:
            self._send_json({"error": "Not found"}, 404)
            return
        data = resolved.read_bytes()
        content_type = mimetypes.guess_type(str(resolved))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._send_html(load_grafana_html())
        elif path == "/api-explorer":
            self._send_html(load_index_html())
        elif path.startswith("/assets/"):
            self._send_file(BASE_DIR / path.lstrip("/"))
        elif path == "/grafana-dashboard.json":
            self._send_raw_json(load_grafana_dashboard_json())
        elif path == "/health":
            self._send_json({"status": "up"})
        elif path == "/api/functions":
            self._send_json(list_functions())
        elif path == "/api/dashboard_data":
            self._send_json(get_dashboard_data(), cls=DashboardEncoder)
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/call":
            self._send_json({"error": "Not found"}, 404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            result = call_function_with_requests(
                body.get("name", ""),
                body.get("params", {}),
                enrich_ids=bool(body.get("enrich_ids", False)),
            )
            self._send_json({**result, "elapsed_ms": 0})
        except (ValueError, json.JSONDecodeError) as exc:
            self._send_json({"error": f"Invalid request: {exc}"}, 400)
        except ThcApiError as exc:
            self._send_json({"error": str(exc)}, 502)
        except Exception as exc:
            self._send_json({"error": f"Unexpected server error: {exc}"}, 500)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"THC API Explorer listening on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

