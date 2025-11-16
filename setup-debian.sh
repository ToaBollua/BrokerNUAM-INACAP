#!/bin/bash

# setup-debian.sh
# Script de instalación automatizado para el Mantenedor NUAM (Sistemas Debian/Ubuntu).

# --- 1. Instalación de Dependencias del Sistema ---
echo "--- 1. Instalando dependencias (apt) ---"
sudo apt-get update
sudo apt-get install -y postgresql postgresql-client python3-venv

# --- 2. Configuración de PostgreSQL ---
echo "--- 2. Configurando PostgreSQL ---"

# Iniciar y habilitar el servicio (systemd)
sudo systemctl enable --now postgresql

# Comprueba si el usuario 'mantenedor_user' existe
if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='mantenedor_user'" | grep -q 1; then
    echo "Usuario 'mantenedor_user' ya existe. Omitiendo creación de usuario."
else
    sudo -u postgres createuser mantenedor_user
    echo "Usuario 'mantenedor_user' creado."
fi

# Establece/restablece la contraseña y los permisos (esto es seguro ejecutarlo varias veces)
echo "Estableciendo contraseña y permisos para 'mantenedor_user'..."
sudo -u postgres psql -c "ALTER USER mantenedor_user WITH PASSWORD 'mantenedor_pass';"
sudo -u postgres psql -c "ALTER USER mantenedor_user CREATEDB;" # Permiso para crear DBs de test

# Comprueba si la base de datos 'mantenedor_db' existe
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw 'mantenedor_db'; then
    echo "Base de datos 'mantenedor_db' ya existe. Omitiendo creación de BD."
else
    sudo -u postgres createdb -O mantenedor_user mantenedor_db
    echo "Base de datos 'mantenedor_db' creada."
fi

# --- 3. Configuración del Entorno Python ---
echo "--- 3. Configurando Entorno Python (venv) ---"

if [ -d "venv" ]; then
    echo "'venv' ya existe. Omitiendo."
else
    python3 -m venv venv
    echo "'venv' creado."
fi

echo "Activando venv e instalando dependencias..."
source venv/bin/activate
pip install -r requirements.txt

# --- 4. Creación del archivo .env ---
echo "--- 4. Creando archivo .env ---"
cat <<EOF > .env
DATABASE_URL=postgres://mantenedor_user:mantenedor_pass@localhost:5432/mantenedor_db
DJANGO_SETTINGS_MODULE=brokernuam.settings
SECRET_KEY='local-debug-key-insecure'
DEBUG=True
EOF
echo ".env creado exitosamente."

# --- 5. Ejecución de Migraciones ---
echo "--- 5. Aplicando Migraciones de Base de Datos ---"
python manage.py migrate

# --- 6. Creación de Superusuario (No interactivo) ---
echo "--- 6. Creando Superusuario (admin/admin) ---"
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@nuam.com', 'admin')" | python manage.py shell
echo "Superusuario 'admin' con contraseña 'admin' creado/verificado."

# --- 7. Finalización ---
echo "--- Instalación Completa ---"
echo "Para iniciar el servidor, activa el entorno virtual:"
echo "source venv/bin/activate"
echo "...y luego ejecuta:"
echo "python manage.py runserver"