# Arquitectura THC_API

## Alcance

Este documento describe el comportamiento inferido directamente del código fuente. No sustituye la prueba funcional obligatoria definida en `docs/AGENTS_NORMAS.MD`.

## Componentes

```text
Usuario navegador
  |
  | http://127.0.0.1:8080/
  v
source/thc_api.py
  |-- sirve assets/index.html
  |-- expone /health
  |-- expone /api/functions
  |-- expone /api/call
  |-- expone /api/dashboard_data

/api/call
  v
source/thc_client.py
  |-- valida parámetros contra source/thc_client_registry.py
  |-- llama api.thehunter.com o apiv2.thehunter.com
  |-- opcionalmente enriquece IDs con catálogos

Sincronización
  scripts/sync_catalogs.py -> source/thc_db.py -> sql/schema.sql -> PostgreSQL
  scripts/sync_queries.py  -> source/thc_query_db.py -> PostgreSQL
  scripts/apply_views.py   -> sql/dashboard_views.sql -> PostgreSQL

Dashboard local
  /api/dashboard_data -> source/thc_dashboard.py -> vistas/tablas PostgreSQL -> JSON

Metabase
  scripts/create_metabase_dashboard.py -> API Metabase -> preguntas/dashboards
```

## Servidor local

Archivo: `source/thc_api.py`.

- Host fijo: `127.0.0.1`.
- Puerto fijo: `8080`.
- Servidor: `ThreadingHTTPServer`.
- Launcher raíz: `thc_api.py`.
- HTML principal: `assets/index.html`.

### Manejo de errores HTTP

| Caso | Código | Respuesta |
|---|---:|---|
| Ruta inexistente | `404` | `{"error":"Not found"}` |
| JSON inválido en `/api/call` | `400` | `{"error":"Invalid request: ..."}` |
| Error API externa | `502` | `{"error":"Upstream ..."}` |
| Excepción no controlada | `500` | `{"error":"Unexpected server error: ..."}` |

## Cliente theHunter

Archivo: `source/thc_client.py`.

Bases remotas:

- `https://api.thehunter.com`
- `https://apiv2.thehunter.com`

Características:

- Timeout: `20` segundos.
- `get_application_data` usa `lru_cache(maxsize=8)`.
- Las peticiones capturadas para UI redactan parámetros sensibles cuyo nombre contenga `token`, `password`, `secret` o `key`.
- `call_function` valida parámetros numéricos convirtiéndolos a `int`.
- Si un parámetro requerido llega vacío, lanza `ThcApiError`.

## Registro de funciones

Archivo: `source/thc_client_registry.py`.

Total registrado: **53** funciones.

53

## Sincronización PostgreSQL

### Catálogos

Flujo:

```text
scripts/sync_catalogs.py
  -> source.thc_db.sync_catalogs(lang)
  -> source.thc_client.get_application_data(lang)
  -> sql/schema.sql
  -> tablas api.*
```

Comportamiento:

- Crea/aplica esquema con `sql/schema.sql`.
- Inserta una fila en `api.catalog_sync_runs` con estado `running`.
- Borra datos del idioma indicado en tablas dependientes de idioma.
- Inserta catálogo genérico en `api.catalog_entries`.
- Inserta tablas normalizadas mediante `source/thc_catalog_loader.py`.
- Actualiza el sync run a `completed`.

### Consultas API

Flujo:

```text
scripts/sync_queries.py
  -> source.thc_query_db.sync_queries(...)
  -> source.thc_client.call_function(...)
  -> tablas api.query_*
```

Comportamiento relevante:

- Puede sincronizar todas las funciones registradas o solo las indicadas con `--function`.
- Genera tablas dinámicas con prefijo `api.query_`.
- Expande estructuras JSON anidadas a tablas hijas.
- Crea tablas auxiliares de estadísticas por arma cuando detecta campos compatibles.
- Usa parámetros por defecto cuando no se proporcionan valores.

## Dashboard local

Archivo: `source/thc_dashboard.py`.

Endpoint consumidor: `GET /api/dashboard_data`.

Bloques JSON devueltos si la BD responde:

| Clave | Origen principal |
|---|---|
| `overview` | `api.vw_hunter_overview` |
| `expeditions_weekly` | `api.vw_expedition_weekly` |
| `reserves` | `api.vw_reserve_performance` |
| `weapons` | `api.vw_weapon_analytics` |
| `species` | `api.vw_species_analytics` |
| `records` | `api.vw_personal_records` |
| `recent_expeditions` | `api.query_statistics_history_expeditions` + `api.query_catalog_reserves` |
| `top1_count` | `api.vw_leaderboard_top100` |
| `top100_count` | `api.vw_leaderboard_top100` |
| `recent_records` | `api.vw_personal_records` |
| `last_expedition_animals` | `api.query_statistics_last_hunt_animal` + `api.query_catalog_species` |
| `last_hunt_details` | `api.query_statistics_last_hunt` y tabla animal asociada |
| `kpis` | Varias tablas `api.query_*` |

Si ocurre cualquier excepción exterior, imprime `Error fetching dashboard data:` y devuelve `{}`.

## SQL

| Archivo | Función |
|---|---|
| `sql/schema.sql` | Crea esquema `api`, tablas base de catálogos, vistas/funciones auxiliares. |
| `sql/dashboard_views.sql` | Vistas analíticas consumidas por `source/thc_dashboard.py`. |
| `sql/metabase_queries.sql` | Consultas para cuadros de mando Metabase. |
| `sql/hall_of_fame_schema.sql` | Estructura específica Hall of Fame. |
| `sql/hall_of_fame_examples.sql` | Consultas ejemplo Hall of Fame. |
| `sql/quick_validation.sql` | Validaciones SQL rápidas. |

## Puntos de riesgo documentados

| Riesgo | Evidencia en código | Impacto |
|---|---|---|
| Contraseña fija del dashboard | `source/thc_dashboard.py` usa `password="system"` | El dashboard puede fallar aunque `THC_DB_PASSWORD` esté configurada. |
| `/api/dashboard_data` oculta excepciones | `except Exception as e: ... return {}` | Un fallo de BD puede parecer respuesta vacía. |
| `scripts/inspect_html.py` afirma `CUMPLE: SI` | El script imprime ese texto si pasan asserts HTML | Según normas, esa prueba no basta para cierre funcional completo. |
| Dependencia de APIs externas | `api.thehunter.com`, `apiv2.thehunter.com` | Las pruebas pueden fallar por red/API externa. |
| Tokens OAuth manuales | funciones `missions`, `competition_states`, etc. | Sin token no se prueban endpoints personales autenticados. |
