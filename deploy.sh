#!/bin/bash

# ==============================================================================
# [SYSTEM PERSONA: H0P3]
# [PROTOCOL: DEBIAN_INSTALLER v4.3 - FIX: ENV + DOCKER PERMS + PORT AUTO-FREE + REAL HEALTHCHECK]
# [TARGET: NUAM MICROSERVICES ARCHITECTURE]
# ==============================================================================

set -u

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

require_cmd() { command -v "$1" >/dev/null 2>&1 || log_error "Falta '$1'. Instálalo e intenta nuevamente."; }

# --- HELPERS: PUERTO 5432 ---
port_5432_in_use() {
  sudo ss -ltnp 2>/dev/null | grep -qE '(:5432)\s'
}

pids_listening_5432() {
  # Devuelve PIDs (uno por línea) que escuchan en 5432 (si hay)
  sudo ss -ltnp 2>/dev/null \
    | awk '/:5432/ && /users:\(\(/ {
        match($0, /pid=([0-9]+)/, a);
        if (a[1]!="") print a[1];
      }' \
    | sort -u
}

free_port_5432() {
  if ! port_5432_in_use; then
    return 0
  fi

  log_warn "El puerto 5432 del host está en uso. Intentando liberarlo automáticamente..."

  # 1) Intento limpio: detener y deshabilitar postgresql.service si existe
  if systemctl list-unit-files 2>/dev/null | grep -q '^postgresql\.service'; then
    if sudo systemctl is-active --quiet postgresql; then
      log_info "Deteniendo servicio postgresql (host)..."
      sudo systemctl stop postgresql >/dev/null 2>&1 || true
    fi
    if sudo systemctl is-enabled --quiet postgresql; then
      log_info "Deshabilitando servicio postgresql (host)..."
      sudo systemctl disable postgresql >/dev/null 2>&1 || true
    fi
  fi

  # Espera corta por liberación de socket
  sleep 2

  # 2) Si sigue ocupado, matar PID(s) que están escuchando en 5432
  if port_5432_in_use; then
    local pids
    pids="$(pids_listening_5432 || true)"
    if [ -n "$pids" ]; then
      log_warn "5432 sigue ocupado. Matando proceso(s) que escuchan en 5432: $pids"
      # Primero SIGTERM
      while read -r pid; do
        [ -n "$pid" ] && sudo kill -TERM "$pid" >/dev/null 2>&1 || true
      done <<< "$pids"

      sleep 2

      # Si aún está ocupado, SIGKILL
      if port_5432_in_use; then
        log_warn "SIGTERM no fue suficiente. Aplicando SIGKILL a: $pids"
        while read -r pid; do
          [ -n "$pid" ] && sudo kill -KILL "$pid" >/dev/null 2>&1 || true
        done <<< "$pids"
        sleep 1
      fi
    else
      log_warn "No se pudo identificar PID en 5432 vía ss. Intentando con lsof..."
      if command -v lsof >/dev/null 2>&1; then
        sudo lsof -tiTCP:5432 -sTCP:LISTEN | xargs -r sudo kill -TERM || true
        sleep 2
        sudo lsof -tiTCP:5432 -sTCP:LISTEN | xargs -r sudo kill -KILL || true
        sleep 1
      fi
    fi
  fi

  # 3) Validación final
  if port_5432_in_use; then
    log_error "No se pudo liberar el puerto 5432 automáticamente. Revisa: sudo ss -ltnp | grep :5432"
  fi

  log_success "Puerto 5432 liberado correctamente."
  return 0
}

# --- 2. DETECCIÓN DE ENTORNO ---
if docker compose version >/dev/null 2>&1; then
    DOCKER_CMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    DOCKER_CMD="docker-compose"
else
    log_error "No se encontró docker-compose ni docker compose. Instala Docker primero."
fi

require_cmd openssl
require_cmd ss
require_cmd sudo

# --- 2.1 PRE-FLIGHT: PERMISOS DOCKER ---
if ! docker ps >/dev/null 2>&1; then
    log_warn "Docker no es accesible para el usuario actual ($USER)."
    log_warn "Solución recomendada (permanente):"
    log_warn "  sudo usermod -aG docker $USER"
    log_warn "  newgrp docker   (o cerrar sesión y volver a entrar)"
    log_warn "Intentando continuar con sudo para este despliegue..."

    if sudo docker ps >/dev/null 2>&1; then
        DOCKER_CMD="sudo $DOCKER_CMD"
        log_success "Se usará sudo para ejecutar Docker en este despliegue."
    else
        log_error "Docker no está disponible ni con sudo. Verifica que el servicio Docker esté activo."
    fi
fi

# --- 2.2 PRE-FLIGHT: .env (AUTO-CREACIÓN + VALIDACIÓN) ---
ENV_FILE=".env"
ENV_EXAMPLE=".env.example"

if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$ENV_EXAMPLE" ]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        log_warn "No existía $ENV_FILE; se creó automáticamente desde $ENV_EXAMPLE."
        log_warn "Si es un entorno distinto (producción), revisa y ajusta variables en $ENV_FILE."
    else
        log_error "Falta $ENV_FILE y no existe $ENV_EXAMPLE. No se puede continuar."
    fi
fi

set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a

required_vars=(POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB)
for v in "${required_vars[@]}"; do
    if [ -z "${!v:-}" ]; then
        log_error "Variable obligatoria '$v' no está definida o está vacía en $ENV_FILE."
    fi
done
log_success ".env detectado y validado correctamente."

# --- 2.3 PRE-FLIGHT: LIBERAR PUERTO 5432 AUTOMÁTICAMENTE ---
free_port_5432

# --- 3. MODO LIMPIEZA (NUCLEAR OPTION) ---
if [[ "${1:-}" == "--clean" ]]; then
    echo -e "${RED}"
    echo "========================================================"
    echo " ☢️  INICIANDO PROTOCOLO DE LIMPIEZA NUCLEAR  ☢️"
    echo "    SE BORRARÁ TODA LA BASE DE DATOS Y CERTIFICADOS"
    echo "========================================================"
    echo -e "${NC}"

    log_info "Deteniendo contenedores..."
    $DOCKER_CMD down --remove-orphans

    log_info "Eliminando volúmenes persistentes..."
    if [ -d "postgres_data" ]; then
        sudo rm -rf postgres_data
        log_success "Base de datos eliminada (postgres_data)."
    fi

    rm -rf srv-django-backend/certs

    log_info "Limpiando caché de Python..."
    find . -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true

    sleep 2
fi

# --- 4. GENERACIÓN DE SSL (HTTPS) ---
CERT_DIR="srv-django-backend/certs"
if [ ! -f "$CERT_DIR/cert.pem" ]; then
    log_info "Generando certificados SSL auto-firmados para HTTPS..."
    mkdir -p "$CERT_DIR"
    sudo chown -R "$USER:$USER" srv-django-backend/ 2>/dev/null || true

    openssl req -x509 -newkey rsa:4096 \
      -keyout "$CERT_DIR/key.pem" \
      -out "$CERT_DIR/cert.pem" \
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
    log_error "Falló el despliegue de Docker. Revisa los logs: $DOCKER_CMD logs -f"
fi

# --- 6. ESPERA REAL (POSTGRES READY) ---
log_info "Esperando que la Base de Datos (Postgres) esté lista..."

# Nota:
# - En Docker Compose, 'exec' usa el NOMBRE DEL SERVICIO (docker-compose.yml), no el nombre del contenedor.
# - En este proyecto el servicio es: postgres (aunque el contenedor se llame postgres_db).
PG_SERVICE="postgres"

for i in {1..240}; do
    # Puede fallar si el contenedor aún no está listo o si todavía está iniciando; en ambos casos seguimos esperando.
    if $DOCKER_CMD exec -T "$PG_SERVICE" pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
        log_success "Postgres listo para aceptar conexiones."
        break
    fi

    # Evitar abortar prematuramente: después de un --clean es normal que el servicio tarde en pasar a 'running'.
    if (( i % 10 == 0 )); then
        # Mostrar un estado útil cada 10 intentos (sin fallar si el comando aún no entrega info).
        STATUS_LINE="$($DOCKER_CMD ps "$PG_SERVICE" --format '{{.Name}} {{.State}} {{.Status}}' 2>/dev/null | head -n 1 || true)"
        if [ -n "$STATUS_LINE" ]; then
            log_info "Estado Postgres: $STATUS_LINE"
        fi
        log_info "Postgres aún no está listo... ($i/240)"
    fi

    sleep 2

    if [ "$i" -eq 240 ]; then
        log_error "Postgres no estuvo listo a tiempo. Revisa: $DOCKER_CMD logs --tail 200 $PG_SERVICE"
    fi
done

# --- 7. POST-CONFIGURACIÓN (DJANGO) ---
log_info "Aplicando Migraciones (Estructura de Base de Datos)..."
$DOCKER_CMD exec -T srv-django-backend python manage.py makemigrations api
$DOCKER_CMD exec -T srv-django-backend python manage.py migrate --noinput

log_info "Recolectando Archivos Estáticos (CSS/JS)..."
$DOCKER_CMD exec -T srv-django-backend python manage.py collectstatic --noinput

log_info "Verificando Superusuario..."
$DOCKER_CMD exec -T srv-django-backend python manage.py shell -c \
"from django.contrib.auth import get_user_model; User = get_user_model(); \
User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@nuam.cl', 'admin')"
log_success "Usuario Admin asegurado."

log_info "Configurando Corredor por Defecto..."
$DOCKER_CMD exec -T srv-django-backend python manage.py shell -c \
"from api.models import Broker; Broker.objects.get_or_create(name='Corredor Default', code='DEFAULT'); print('Broker Default verificado.')"

log_info "Vinculando Admin con Perfil..."
$DOCKER_CMD exec -T srv-django-backend python manage.py shell -c \
"from django.contrib.auth.models import User; from api.models import UserProfile, Broker; \
u = User.objects.get(username='admin'); b = Broker.objects.get(code='DEFAULT'); \
UserProfile.objects.get_or_create(user=u, defaults={'broker': b}); print('Perfil de Admin vinculado correctamente.')"
log_success "Perfil de Admin configurado correctamente."

# --- 8. PRUEBAS FINALES ---
log_info "Ejecutando Test Unitario de Segregación..."
$DOCKER_CMD exec -T srv-django-backend python manage.py test api

# --- 9. RESUMEN ---
echo ""
echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN}   🚀 SISTEMA NUAM OPERATIVO Y SEGURO (HTTPS)   ${NC}"
echo -e "${GREEN}====================================================${NC}"
echo -e " > 📊 Dashboard:    https://localhost:8000 (Aceptar riesgo SSL)"
echo -e " > ⚙️  Admin Panel:  https://localhost:8000/admin"
echo -e " > 👤 Credenciales: admin / admin"
echo -e ""
echo -e "${YELLOW}[TIP]${NC} Para ver logs en tiempo real: ${BLUE}$DOCKER_CMD logs -f${NC}"
echo ""
