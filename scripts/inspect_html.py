import urllib.request

print("Realizando peticiones al servidor local en http://127.0.0.1:8080/ ...")
html = urllib.request.urlopen('http://127.0.0.1:8080/').read().decode('utf-8')

# Verificaciones de elementos obsoletos
assert 'diamond-badge' not in html, "ERROR: diamond-badge sigue existiendo en el HTML"
assert 'expedition-hero' not in html, "ERROR: expedition-hero sigue existiendo en el HTML"
print("[OK] Elementos antiguos (diamond-badge, expedition-hero) eliminados correctamente.")

# Verificaciones de nuevos elementos y IDs requeridos
assert 'hunter-badge-img' in html, "ERROR: No se encuentra hunter-badge-img en el HTML"
assert 'hunter-badge-label' in html, "ERROR: No se encuentra hunter-badge-label en el HTML"
assert 'last-exp-reserve-logo-name' in html, "ERROR: No se encuentra last-exp-reserve-logo-name en el HTML"
assert 'achievement-badge' in html, "ERROR: No se encuentra la clase achievement-badge en el HTML"
assert 'expedition-reserve-logo' in html, "ERROR: No se encuentra la clase expedition-reserve-logo en el HTML"
print("[OK] Nuevos elementos e IDs de UI presentes en el HTML.")

# Verificaciones de lógica JS añadida
assert 'hunter-badge-img' in html and 'Moose' in html, "ERROR: Falta la lógica de inicialización o definición de los badges"
assert 'last-exp-reserve-logo-name' in html and 'last.reserve_name' in html, "ERROR: Falta la asignación del nombre de la reserva en JS"
print("[OK] Logica JS para asignacion dinamica presente en el codigo fuente.")

print("\n[OK] ¡TODAS LAS VERIFICACIONES SE HAN COMPLETADO CON EXITO! (CUMPLE: SI)")


