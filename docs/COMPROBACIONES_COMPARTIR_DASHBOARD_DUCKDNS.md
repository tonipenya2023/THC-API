# Comprobaciones - Compartir dashboard por DuckDNS

Fecha: 2026-06-09

## Objetivo entendido

Compartir el dashboard Grafana para acceso externo mediante un dominio DuckDNS.

No se debe resolver mediante cambios en `assets/grafana_dashboard.html`.

## Comprobaciones realizadas

- Se reviso la documentacion local:
  - `docs/README.md`
  - `docs/CAMBIOS.MD`
  - `docs/AGENTS_NORMAS.MD`
- Se busco configuracion o menciones existentes sobre:
  - `duckdns`
  - `GF_SERVER`
  - `GF_AUTH`
  - `GRAFANA_URL`
  - `3001`
  - `grafana-thc`
  - `root_url`
  - `domain`
  - `anonymous`
  - `allow_embedding`
- No se encontro configuracion DuckDNS existente en el repositorio.
- Se comprobo que la configuracion documentada anteriormente usa Grafana local en:
  - `http://127.0.0.1:3001`
- Se comprobo que el proyecto documenta el contenedor:
  - `grafana-thc`
- Se comprobo que `docs/CAMBIOS.MD` indica una configuracion previa con:
  - `GF_SECURITY_ALLOW_EMBEDDING=true`
  - `GF_AUTH_ANONYMOUS_ENABLED=true`
  - `GF_AUTH_ANONYMOUS_ORG_ROLE=Admin`
  - puerto local `3001`
- Se revisaron scripts relacionados con Grafana:
  - `scripts/setup_grafana.py`
  - `scripts/fix_grafana_dashboard_permissions.py`
  - `scripts/create_grafana_domain_dashboards.py`
  - `scripts/update_grafana_hero_header.py`
  - `backup-grafana.ps1`
- Se comprobo que esos scripts apuntan a Grafana local:
  - `http://127.0.0.1:3001`
- Se comprobo que `backup-grafana.ps1` espera el contenedor Docker:
  - `grafana-thc`
- Se comprobo que existe copia local de datos de Grafana en:
  - `grafana-backup/grafana.db`
- Se intento comprobar el servicio local:
  - `http://127.0.0.1:8080/health`
- Resultado de esa prueba:
  - timeout
  - el servicio local `8080` no respondia en ese momento
- Se comprobo que no hay repositorio Git disponible en esta ruta:
  - `git status --short` devolvio `fatal: not a git repository`
- Se revisaron lanzadores locales:
  - `run_listening_8080.bat`
  - `run_listening_8081.bat`
- Se comprobo que `run_listening_8080.bat` ejecuta:
  - `py c:\_MisProyectos\THC_API\thc_api.py`
- Se comprobo que `run_listening_8081.bat` ejecuta el mismo servidor con:
  - `THC_API_PORT=8081`

## Conclusion tecnica

Para acceso por DuckDNS no basta con cambiar el HTML local.

Hay que configurar la exposicion de Grafana:

- Dominio publico DuckDNS exacto.
- Puerto externo o proxy HTTPS.
- Redireccion NAT/firewall hacia Grafana o hacia el proxy.
- Configuracion de Grafana con URL publica, normalmente mediante:
  - `GF_SERVER_DOMAIN`
  - `GF_SERVER_ROOT_URL`
  - `GF_SERVER_SERVE_FROM_SUB_PATH`, solo si aplica.

## Dato pendiente pedido una sola vez

Dominio exacto confirmado posteriormente:

- `http://thc-api.duckdns.org:3001/`
- URL dashboard exacta:
  - `http://thc-api.duckdns.org:3001/d/76b66a2d-ef24-4135-8b5c-9d6e9c9ad39e?orgId=1&kiosk`

Evidencia de prueba:

- `evidencias/prueba_duckdns_grafana_20260609_212303.txt`
- Correccion posterior:
  - `evidencias/correccion_prueba_duckdns_grafana_20260609_213129.txt`
  - El usuario indica que el enlace no funciona en sesion privada.
  - El usuario no pidio hacer publico ese dashboard.
  - HTTP 200 con HTML de Grafana no demuestra acceso anonimo funcional al dashboard.

## Estado

ACTUALIZADO.

Correccion posterior:

- El dashboard correcto indicado por el usuario es `thc-competiciones`.
- Se elimino la variable `query0`, que bloqueaba `Compartir externamente`.
- Backup previo:
  - `evidencias/grafana_thc_competiciones_before_remove_query0_20260609_213841.json`
- Evidencia:
  - `evidencias/quitar_variable_query0_thc_competiciones_20260609_214341.txt`
- El usuario confirma que ya lo tiene.

CUMPLE: SI
