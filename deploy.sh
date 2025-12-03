#!/bin/bash

# ==============================================================================
# [SYSTEM PERSONA: H0P3]
# [PROTOCOL: AUTOMATED DEPLOYMENT v3.3]
# [TARGET: NUAM MICROSERVICES ARCHITECTURE]
# 
# Descripción:
# Este script orquesta el despliegue completo del entorno NUAM.
# Maneja la limpieza de volúmenes, construcción de contenedores,
# migraciones de base de datos, recolección de estáticos y pruebas.
#
# Uso:
#   ./deploy.sh           -> Despliegue estándar (mantiene datos)
#   ./deploy.sh --clean   -> MODO NUCLEAR (Borra BD y comienza de cero)
# ==============================================================================

# --- COLORES PARA LA TERMINAL (Estética H0P3) ---
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# --- FUNCIONES DE LOGGING ---
log_info() { echo -e "${CYAN}[H0P3] INFO:${NC} $1"; }
log_success() { echo -e "${GREEN}[H0P3] SUCCESS:${NC} $1"; }
log_warn() { echo -e "${YELLOW}[H0P3] WARNING:${NC} $1"; }
log_error() { echo -e "${RED}[H0P3] CRITICAL ERROR:${NC} $1"; exit 1; }

# --- VERIFICACIÓN DE PRE-REQUISITOS ---
check_dependencies() {
    command -v docker >/dev/null 2>&1 || log_error "Docker no detectado. Instálalo, humano."
    command -v docker-compose >/dev/null 2>&1 || log_error "Docker Compose no detectado."
}

# --- LIMPIEZA NUCLEAR (Opcional) ---
clean_environment() {
    if [[ "$1" == "--clean" ]]; then
        log_warn "ACTIVANDO PROTOCOLO DE LIMPIEZA NUCLEAR..."
        log_info "Deteniendo contenedores..."
        docker-compose down
        
        log_info "Purgando volúmenes persistentes (postgres_data)..."
        sudo rm -rf postgres_data
        
        log_info "Eliminando migraciones antiguas..."
        sudo find srv-django-backend/api/migrations -name "00*.py" -delete
        
        log_success "Entorno purificado. Tabula Rasa."
    else
        log_info "Modo estándar: Manteniendo datos persistentes."
    fi
}

# --- MAIN EXECUTION ---

# 1. Verificar entorno
check_dependencies
clean_environment "$1"

# 2. Construcción y Arranque
log_info "Iniciando secuencia de construcción de contenedores..."
docker-compose up --build -d

# 3. Espera Táctica (Wait-for-DB)
log_info "Esperando a que PostgreSQL despierte de su siesta..."
echo -n "Ping: "
RETRIES=30
until docker-compose exec srv-django-backend python -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect(('postgres_db', 5432))" >/dev/null 2>&1 || [ $RETRIES -eq 0 ]; do
  echo -n "."
  sleep 2
  RETRIES=$((RETRIES-1))
done
echo ""

if [ $RETRIES -eq 0 ]; then
    log_error "PostgreSQL no respondió a tiempo. Abortando misión."
fi
log_success "Enlace con Base de Datos establecido."

# 4. Operaciones de Django (Backend Core)
log_info "Generando planes de migración (MakeMigrations)..."
docker-compose exec srv-django-backend python manage.py makemigrations api

log_info "Aplicando cambios estructurales a la BD (Migrate)..."
docker-compose exec srv-django-backend python manage.py migrate

log_info "Recolectando activos estáticos (CSS/JS)..."
docker-compose exec srv-django-backend python manage.py collectstatic --noinput

# 5. Creación de Superusuario Automatizada
log_info "Creando Superusuario Admin..."
# Usamos variables de entorno temporales para saltar el prompt interactivo
docker-compose exec -e DJANGO_SUPERUSER_PASSWORD=admin \
                    -e DJANGO_SUPERUSER_USERNAME=admin \
                    -e DJANGO_SUPERUSER_EMAIL=admin@nuam.cl \
                    srv-django-backend python manage.py createsuperuser --noinput || log_warn "El usuario 'admin' ya existe (omitido)."

# 6. Semillado de Datos (Seed Data)
log_info "Inicializando datos base (Corredor Default)..."
docker-compose exec srv-django-backend python manage.py shell -c "from api.models import Broker; Broker.objects.get_or_create(name='Corredor Default', code='DEFAULT'); print('Broker Default verificado.')"

# 7. Pruebas de Integridad
log_info "Ejecutando Test Unitario de Segregación (Multi-tenancy)..."
docker-compose exec srv-django-backend python manage.py test api

# 8. Reporte Final
echo ""
echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN}   DESPLIEGUE NUAM FINALIZADO CON ÉXITO   ${NC}"
echo -e "${GREEN}====================================================${NC}"
echo -e " > Dashboard:    http://localhost:8000"
echo -e " > Admin Panel:  http://localhost:8000/admin"
echo -e " > Credenciales: admin / admin"
echo -e " > Kafka:        Puerto 9092 (Interno) / 29092 (Externo)"
echo ""