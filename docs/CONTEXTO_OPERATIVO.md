# CONTEXTO OPERATIVO

Documento de lectura previa para cualquier agente antes de iniciar tareas en este proyecto.

Objetivo: evitar repetir comprobaciones ya realizadas y separar hechos conocidos de datos pendientes.

## Proyecto

- Ruta objetivo: `C:\_MisProyectos\THC_API`
- Servidor local esperado: `python thc_api.py`
- URL local esperada del frontend/API: `http://127.0.0.1:8080/`
- Evidencias: `C:\_MisProyectos\THC_API\evidencias`
- Historico de cambios: `docs/CAMBIOS.MD`
- Normas prevalentes: `docs/AGENTS_NORMAS.MD`

## Grafana

- Grafana local documentado en: `http://127.0.0.1:3001`
- Contenedor esperado: `grafana-thc`
- Dashboard principal Grafana v2:
  - UID: `76b66a2d-ef24-4135-8b5c-9d6e9c9ad39e`
  - JSON fuente: `docs/grafana_dashboard_thc_hunter_v2.json`
- Copia local de datos detectada:
  - `grafana-backup/grafana.db`

## Configuracion Grafana ya documentada

En `docs/CAMBIOS.MD` consta una configuracion previa con:

- `GF_SECURITY_ALLOW_EMBEDDING=true`
- `GF_AUTH_ANONYMOUS_ENABLED=true`
- `GF_AUTH_ANONYMOUS_ORG_ROLE=Admin`
- Puerto local `3001`

## Scripts Grafana conocidos

- `scripts/setup_grafana.py`
  - Espera Grafana local en `http://127.0.0.1:3001`
  - Configura datasource PostgreSQL
  - Importa el dashboard v2
- `scripts/fix_grafana_dashboard_permissions.py`
  - Ajusta permisos Viewer/Editor en dashboards THC
- `scripts/create_grafana_domain_dashboards.py`
  - Crea dashboards de dominio clonando estilo TEST
- `scripts/update_grafana_hero_header.py`
  - Actualiza cabecera visual del dashboard Grafana
- `backup-grafana.ps1`
  - Espera el contenedor `grafana-thc`
  - Copia `/var/lib/grafana`

## DuckDNS / Compartir dashboard

Hecho comprobado:

- No se encontro configuracion DuckDNS existente en el repositorio.
- Los scripts existentes apuntan a Grafana local `http://127.0.0.1:3001`.
- Compartir por DuckDNS no debe resolverse tocando `assets/grafana_dashboard.html`.
- URL DuckDNS confirmada:
  - `http://thc-api.duckdns.org:3001/`
- URL visual exacta del dashboard Grafana v2:
  - `http://thc-api.duckdns.org:3001/d/76b66a2d-ef24-4135-8b5c-9d6e9c9ad39e?orgId=1&kiosk`
- Prueba externa parcial realizada el `2026-06-09 21:23:03 +02:00`:
  - URL base DuckDNS: HTTP 200, titulo `Grafana`
  - URL dashboard: HTTP 200, titulo `Grafana`, `HAS_LOGIN=False`
  - Salud Grafana: HTTP 200, `database=ok`, version `13.0.2`
  - API dashboard UID: HTTP 403
- Correccion del `2026-06-09 21:31:29 +02:00`:
  - El usuario indica que el enlace no funciona en sesion privada.
  - El usuario no pidio hacer publico ese dashboard.
  - HTTP 200 con HTML de Grafana no demuestra acceso anonimo funcional al dashboard.
  - La prueba anterior queda invalidada como cierre.
- Dashboard correcto indicado por el usuario:
  - `http://localhost:3001/d/thc-competiciones/thc-competiciones?orgId=1&from=now-6h&to=now&timezone=Europe%2FMadrid&var-query0=`
- Para publicarlo sin hacer publico todo Grafana, se debe usar `Compartir externamente` / `Public dashboard` solo en ese dashboard.
- Bloqueo encontrado: Grafana no permite `Public dashboard` con variables de plantilla.
- Cambio aplicado el `2026-06-09 21:43:41 +02:00`:
  - Se elimino la variable `query0` del dashboard `thc-competiciones`.
  - Backup previo: `evidencias/grafana_thc_competiciones_before_remove_query0_20260609_213841.json`.
  - Verificacion: antes `VARS=query0`; despues `TEMPLATING_COUNT=0`; version dashboard `32`.
  - El usuario confirma que ya lo tiene.

Para acceso externo por DuckDNS hacen falta, como minimo:

- Dominio DuckDNS exacto: ya confirmado como `thc-api.duckdns.org`.
- Modo de acceso:
  - directo por puerto: `http://thc-api.duckdns.org:3001`
  - o proxy/HTTPS, por ejemplo `https://dominio.duckdns.org`
- Redireccion NAT/firewall hacia Grafana o hacia el proxy.
- Configuracion publica de Grafana, normalmente:
  - `GF_SERVER_DOMAIN`
  - `GF_SERVER_ROOT_URL`
  - `GF_SERVER_SERVE_FROM_SUB_PATH`, solo si aplica.

Dato pendiente antes de implementar cambios adicionales:

- Solo haria falta confirmar si se quiere pasar de HTTP directo por puerto `3001` a proxy/HTTPS.

## Estado comprobado reciente

- `http://127.0.0.1:8080/health` no respondio antes del timeout durante la comprobacion anterior.
- La ruta no aparece como repositorio Git:
  - `git status --short` devolvio `fatal: not a git repository`
- Existe detalle de comprobaciones DuckDNS/Grafana en:
  - `docs/COMPROBACIONES_COMPARTIR_DASHBOARD_DUCKDNS.md`
- Existe evidencia de prueba DuckDNS parcial, posteriormente invalidada como cierre:
  - `evidencias/prueba_duckdns_grafana_20260609_212303.txt`
- Existe evidencia de correccion:
  - `evidencias/correccion_prueba_duckdns_grafana_20260609_213129.txt`
- Existe evidencia de eliminacion de variable `query0`:
  - `evidencias/quitar_variable_query0_thc_competiciones_20260609_214341.txt`

## Decisiones operativas

- Antes de investigar Grafana/DuckDNS, leer este documento.
- No repetir busquedas generales de DuckDNS/Grafana si este documento ya cubre el dato.
- Si se descubre un hecho operativo estable, agregarlo aqui.
- Si se realiza una prueba funcional, registrar el resultado en `docs/CAMBIOS.MD`.

## Estado actual de compartir dashboard DuckDNS

RESUELTA la incompatibilidad de variables para publicar solo `thc-competiciones`.

Hecho:

- El dashboard correcto es `thc-competiciones`.
- La variable `query0` fue eliminada.
- El usuario confirma que ya tiene el enlace/activacion.

URL local base del dashboard:

- `http://localhost:3001/d/thc-competiciones/thc-competiciones?orgId=1&from=now-6h&to=now&timezone=Europe%2FMadrid`

CUMPLE: SI

## Estado actual de enlaces en thc-competiciones

RESUELTO el enlace desde `competition_id` hacia la ficha publica de theHunter.

Hecho:

- En el panel `ACTIVAS` del dashboard `thc-competiciones`, el campo `competition_id` tiene data link.
- URL configurada: `https://www.thehunter.com/#competitions/details/${__value.raw}`.
- Dashboard guardado en Grafana como version `34`.
- Prueba real realizada el `2026-06-10 00:18:32 +02:00`:
  - URL origen: `http://127.0.0.1:3001/d/thc-competiciones/thc-competiciones?orgId=1&from=now-6h&to=now&timezone=Europe%2FMadrid`
  - Click en `174150`.
  - URL destino abierta: `https://www.thehunter.com/#competitions/details/174150`.
- Evidencia: `evidencias/link_competition_id_thc_competiciones_20260610_001832.txt`.

CUMPLE: SI
