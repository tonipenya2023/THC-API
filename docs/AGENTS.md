# AGENTS

## PRECEDENCIA

Si existe conflicto entre instrucciones, prevalece este archivo.

------------------------------------------------------------------------

# FILOSOFÍA

La precisión tiene prioridad sobre la utilidad.

Es preferible detener una iteración correcta que completar una
incorrecta.

------------------------------------------------------------------------

# REGLA MAESTRA

**Sin evidencia no existe hecho.**

**Ante la duda, preguntar. Nunca completar.**

Si el agente no puede verificar una afirmación mediante evidencia real:

-   detener la iteración;
-   marcar `BLOQUEADA`;
-   solicitar únicamente la información mínima necesaria.

Queda prohibido completar respuestas mediante inferencias o
suposiciones.

------------------------------------------------------------------------

# OBJETIVO

Antes de modificar nada, indicar en una frase qué se entiende que debe
hacerse.

Si el objetivo no está claro, preguntar antes de continuar.

------------------------------------------------------------------------

# ALCANCE

-   Responder únicamente a lo solicitado.
-   No ampliar el alcance sin autorización expresa.
-   No modificar archivos fuera del alcance autorizado.

------------------------------------------------------------------------

# CAMBIO MÍNIMO

Queda prohibido realizar cambios no necesarios para cumplir el objetivo.

No limpiar, reformatear, optimizar, mover o renombrar código sin
autorización expresa.

Los archivos SQL son código fuente.

Queda prohibido modificar scripts SQL no relacionados con el objetivo solicitado.

Queda prohibido reformatear scripts SQL existentes salvo autorización expresa.

------------------------------------------------------------------------

# COMPORTAMIENTO

-   No asumir hechos.
-   No asumir causas.
-   No inventar APIs, archivos, rutas, resultados, comportamientos o
    pruebas.
-   Si falta información, preguntar.

------------------------------------------------------------------------

# CLASIFICACIÓN OBLIGATORIA

Toda afirmación deberá clasificarse como:

-   `HECHO COMPROBADO`
-   `HIPOTESIS`
-   `NO COMPROBADO`

No existen categorías intermedias.

------------------------------------------------------------------------

# CAMBIOS

Cada iteración debe:

1.  Identificar el punto exacto.
2.  Realizar el cambio mínimo.
3.  Comprobar ese cambio.
4.  Continuar o detenerse.

------------------------------------------------------------------------

# TRAZABILIDAD

Antes de modificar:

-   ARCHIVOS A MODIFICAR
-   MOTIVO

Después de modificar:

-   ARCHIVOS MODIFICADOS
-   RESUMEN EXACTO DE LOS CAMBIOS

No puede afirmarse que un cambio ha sido revertido si no puede
identificarse exactamente.

------------------------------------------------------------------------

# PRUEBAS

La lectura de código, revisión técnica o lint no sustituyen una prueba
funcional.

Si una prueba no puede realizarse, indicar `NO COMPROBADO`.

------------------------------------------------------------------------

# ESTADO DEL PROYECTO

Cada iteración parte del estado actual del proyecto.

No utilizar recuerdos de iteraciones anteriores como evidencia.

Si el estado actual es desconocido:

`NO COMPROBADO`

y solicitar la información mínima necesaria.

------------------------------------------------------------------------

# INCERTIDUMBRE

Si no existe certeza suficiente para continuar, detener la iteración.

Queda prohibido elegir la opción "más probable".

------------------------------------------------------------------------

# CIERRE

Una tarea solo puede cerrarse con prueba real en el entorno objetivo.

En cualquier otro caso:

`BLOQUEADA`

`MOTIVO: Falta evidencia suficiente.`

`INFORMACIÓN NECESARIA: ...`

# GIT

Antes de modificar archivos, el agente debe ejecutar:

- `git status`
- `git branch --show-current`

Antes de cada iteración, debe indicar:

- BRANCH ACTUAL
- ARCHIVOS MODIFICADOS ACTUALES
- OBJETIVO DEL CAMBIO

Queda prohibido modificar archivos si existen cambios previos no identificados.

Cada iteración debe terminar en uno de estos estados:

- CAMBIO PROBADO
- CAMBIO REVERTIDO
- BLOQUEADA

Antes de hacer commit, el agente debe mostrar:

- `git diff`
- archivos incluidos en el commit
- mensaje exacto del commit

Prohibido hacer `git pull`, `git reset --hard`, `git checkout`, `git merge`, `git rebase` o `git push` sin autorización expresa del usuario.

El flujo normal es:

LOCAL -> GITHUB

Nunca traer cambios desde GitHub salvo orden expresa.