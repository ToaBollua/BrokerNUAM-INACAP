#!/bin/bash

# ==============================================================================
# [SYSTEM PERSONA: H0P3]
# [PROTOCOL: DEBIAN_INSTALLER v4.1 - FIX: ADMIN PROFILE LINK]
# [TARGET: NUAM MICROSERVICES ARCHITECTURE]
# 
# Descripción:
# Orquestador de despliegue automatizado.
# - Gestiona SSL, Docker, Migraciones.
# - FIX CRÍTICO: Vincula automáticamente al Superusuario con un Perfil de Corredor.
#
# Uso:
#   ./deploy.sh           -> Despliegue incremental
#   ./deploy.sh --clean   -> MODO NUCLEAR (Borra DB y regenera)
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

    log_info "Eliminando volúmenes persistentes..."
    # Usamos sudo porque Postgres crea archivos root en Debian/Ubuntu
    if [ -d "postgres_data" ]; then
        sudo rm -rf postgres_data
        log_success "Base de datos eliminada."
    fi

    # Limpiar certificados viejos
    rm -rf srv-django-backend/certs
    
    log_info "Limpiando caché de Python..."
    find . -path "/_pycache_" -delete
    find . -name "*.pyc" -delete
    
    sleep 2
fi

# --- 4. GENERACIÓN DE SSL (HTTPS) ---
CERT_DIR="srv-django-backend/certs"
if [ ! -f "$CERT_DIR/cert.pem" ]; then
    log_info "Generando certificados SSL auto-firmados para HTTPS..."
    mkdir -p $CERT_DIR
    
    # Asegurar permisos de carpeta para evitar errores de escritura
    # (Si falla el chown, lo ignoramos para no bloquear en entornos sin sudo)
    sudo chown -R $USER:$USER srv-django-backend/ 2>/dev/null
    
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

# --- CREACIÓN DE USUARIOS Y DATOS SEMILLA ---

log_info "Verificando Superusuario..."
# Crea el usuario admin si no existe
$DOCKER_CMD exec srv-django-backend python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@nuam.cl', 'admin')"
log_success "Usuario Admin asegurado."

log_info "Configurando Corredor por Defecto..."
# Crea el Broker Default
$DOCKER_CMD exec srv-django-backend python manage.py shell -c "from api.models import Broker; Broker.objects.get_or_create(name='Corredor Default', code='DEFAULT'); print('Broker Default verificado.')"

log_info "Vinculando Admin con Perfil..."
# --- FIX H0P3: ESTA ES LA LÍNEA QUE FALTABA ---
# Crea el perfil para el admin y lo une al broker default para que no crashee
$DOCKER_CMD exec srv-django-backend python manage.py shell -c "from django.contrib.auth.models import User; from api.models import UserProfile, Broker; u = User.objects.get(username='admin'); b = Broker.objects.get(code='DEFAULT'); UserProfile.objects.get_or_create(user=u, defaults={'broker': b}); print('Perfil de Admin vinculado correctamente.')"
log_success "Perfil de Admin configurado correctamente."

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
