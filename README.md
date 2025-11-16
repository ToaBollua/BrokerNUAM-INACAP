# Proyecto: Mantenedor de Calificaciones NUAM

## Descripción

Sistema de mantenedor de calificaciones tributarias desarrollado en Django 5.2, utilizando PostgreSQL como base de datos.

## Requisitos Previos (Generales)

* Python 3.11+
* `python-venv` (o `python3-venv`)
* PostgreSQL (Servicio local instalado y corriendo)

---

## Instalación Automatizada (Linux / Arch)

### 1. Requisitos (Arch Linux)

```bash
sudo pacman -Syu postgresql python-venv
```

### 2. Configuración de PostgreSQL (Arch)

Asegúrate de que el servicio de PostgreSQL esté iniciado y habilitado:

```bash
# Inicializa la base de datos (solo si es la primera vez)
sudo -u postgres initdb --locale $LANG -E UTF8 -D /var/lib/postgres/data

# Inicia y habilita el servicio
sudo systemctl enable --now postgresql
```

### 3. Ejecución del Script (Arch)

Este script (`setup-arch.sh`) configurará la BD, el `venv`, instalará dependencias, creará el `.env` y las migraciones, y generará un superusuario (`admin`/`admin`).

```bash
# 1. Da permisos de ejecución al script
chmod +x setup-arch.sh

# 2. Ejecuta el script (requerirá tu contraseña de sudo para Postgres)
./setup.sh
```

---

## Instalación Automatizada (Linux / Debian / Ubuntu)

### 1. Requisitos (Debian/Ubuntu)

```bash
sudo apt-get update
sudo apt-get install -y postgresql postgresql-client python3-venv
```

### 2. Configuración de PostgreSQL (Debian)

El servicio debería iniciarse automáticamente tras la instalación.

```bash
# Verifica que el servicio esté corriendo
sudo systemctl enable --now postgresql
```

### 3. Ejecución del Script (Debian)

Este script (`setup-debian.sh`) configurará la BD, el `venv`, instalará dependencias, creará el `.env` y las migraciones, y generará un superusuario (`admin`/`admin`).

```bash
# 1. Da permisos de ejecución al script
chmod +x setup-debian.sh

# 2. Ejecuta el script (requerirá tu contraseña de sudo para Postgres)
./setup-debian.sh
```

---

## Instalación Automatizada (Windows / PowerShell)

### 1. Requisitos (Windows)

1.  Haber instalado **Python 3.11+** (asegúrate de que `python` esté en tu `PATH`).
2.  Haber instalado **PostgreSQL** (ej. con el instalador de EDB) y asegurarte de que los binarios (`psql`, `createuser`) estén en tu `PATH` del sistema.
3.  Tener el servicio de PostgreSQL corriendo.

### 2. Configuración de PowerShell

**A. Política de Ejecución:**
PowerShell bloquea los scripts por defecto. Debes permitir la ejecución de scripts locales. Abre PowerShell *como Administrador* y ejecuta:

```powershell
Set-ExecutionPolicy RemoteSigned
# (Presiona 'Y' o 'A' para aceptar)
```

**B. Contraseña de Administrador de Postgres:**
El script necesita la contraseña de tu superusuario `postgres` (la que definiste al instalar PostgreSQL). Abre una terminal normal de PowerShell y establécela como una variable de entorno temporal:

```powersV
# Reemplaza 'tu_contraseña' por tu contraseña real
$env:PGPASSWORD = "tu_contraseña_de_postgres"
```

### 3. Ejecución del Script (Windows)

En la misma terminal donde estableciste `PGPASSWORD`, ejecuta el script de PowerShell:

```powershell
.\setup.ps1
```

---

## Ejecución (Todos los Sistemas)

Una vez finalizada la instalación:

```bash
# 1. Activa el entorno virtual
# (Linux/Mac)
source venv/bin/activate
# (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# 2. Inicia el servidor
python manage.py runserver
```

## Acceso

* **Aplicación:** `http://127.0.0.1:8000/`
* **Admin:** `http://127.0.0.1:8000/admin/`
* **Superusuario:** `admin`
* **Contraseña:** `admin`