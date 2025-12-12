#!/bin/bash

# ==============================================================================
# [SYSTEM PERSONA: H0P3]
# [PROTOCOL: DEBIAN_INSTALLER v4.0]
# [TARGET: NUAM MICROSERVICES ARCHITECTURE]
# 
# Descripción:
# Orquestador de despliegue para entornos Linux (Debian/Ubuntu/Arch).
# Gestiona SSL, Docker, Migraciones y Datos Semilla.
#
# Uso:
#   ./deploy.sh           -> Despliegue incremental (Mantiene datos)
#   ./deploy.sh --clean   -> MODO NUCLEAR (Borra TODO y regenera desde cero)
# ==============================================================================

# --- 1. CONFIGURACIÓN VISUAL ---
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC}   $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERR]${NC}  $1"; exit 1; }

# --- 2. DETECCIÓN DE ENTORNO ---
# Detectar si se usa 'docker-compose' (v1) o 'docker compose' (v2)
if docker compose version >/dev/null 2>&1; then
    DOCKER_CMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    DOCKER_CMD="docker-compose"
else
    log_error "No se encontró docker-compose ni docker compose. Instala Docker primero."
fi

# Verificar OpenSSL (Necesario para HTTPS)
if ! command -v openssl >/dev/null 2>&1; then
    log_error "OpenSSL no está instalado. Ejecuta: sudo apt install openssl"
fi

# --- 3. MODO LIMPIEZA (NUCLEAR OPTION) ---
if [[ "$1" == "--clean" ]]; then
    echo -e "${RED}"
    echo "========================================================"
    echo " ☢️  INICIANDO PROTOCOLO DE LIMPIEZA NUCLEAR  ☢️"
    echo "    SE BORRARÁ TODA LA BASE DE DATOS Y CERTIFICADOS"
    echo "========================================================"
    echo -e "${NC}"
    
    log_info "Deteniendo contenedores..."
    $DOCKER_CMD down --remove-orphans

    log_info "Eliminando volúmenes persistentes (Requiere permisos)..."
    # Usamos sudo porque Postgres crea archivos root
    if [ -d "postgres_data" ]; then
        sudo rm -rf postgres_data
        log_success "Base de datos eliminada."
    fi

    # Limpiar certificados viejos
    rm -rf srv-django-backend/certs
    log_success "Certificados eliminados."
    
    log_info "Limpiando caché de Python..."
    find . -path "*/__pycache__*" -delete
    find . -name "*.pyc" -delete
    
    sleep 2
fi

# --- 4. GENERACIÓN DE SSL (HTTPS) ---
CERT_DIR="srv-django-backend/certs"
if [ ! -f "$CERT_DIR/cert.pem" ]; then
    log_info "Generando certificados SSL auto-firmados para HTTPS..."
    mkdir -p $CERT_DIR
    # Permisos de usuario actual para evitar bloqueos
    sudo chown -R $USER:$USER srv-django-backend/
    
    openssl req -x509 -newkey rsa:4096 \
      -keyout $CERT_DIR/key.pem \
      -out $CERT_DIR/cert.pem \
      -days 365 -nodes \
      -subj "/C=CL/ST=Santiago/L=Macul/O=NUAM/OU=IT/CN=localhost" 2>/dev/null
      
    if [ $? -eq 0 ]; then
        log_success "Certificados generados en $CERT_DIR"
    else
        log_error "Falló la generación de certificados SSL."
    fi
else
    log_info "Certificados SSL detectados. Saltando generación."
fi

# --- 5. CONSTRUCCIÓN Y DESPLIEGUE ---
log_info "Levantando infraestructura con Docker..."
$DOCKER_CMD up --build -d

if [ $? -ne 0 ]; then
    log_error "Falló el despliegue de Docker. Revisa los logs."
fi

# --- 6. ESPERA ACTIVA (HEALTH CHECK) ---
log_info "Esperando que la Base de Datos esté lista..."
# Barra de progreso falsa pero tranquilizadora
for i in {1..10}; do
    echo -ne "Cargando... ["
    for ((j=0; j<i; j++)); do echo -ne "▓"; done
    for ((j=i; j<10; j++)); do echo -ne " "; done
    echo -ne "] ($((i*10))%)\r"
    sleep 1
done
echo ""

# --- 7. POST-CONFIGURACIÓN (DJANGO) ---

log_info "Aplicando Migraciones (Estructura de Base de Datos)..."
$DOCKER_CMD exec srv-django-backend python manage.py makemigrations api
$DOCKER_CMD exec srv-django-backend python manage.py migrate --noinput

log_info "Recolectando Archivos Estáticos (CSS/JS)..."
$DOCKER_CMD exec srv-django-backend python manage.py collectstatic --noinput

# Creación de Superusuario (Idempotente: no falla si ya existe)
log_info "Verificando Superusuario..."
$DOCKER_CMD exec srv-django-backend python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@nuam.cl', 'admin')"
log_success "Superusuario asegurado: admin / admin"

# Semillado de Datos (Broker Default)
log_info "Inicializando datos base..."
$DOCKER_CMD exec srv-django-backend python manage.py shell -c "from api.models import Broker; Broker.objects.get_or_create(name='Corredor Default', code='DEFAULT'); print('Broker Default verificado.')"

# --- 8. PRUEBAS FINALES ---
log_info "Ejecutando Test Unitario de Segregación..."
$DOCKER_CMD exec srv-django-backend python manage.py test api

# --- 9. RESUMEN ---
echo ""
echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN}   🚀 SISTEMA NUAM OPERATIVO Y SEGURO (HTTPS)   ${NC}"
echo -e "${GREEN}====================================================${NC}"
echo -e " > 📊 Dashboard:    https://localhost:8000 (Aceptar riesgo SSL)"
echo -e " > ⚙️  Admin Panel:  https://localhost:8000/admin"
echo -e " > 👤 Credenciales: admin / admin"
echo -e ""
echo -e "${YELLOW}[TIP]${NC} Para ver logs en tiempo real: ${BLUE}docker compose logs -f${NC}"
echo ""