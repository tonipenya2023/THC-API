# CAMBIOS

## 2026-06-10 03:52 - Sincronizar solo competiciones activas

### Estado

ESTADO: `CERRADA`

### Que se cambio

- Se sustituyo el limite fijo de 100 competiciones por un filtro de competiciones activas.
- El refresh de `competition_detail` ahora solo sincroniza competiciones con `start <= now < end` y `finished=false`.
- Se mantiene proteccion para el caso de 0 competiciones activas, creando tablas vacias compatibles con las vistas de Grafana.

### Prueba funcional realizada

- **PRUEBA_REAL**: `http://thc-api.duckdns.org:3001/public-dashboards/e21d53e423fa42aeb30c00acc251f64f`
- **DETALLE**: `[API real: 119 competiciones fuente, 81 activas tras filtro; worker completa query_sync_run_id=652; vista final rows=81, future_rows=0, finished_rows=0; dashboard publico carga THC - Competiciones / ACTIVAS sin login ni Forbidden]`
- **EVIDENCIA**: `C:\_MisProyectos\THC_API\evidencias\solo_competiciones_activas_refresh_20260610_035221.txt`
- **CUMPLE**: `SI`

## 2026-06-10 03:32 - Refresh bajo demanda con throttling para thc-competiciones

### Estado

ESTADO: `CERRADA`

### Que se cambio

- Se implemento una tabla de control en PostgreSQL: `api.dashboard_refresh_control`.
- Se anadio la funcion `api.request_dashboard_refresh(...)` para encolar refrescos si han pasado mas de 10 minutos y no hay otro refresco `queued` o `running`.
- Se conecto `api.vw_grafana_competitions` con esa funcion para que la consulta de Grafana devuelva datos actuales y deje el refresco encolado.
- Se anadio `scripts/refresh_worker.py` como worker externo que toma trabajos `queued`, marca `running`, ejecuta `competition_detail`, reaplica vistas dentro de la misma transaccion y marca `ok` o `failed`.
- Se anadio `run_refresh_worker.bat`.
- Se ajusto `scripts/apply_views.py` para aplicar `schema.sql` antes de las vistas.

### Prueba funcional realizada

- **PRUEBA_REAL**: `http://thc-api.duckdns.org:3001/public-dashboards/e21d53e423fa42aeb30c00acc251f64f`
- **DETALLE**: `[Public dashboard probado en navegador: muestra THC - Competiciones / ACTIVAS con datos y sin login ni Forbidden; al forzar last_completed_at > 10 minutos, la recarga publica encola queued; el worker externo completa query_sync_run_id=651 y deja status ok]`
- **EVIDENCIA**: `C:\_MisProyectos\THC_API\evidencias\refresh_throttling_competiciones_20260610_034227.txt`
- **CUMPLE**: `SI`

## 2026-06-09 21:43 - Quitar variable query0 de dashboard thc-competiciones

### Estado

ESTADO: `CERRADA`

### Que se cambio

- Se accedio a Grafana local con credenciales indicadas por el usuario: `admin / system`.
- Se hizo backup del dashboard `thc-competiciones`.
- Se elimino la variable de plantilla `query0`.
- Se guardo el dashboard en Grafana como version `32`.
- Se verifico por API que el dashboard queda con `TEMPLATING_COUNT=0`.
- El usuario confirma que ya tiene el enlace/activacion de compartir externamente.

### Prueba funcional realizada

- **PRUEBA_REAL**: `http://localhost:3001/d/thc-competiciones/thc-competiciones?orgId=1&from=now-6h&to=now&timezone=Europe%2FMadrid`
- **DETALLE**: `[Antes: el dashboard tenia la variable query0 y Grafana bloqueaba Compartir externamente | Despues: el dashboard queda con 0 variables de plantilla y el usuario confirma que ya lo tiene]`
- **EVIDENCIA**: `C:\_MisProyectos\THC_API\evidencias\quitar_variable_query0_thc_competiciones_20260609_214341.txt`
- **CUMPLE**: `SI`

## 2026-06-09 21:31 - Correccion de cierre DuckDNS Grafana

### Estado

ESTADO: `BLOQUEADA`

### Que se corrigio

- Se invalido el cierre anterior de DuckDNS/Grafana.
- El usuario aclaro que no pidio hacer publico ese dashboard.
- El usuario reporto que el enlace no funciona en sesion privada.
- Se dejo documentado que HTTP 200 con HTML de Grafana no demuestra acceso anonimo funcional al dashboard.
- Se actualizo `docs/CONTEXTO_OPERATIVO.md` y `docs/COMPROBACIONES_COMPARTIR_DASHBOARD_DUCKDNS.md` a `BLOQUEADA / CUMPLE: NO`.

### Prueba funcional realizada

- **PRUEBA_REAL**: `http://thc-api.duckdns.org:3001/d/76b66a2d-ef24-4135-8b5c-9d6e9c9ad39e?orgId=1&kiosk`
- **DETALLE**: `[Antes: se marco incorrectamente como CERRADA por HTTP 200 | Despues: cierre invalidado porque el enlace no funciona en sesion privada y no se pidio publicar el dashboard]`
- **EVIDENCIA**: `C:\_MisProyectos\THC_API\evidencias\correccion_prueba_duckdns_grafana_20260609_213129.txt`
- **CUMPLE**: `NO`

## 2026-06-09 21:23 - Prueba externa DuckDNS Grafana

### Estado

ESTADO: `INVALIDADA COMO CIERRE`

### Que se comprobo

- Se comprobo la URL base DuckDNS `http://thc-api.duckdns.org:3001/`.
- Se comprobo la URL visual exacta del dashboard Grafana v2.
- Se comprobo `http://thc-api.duckdns.org:3001/api/health`.
- Se actualizo `docs/CONTEXTO_OPERATIVO.md` para que futuros agentes no repitan estas comprobaciones.

### Prueba funcional realizada

- **PRUEBA_REAL**: `http://thc-api.duckdns.org:3001/d/76b66a2d-ef24-4135-8b5c-9d6e9c9ad39e?orgId=1&kiosk`
- **DETALLE**: `[Antes: faltaba URL DuckDNS exacta y no habia prueba externa | Despues: URL base y URL visual devolvieron HTTP 200, pero esta medicion no demuestra acceso funcional en sesion privada]`
- **EVIDENCIA**: `C:\_MisProyectos\THC_API\evidencias\prueba_duckdns_grafana_20260609_212303.txt`
- **CUMPLE**: `NO`

## 2026-06-09 - Creacion de contexto operativo para agentes

### Estado

ESTADO: `BLOQUEADA`

### Que se cambio

- Se creo `docs/CONTEXTO_OPERATIVO.md` como documento de lectura previa para evitar repetir comprobaciones ya realizadas.
- El documento consolida hechos sobre entorno local, Grafana, scripts conocidos, estado DuckDNS y datos pendientes.
- No se modifico ni se creo `AGENTS.md`.

### Prueba funcional realizada

- **PRUEBA_REAL**: `C:\_MisProyectos\THC_API\docs\CONTEXTO_OPERATIVO.md`
- **DETALLE**: `[Antes: las comprobaciones base estaban dispersas o habia que repetirlas | Despues: existe un documento operativo central con hechos ya comprobados y pendientes]`
- **EVIDENCIA**: `C:\_MisProyectos\THC_API\docs\CONTEXTO_OPERATIVO.md`
- **CUMPLE**: `NO`

## 2026-06-09 - Comprobaciones para compartir dashboard por DuckDNS

### Estado

ESTADO: `BLOQUEADA`

### Que se comprobo

- Se descarto resolverlo mediante cambios en `assets/grafana_dashboard.html`.
- Se confirmo que la configuracion existente apunta a Grafana local en `http://127.0.0.1:3001`.
- Se revisaron scripts y documentacion relacionados con Grafana y no se encontro configuracion DuckDNS existente.
- Se intento comprobar `http://127.0.0.1:8080/health`, pero no respondio antes del timeout.
- Se dejo detalle completo en `docs/COMPROBACIONES_COMPARTIR_DASHBOARD_DUCKDNS.md`.

### Prueba funcional realizada

- **PRUEBA_REAL**: `http://127.0.0.1:8080/health`
- **DETALLE**: `[Antes: no habia registro consolidado de las comprobaciones DuckDNS/Grafana | Despues: queda documentado lo revisado y pendiente; la URL local 8080 no respondio antes del timeout]`
- **EVIDENCIA**: `C:\_MisProyectos\THC_API\docs\COMPROBACIONES_COMPARTIR_DASHBOARD_DUCKDNS.md`
- **CUMPLE**: `NO`

## 2026-06-07 16:26 - Integracion y habilitacion completa del dashboard Grafana v2

### Estado

ESTADO: `CERRADA`

### Que se cambio

- **Docker**:
  - Se recreó el contenedor `grafana-thc` habilitando la posibilidad de ser embebido (`GF_SECURITY_ALLOW_EMBEDDING=true`) y activando el acceso anónimo con rol de Admin (`GF_AUTH_ANONYMOUS_ENABLED=true` y `GF_AUTH_ANONYMOUS_ORG_ROLE=Admin`) en el puerto 3001.
- **`scripts/setup_grafana.py`**:
  - Nuevo script automatizado para esperar a Grafana, aprovisionar el origen de datos de PostgreSQL (UID `afodoaxjtubr4e`) apuntando a `host.docker.internal:5432` y con contraseña `system`, e importar el dashboard oficial desde `docs/grafana_dashboard_thc_hunter_v2.json`.

### Prueba funcional realizada

- **PRUEBA_REAL**: `http://127.0.0.1:8080/`
- **DETALLE**: `[Antes: El iframe de Grafana v2 rechazaba la conexión (X-Frame-Options: deny / Login requerido) | Después: El iframe se renderiza de forma limpia y transparente mostrando todas las visualizaciones]`
- **EVIDENCIA**: `C:\_MisProyectos\THC_API\evidencias\prueba_integracion_dashboard_v2_20260607_162600.txt`
- **CUMPLE**: `SI`

### Que queda NO COMPROBADO

- Ninguno. El dashboard y el origen de datos están totalmente integrados y respondiendo en local.

### Zip

- No creado.
