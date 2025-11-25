# Script para exportar datos de Supabase a CSV para Power BI
# Ejecuta el script Python de exportación

Write-Host "Exportación de datos para Power BI" -ForegroundColor Cyan
Write-Host ""

# Verificar si Python está instalado
try {
    $pythonVersion = python --version 2>&1
} catch {
    Write-Host "✗ Python no está instalado" -ForegroundColor Red
    exit 1
}

# Verificar si existe el archivo de entorno
if (-not (Test-Path "../../env.txt")) {
    Write-Host "✗ No se encontró el archivo env.txt en ../../env.txt" -ForegroundColor Red
    exit 1
}

# Instalar dependencias si no están instaladas
try {
    python -c "import supabase" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Instalando dependencias..." -ForegroundColor Yellow
        pip install -q -r requirements_csv.txt
    }
} catch {
    pip install -q -r requirements_csv.txt
}

# Ejecutar el script de exportación
python export_to_csv.py

# Verificar si se creó la carpeta de exportación
if (Test-Path "csv_exports") {
    Write-Host ""
    Write-Host "Archivos generados:" -ForegroundColor White
    Get-ChildItem "csv_exports\*.csv" | ForEach-Object {
        Write-Host "  ✓ $($_.Name)" -ForegroundColor Gray
    }
} else {
    Write-Host ""
    Write-Host "⚠️  No se crearon archivos" -ForegroundColor Yellow
}

Write-Host ""
