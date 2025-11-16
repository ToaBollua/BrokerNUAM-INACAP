#!/bin/bash

# setup-arch.sh (Corregido)
# Script de instalación automatizado para el Mantenedor NUAM (Sistemas Arch).
# Asume que se ejecuta desde la raíz 'BrokerNUAM-INACAP', NO desde 'brokernuam/'.

# --- 1. Configuración de PostgreSQL ---
echo "--- 1. Configurando PostgreSQL ---"
if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='mantenedor_user'" | grep -q 1; then
    echo "Usuario 'mantenedor_user' ya existe. Omitiendo creación de usuario."
else
    sudo -u postgres createuser mantenedor_user
    echo "Usuario 'mantenedor_user' creado."
fi
echo "Estableciendo contraseña y permisos para 'mantenedor_user'..."
sudo -u postgres psql -c "ALTER USER mantenedor_user WITH PASSWORD 'mantenedor_pass';"
sudo -u postgres psql -c "ALTER USER mantenedor_user CREATEDB;"
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw 'mantenedor_db'; then
    echo "Base de datos 'mantenedor_db' ya existe. Omitiendo creación de BD."
else
    sudo -u postgres createdb -O mantenedor_user mantenedor_db
    echo "Base de datos 'mantenedor_db' creada."
fi

# --- 2. Configuración del Entorno Python ---
echo "--- 2. Configurando Entorno Python (venv) ---"
if [ -d "venv" ]; then
    echo "'venv' ya existe. Reutilizando."
else
    python -m venv venv
    echo "'venv' creado."
fi
echo "Activando venv e instalando dependencias..."
source venv/bin/activate
pip install -r requirements.txt

# --- 3. Creación del archivo .env (Ruta Corregida) ---
echo "--- 3. Creando archivo .env en brokernuam/ ---"
cat <<EOF > brokernuam/.env
DATABASE_URL=postgres://mantenedor_user:mantenedor_pass@localhost:5432/mantenedor_db
DJANGO_SETTINGS_MODULE=brokernuam.settings
SECRET_KEY='local-debug-key-insecure'
DEBUG=True
EOF
echo ".env creado exitosamente."

# --- 4. Aplicando Migraciones (Ruta Corregida) ---
echo "--- 4. Aplicando Migraciones de Base de Datos ---"
cd brokernuam/  # <--- CORRECCIÓN: Entrar al directorio
python manage.py migrate
cd ..           # <--- CORRECCIÓN: Salir

# --- 5. Creación de Superusuario (Ruta Corregida) ---
echo "--- 5. Creando Superusuario (admin/admin) ---"
cd brokernuam/  # <--- CORRECCIÓN: Entrar al directorio
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@nuam.com', 'admin')" | python manage.py shell
cd ..           # <--- CORRECCIÓN: Salir
echo "Superusuario 'admin' con contraseña 'admin' creado/verificado."

# --- 6. Finalización (Instrucciones Corregidas) ---
echo "--- Instalación Completa ---"
echo "Para iniciar el servidor, activa el entorno virtual:"
echo "source venv/bin/activate"
echo "...luego entra al directorio del proyecto:"
echo "cd brokernuam"
echo "...y finalmente ejecuta:"
echo "python manage.py runserver"