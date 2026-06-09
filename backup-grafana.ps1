# ==========================================
# Backup Grafana - THC
# Destino: C:\_BS_\THC_API\Grafana
# Conserva las 7 copias más recientes
# ==========================================

$destino = "C:\_BS_\THC_API\Grafana"
$fecha = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$rutaBackup = Join-Path $destino $fecha

# Crear carpeta destino
New-Item -ItemType Directory -Force -Path $rutaBackup | Out-Null

# Comprobar que Grafana está en ejecución
$running = docker inspect -f "{{.State.Running}}" grafana-thc 2>$null

if ($running -ne "true") {
    Write-Host "ERROR: El contenedor grafana-thc no está en ejecución."
    exit 1
}

Write-Host "Creando backup..."

# Copiar todo el directorio de datos de Grafana
docker cp grafana-thc:/var/lib/grafana $rutaBackup

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: No se pudo realizar el backup."
    exit 1
}

# Mantener únicamente las 7 copias más recientes
Get-ChildItem $destino -Directory |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip 7 |
    Remove-Item -Recurse -Force

Write-Host ""
Write-Host "Backup completado correctamente:"
Write-Host $rutaBackup