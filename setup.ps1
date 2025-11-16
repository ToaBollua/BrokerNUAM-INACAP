#!/usr/bin/env pwsh
#
# setup.ps1 (Corregido)
# Script de instalación automatizado de PowerShell para el Mantenedor NUAM en Windows.
# Asume que se ejecuta desde la raíz 'BrokerNUAM-INACAP', NO desde 'brokernuam/'.
#
$ErrorActionPreference = "Stop"
Write-Host "--- Automatización de Instalación de Windows para NUAM ---" -ForegroundColor Cyan

# --- 0. Definir Variables ---
$DB_USER = "mantenedor_user"
$DB_PASS = "mantenedor_pass"
$DB_NAME = "mantenedor_db"
$PROJECT_DIR = "brokernuam"

# --- 1. Verificar PGPASSWORD ---
if (-not $env:PGPASSWORD) {
    Write-Host "[ERROR] Variable de entorno PGPASSWORD no encontrada." -ForegroundColor Red
    Write-Host "Este script necesita la contraseña del superusuario 'postgres' de tu instalación de Windows."
    Write-Host "En esta misma terminal, ejecuta lo siguiente y vuelve a intentarlo:"
    Write-Host ''
    Write-Host ' $env:PGPASSWORD = "tu_contraseña_de_postgres" '
    Write-Host ''
    exit 1
}

# --- 2. Configuración de PostgreSQL ---
Write-Host "--- 1. Configurando PostgreSQL (Host: localhost, User: postgres) ---"
try {
    $userExists = psql -U postgres -d postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'"
    if ($userExists -eq "1") { Write-Host "Usuario '$DB_USER' ya existe." }
    else { Write-Host "Creando usuario '$DB_USER'..."; createuser -U postgres $DB_USER }

    $dbExists = psql -U postgres -lqt | findstr /C:"$DB_NAME"
    if ($LASTEXITCODE -eq 0) { Write-Host "Base de datos '$DB_NAME' ya existe." }
    else { Write-Host "Creando base de datos '$DB_NAME'..."; createdb -U postgres -O $DB_USER $DB_NAME }

    Write-Host "Estableciendo contraseña y permisos para '$DB_USER'..."
    psql -U postgres -d postgres -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASS';"
    psql -U postgres -d postgres -c "ALTER USER $DB_USER CREATEDB;"
} catch {
    Write-Host "[ERROR] Falló la configuración de PostgreSQL." -ForegroundColor Red
    Write-Host "Asegúrate de que el servicio de PostgreSQL esté corriendo y que 'psql' esté en tu PATH."
    Write-Host $_.Exception.Message
    exit 1
}

# --- 3. Configuración del Entorno Python ---
Write-Host "--- 2. Configurando Entorno Python (venv) ---"
if (Test-Path "venv") { Write-Host "'venv' ya existe. Omitiendo." }
else { Write-Host "Creando 'venv'..."; python -m venv venv }

Write-Host "Instalando dependencias desde requirements.txt..."
.\venv\Scripts\pip.exe install -r requirements.txt

# --- 4. Creación del archivo .env (Ruta Corregida) ---
Write-Host "--- 3. Creando archivo .env en $PROJECT_DIR ---"
$envPath = Join-Path -Path $PROJECT_DIR -ChildPath ".env"
$envContent = @"
DATABASE_URL=postgres://$DB_USER`:$DB_PASS@localhost:5432/$DB_NAME
DJANGO_SETTINGS_MODULE=brokernuam.settings
SECRET_KEY='local-debug-key-insecure'
DEBUG=True
"@
Set-Content -Path $envPath -Value $envContent
Write-Host ".env creado exitosamente."

# --- 5. Ejecución de Migraciones (Ruta Corregida) ---
Write-Host "--- 4. Aplicando Migraciones de Base de Datos ---"
Push-Location $PROJECT_DIR # <--- CORRECCIÓN: Entrar al directorio
.\..\\venv\Scripts\python.exe manage.py migrate # <--- CORRECCIÓN: ../venv
Pop-Location # <--- CORRECCIÓN: Salir

# --- 6. Creación de Superusuario (Ruta Corregida) ---
Write-Host "--- 5. Creando Superusuario (admin/admin) ---"
$cmd = "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@nuam.com', 'admin')"
Push-Location $PROJECT_DIR # <--- CORRECCIÓN: Entrar al directorio
echo $cmd | .\..\\venv\Scripts\python.exe manage.py shell # <--- CORRECCIÓN: ../venv
Pop-Location # <--- CORRECCIÓN: Salir
Write-Host "Superusuario 'admin' con contraseña 'admin' creado/verificado."

# --- 7. Finalización (Instrucciones Corregidas) ---
Write-Host "--- Instalación Completa ---" -ForegroundColor Green
Write-Host "Para iniciar el servidor, activa el entorno virtual:"
Write-Host ".\venv\Scripts\Activate.ps1"
Write-Host "...luego entra al directorio del proyecto:"
Write-Host "cd brokernuam"
Write-Host "...y finalmente ejecuta:"
Write-Host "python manage.py runserver"