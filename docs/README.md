# THC_API

Proyecto local para consultar datos de theHunter Classic, exponerlos mediante una UI HTTP local y sincronizar catálogos/consultas hacia PostgreSQL para analítica.

## Estado documental

- Documentación actualizada por lectura estática del código fuente del ZIP `THC_API20260605 1639.zip`.
- Estado funcional del proyecto: `BLOQUEADA` hasta ejecutar pruebas reales en el entorno objetivo.
- Norma prevalente: `docs/AGENTS_NORMAS.MD`.

## Entorno objetivo definido por normas

- Ruta del proyecto: `C:\_MisProyectos\THC_API`
- Comando de arranque: `python thc_api.py`
- URL local esperada: `http://127.0.0.1:8080/`
- Evidencias: `C:\_MisProyectos\THC_API\evidencias`
- Registro de cambios: `C:\_MisProyectos\THC_API\docs\CAMBIOS.MD`

## Estructura real del proyecto

| Ruta | Uso real |
|---|---|
| `thc_api.py` | Lanzador raíz. Importa `main` desde `source.thc_api`. |
| `source/thc_api.py` | Servidor HTTP local basado en `ThreadingHTTPServer`. Sirve UI y endpoints JSON. |
| `source/thc_client.py` | Cliente reutilizable contra `https://api.thehunter.com` y `https://apiv2.thehunter.com`. |
| `source/thc_client_registry.py` | Registro de funciones expuestas a la UI y a `/api/call`. |
| `source/thc_db.py` | Persistencia de catálogos oficiales en PostgreSQL. |
| `source/thc_query_db.py` | Persistencia genérica de respuestas de funciones API en PostgreSQL. |
| `source/thc_catalog_loader.py` | Carga normalizada de catálogos en tablas relacionales. |
| `source/thc_dashboard.py` | Lectura de vistas/tablas PostgreSQL para `/api/dashboard_data`. |
| `scripts/sync_catalogs.py` | Sincroniza catálogos oficiales a PostgreSQL. |
| `scripts/sync_queries.py` | Sincroniza consultas API registradas a PostgreSQL. |
| `scripts/apply_views.py` | Aplica `sql/dashboard_views.sql`. |
| `scripts/create_metabase_dashboard.py` | Crea/actualiza dashboards y preguntas en Metabase. |
| `scripts/inspect_html.py` | Verifica por HTTP elementos concretos de la UI local. |
| `sql/schema.sql` | Esquema base `api`, tablas de catálogos y funciones SQL auxiliares. |
| `sql/dashboard_views.sql` | Vistas analíticas usadas por el dashboard local. |
| `sql/metabase_queries.sql` | Consultas SQL para Metabase. |
| `sql/hall_of_fame_schema.sql` | Esquema específico de Hall of Fame. |
| `sql/hall_of_fame_examples.sql` | Ejemplos SQL de Hall of Fame. |
| `sql/quick_validation.sql` | Consultas rápidas de validación SQL. |
| `assets/index.html` | UI principal servida en `/`. |
| `assets/dashboard_prototype.html` | Prototipo HTML del dashboard. |
| `tests/test_logo_urls.py` | Comprobación auxiliar de URLs de logos. |
| `tests/verify_logo.py` | Comprobación auxiliar de logo. |
| `run_sync.bat` | Flujo Windows para sincronización. |
| `docs/` | Documentación y normas. |
| `evidencias/` | Logs/evidencias generadas. |

No existe carpeta `examples/` en el ZIP revisado.

## Endpoints HTTP locales

| Método | Ruta | Implementación | Respuesta esperada |
|---|---|---|---|
| `GET` | `/` | `source.thc_api.Handler.do_GET` | HTML de `assets/index.html`. |
| `GET` | `/health` | `source.thc_api.Handler.do_GET` | JSON `{"status":"up"}`. |
| `GET` | `/api/functions` | `source.thc_api.Handler.do_GET` + `source.thc_client.list_functions` | Lista de funciones disponibles para la UI. |
| `GET` | `/api/dashboard_data` | `source.thc_api.Handler.do_GET` + `source.thc_dashboard.get_dashboard_data` | JSON con bloques analíticos desde PostgreSQL; devuelve `{}` si ocurre excepción. |
| `POST` | `/api/call` | `source.thc_api.Handler.do_POST` + `source.thc_client.call_function_with_requests` | JSON con `data`, `requests` y `elapsed_ms`. |

Cualquier otra ruta devuelve `404` con `{"error":"Not found"}`.

## Variables de entorno reales

| Variable | Uso |
|---|---|
| `THC_DB_HOST` | Host PostgreSQL. Default `127.0.0.1`. |
| `THC_DB_PORT` | Puerto PostgreSQL. Default `5432`. |
| `THC_DB_NAME` | Base de datos. Default `thc_api`. |
| `THC_DB_USER` | Usuario PostgreSQL. Default `postgres`. |
| `THC_DB_PASSWORD` | Obligatoria en `source/thc_db.connect`; usada por sincronización de catálogos/consultas. |
| `METABASE_URL` | URL de Metabase. Default `http://localhost:3000`. |
| `METABASE_EMAIL` | Requerida para `scripts/create_metabase_dashboard.py`. |
| `METABASE_PASSWORD` | Requerida para `scripts/create_metabase_dashboard.py`. |
| `METABASE_DATABASE_ID` | Requerida para crear dashboards Metabase, salvo uso de `--list-databases`. |

## Incidencia técnica documentada

`source/thc_dashboard.py` no lee `THC_DB_PASSWORD`; usa contraseña fija `system` en `psycopg2.connect`. Esto puede provocar diferencia entre sincronización y dashboard si el entorno usa otra contraseña.

## Comandos operativos

Desde `C:\_MisProyectos\THC_API`:

```powershell
python thc_api.py
python scripts\sync_catalogs.py --lang es_ES
python scripts\sync_queries.py --user-id 29509787 --lang es_ES
python scripts\sync_queries.py --user-id 29509787 --lang es_ES --oauth-access-token TU_TOKEN
python scripts\apply_views.py
python scripts\inspect_html.py
python scripts\create_metabase_dashboard.py --list-databases
python scripts\create_metabase_dashboard.py
```

## Funciones disponibles en `/api/functions`

Total detectado por código: **53** funciones    

53

## Documentos relacionados

- `docs/ARCHITECTURE.md`: arquitectura y flujos.
- `docs/TEST_PLAN.md`: pruebas funcionales requeridas para poder cerrar con `CUMPLE: SI`.
- `docs/CAMBIOS.MD`: registro de cambios documentales y técnicos.
- `docs/CURRENT_TASK.md`: estado actual de la tarea.
- `docs/TAREAS_PENDIENTES.MD`: pendientes y bloqueos.
