param(
  [string]$EnvDir = "venv"
)

# Ir a la carpeta del script
$here = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Push-Location $here

# Crear venv si no existe
if (-not (Test-Path $EnvDir)) {
  python -m venv $EnvDir
}

# Actualizar pip e instalar requirements
$pythonExe = Join-Path $EnvDir "Scripts\python.exe"
& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install -r .\supabase\backEnd\db\seeds\requirements.txt

Write-Host "Dependencias instaladas en '$EnvDir'. Activar con: .\$EnvDir\Scripts\Activate.ps1"

Pop-Location
