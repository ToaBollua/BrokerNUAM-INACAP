#!/usr/bin/env pwsh
#
# setup.ps1
# Script de instalación automatizado de PowerShell para el Mantenedor NUAM en Windows.
#
# REQUISITO PREVIO:
# 1. Instalar Python 3.11+ (asegúrate de que 'python' esté en el PATH).
# 2. Instalar PostgreSQL (asegúrate de que 'psql', 'createuser', 'createdb' estén en el PATH).
# 3. La contraseña del superusuario 'postgres' de PostgreSQL.
#
$ErrorActionPreference = "Stop"
Write-Host "--- Automatización de Instalación de Windows para NUAM ---" -ForegroundColor Cyan

# --- 0. Definir Variables ---
$DB_USER = "mantenedor_user"
$DB_PASS = "mantenedor_pass"
$DB_NAME = "mantenedor_db"

# --- 1. Verificar PGPASSWORD ---
# El script debe ejecutarse como el superusuario 'postgres' de la BD.
# La forma más limpia es que el usuario establezca esta variable ANTES de ejecutar.
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
    # Comprobar/Crear Usuario
    $userExists = psql -U postgres -d postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'"
    if ($userExists -eq "1") {
        Write-Host "Usuario '$DB_USER' ya existe."
    } else {
        Write-Host "Creando usuario '$DB_USER'..."
        createuser -U postgres $DB_USER
    }

    # Comprobar/Crear BD
    $dbExists = psql -U postgres -lqt | findstr /C:"$DB_NAME"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Base de datos '$DB_NAME' ya existe."
    } else {
        Write-Host "Creando base de datos '$DB_NAME'..."
        createdb -U postgres -O $DB_USER $DB_NAME
    }

    # Establecer contraseña y permisos (CREATEDB es para los tests)
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
if (Test-Path "venv") {
    Write-Host "'venv' ya existe. Omitiendo."
} else {
    Write-Host "Creando 'venv'..."
    python -m venv venv
}

Write-Host "Instalando dependencias desde requirements.txt..."
# Llamamos a pip directamente en lugar de activar el venv (más robusto para scripts)
.\venv\Scripts\pip.exe install -r requirements.txt

# --- 4. Creación del archivo .env ---
Write-Host "--- 3. Creando archivo .env ---"
$envContent = @"
DATABASE_URL=postgres://$DB_USER`:$DB_PASS@localhost:5432/$DB_NAME
DJANGO_SETTINGS_MODULE=brokernuam.settings
SECRET_KEY='local-debug-key-insecure'
DEBUG=True
"@
# (Nota: ` es el caracter de escape para el $ en PowerShell)
Set-Content -Path ".env" -Value $envContent
Write-Host ".env creado exitosamente."

# --- 5. Ejecución de Migraciones ---
Write-Host "--- 4. Aplicando Migraciones de Base de Datos ---"
.\venv\Scripts\python.exe manage.py migrate

# --- 6. Creación de Superusuario (No interactivo) ---
Write-Host "--- 5. Creando Superusuario (admin/admin) ---"
$cmd = "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@nuam.com', 'admin')"
echo $cmd | .\venv\Scripts\python.exe manage.py shell
Write-Host "Superusuario 'admin' con contraseña 'admin' creado/verificado."

# --- 7. Finalización ---
Write-Host "--- Instalación Completa ---" -ForegroundColor Green
Write-Host "Para iniciar el servidor, activa el entorno virtual:"
Write-Host ".\venv\Scripts\Activate.ps1"
Write-Host "...y luego ejecuta:"
Write-Host "python manage.py runserver"