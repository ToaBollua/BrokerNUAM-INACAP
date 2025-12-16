# 🏛️ NUAM Exchange - Sistema de Gestión de Calificaciones Tributarias

![Status](https://img.shields.io/badge/Status-Stable-success)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)
![Python](https://img.shields.io/badge/Python-3.11-yellow?logo=python)
![Django](https://img.shields.io/badge/Django-5.0-green?logo=django)
![Kafka](https://img.shields.io/badge/Kafka-Event--Driven-black?logo=apachekafka)
![Security](https://img.shields.io/badge/Security-Multi--Tenant-red)

> **Infraestructura crítica para la gestión centralizada, segura y asíncrona de datos tributarios en el Holding Bursátil Regional (Chile, Colombia, Perú).**

---

## 📑 Tabla de Contenidos
1. [Descripción del Proyecto](#-descripción-del-proyecto)
2. [Arquitectura de la Solución](#-arquitectura-de-la-solución)
3. [Características Principales](#-características-principales)
4. [Estructura del Proyecto](#-estructura-del-proyecto)
5. [Instalación y Despliegue](#-instalación-y-despliegue)
6. [Guía de Uso](#-guía-de-uso)
7. [Pruebas y QA](#-pruebas-y-qa)
8. [Autores](#-autores)

---

## 📋 Descripción del Proyecto

Este proyecto implementa una arquitectura de **Microservicios Orientada a Eventos (EDA)** para resolver la complejidad operativa en la carga y distribución de calificaciones tributarias.

El sistema reemplaza los procesos manuales propensos a errores con un flujo automatizado que garantiza:
* **Integridad de Datos:** Validación estricta de factores matemáticos.
* **Seguridad:** Aislamiento lógico de datos entre corredores (Multi-tenancy) y auditoría inmutable.
* **Resiliencia:** Desacoplamiento de la ingesta mediante Apache Kafka.
* **Interoperabilidad:** Soporte multi-moneda (CLP, USD, COP, PEN) y exportación estándar (Excel/JSON).

---

## 🏗️ Arquitectura de la Solución

El ecosistema se orquesta mediante **Docker Compose** e integra los siguientes nodos:

| Servicio | Tecnología | Función |
| :--- | :--- | :--- |
| **Backend Core** | Django 5.0 + Gunicorn | API REST, lógica de negocio, cálculo de factores y gestión de usuarios. Sirve HTTPS con certificados OpenSSL. |
| **Bus de Eventos** | Apache Kafka + Zookeeper | Sistema nervioso central. Gestiona el tópico `nuam_events` para desacoplar la carga de datos del procesamiento. |
| **Consumer** | Python Standalone | Worker que escucha Kafka, valida reglas de negocio y persiste en BD usando el ORM de Django. |
| **Notifier** | Python Standalone | Microservicio reactivo (Patrón Fan-out) que simula el envío de alertas en tiempo real a los corredores. |
| **Persistencia** | PostgreSQL 16 | Base de datos relacional transaccional optimizada para JSONB. |

---

## ✨ Características Principales

### 🔒 Seguridad y Compliance
* **HTTPS Nativo:** Cifrado de tráfico mediante `django-extensions` y certificados OpenSSL.
* **Multi-tenancy:** Un corredor jamás puede acceder a los registros de otro. Filtros aplicados a nivel de ORM.
* **Auditoría:** Registro automático de acciones (`AuditLog`) de quién hizo qué y cuándo.

### 📊 Operación Financiera
* **Carga Inteligente:** Formulario manual con validación de factores (<= 1.0) y cálculo automático de JSON.
* **Soporte Regional:** Manejo de monedas locales (CLP, COP, PEN) y Dólar (USD).
* **Reportabilidad:** Exportación de datos propios a Excel (.xlsx) y vista de impresión PDF.

---

## 📂 Estructura del Proyecto

```text
BrokerNUAM-INACAP/
├── README.md                 # Guía de uso/instalación y descripción general del sistema
├── .env.example              # Plantilla de variables de entorno (DB, Django, Kafka, DEBUG, etc.)
├── docker-compose.yml        # Orquestación completa: Postgres + Kafka/Zookeeper + Backend Django + Consumer + Notifier
├── deploy.sh                 # Script maestro: genera SSL, levanta contenedores, мигра BD, collectstatic, crea admin/broker, ejecuta tests
├── locustfile.py             # Pruebas de carga (login + navegación Dashboard y Admin)
├── link.txt                  # Enlace a documentación externa (presentación/entregable)
├── package-lock.json         # Artefacto Node (placeholder); no es núcleo del backend Python/Django
│
├── srv-django-backend/       # Servicio principal (Django): UI + lógica de negocio + persistencia
│   ├── Dockerfile            # Imagen del backend (Python + dependencias + gunicorn)
│   ├── requirements.txt      # Dependencias (Django, dj-database-url, Jazzmin, WhiteNoise, import-export, etc.)
│   ├── manage.py             # CLI Django (migrate, createsuperuser, collectstatic, etc.)
│   │
│   ├── nuam/                 # Configuración del proyecto Django (settings, urls, wsgi/asgi)
│   │   ├── settings.py       # Config por variables de entorno (DB vía DATABASE_URL, estáticos, Jazzmin, login redirects, etc.)
│   │   ├── urls.py           # Enrutamiento principal del proyecto
│   │   ├── wsgi.py / asgi.py # Entrypoints para servidores WSGI/ASGI
│   │   └── __init__.py
│   │
│   ├── api/                  # App de negocio (core): multi-tenancy, modelos, vistas, formularios, exportación
│   │   ├── models.py         # Entidades clave: Broker (tenant), UserProfile (asignación), TaxQualification, AuditLog
│   │   ├── views.py          # Dashboard segregado, ingreso manual, carga CSV, exportación XLSX, auditoría
│   │   ├── forms.py          # Formularios con validaciones y armado de payload JSON (financial_data)
│   │   ├── resources.py      # Exportador XLSX (django-import-export) para TaxQualification
│   │   ├── urls.py           # Rutas del módulo (home, upload-csv, export, entry/manual, etc.)
│   │   ├── admin.py          # Registro y configuración de modelos en Django Admin
│   │   └── migrations/       # Versionado del esquema de BD (evolución de modelos)
│   │
│   ├── templates/            # Vistas HTML (UI): login, dashboard, formularios de carga/ingreso
│   │   ├── base.html         # Layout base (estructura común)
│   │   ├── index.html        # Dashboard principal
│   │   ├── login.html        # Autenticación
│   │   ├── manual_entry.html # Formulario de ingreso manual
│   │   └── upload_csv.html   # Carga masiva por CSV
│   │
│   ├── static/               # Recursos estáticos (CSS/JS)
│   │   └── css/base.css      # Estilos base de la interfaz
│   │
│   └── certs/                # Certificados SSL locales (auto-firmados; generados/gestionados por deploy.sh)
│       ├── cert.pem
│       └── key.pem
│
├── srv-kafka-consumer/       # Microservicio de ingesta: consume eventos Kafka y persiste en Postgres vía ORM Django
│   ├── Dockerfile            # Imagen del consumidor (incluye dependencias para Postgres/Kafka)
│   ├── requirements.txt      # Dependencias (confluent-kafka, Django, dj-database-url, etc.)
│   ├── consumer.py           # Suscriptor a tópico 'nuam_events': upsert de TaxQualification + creación de AuditLog
│   └── simulate_bolsa.py     # Generador de eventos de ejemplo hacia Kafka (simulación “bolsa”)
│
└── srv-notifier/             # Microservicio de notificación: lee eventos Kafka y ejecuta acción (simulada)
    ├── Dockerfile            # Imagen liviana (confluent-kafka)
    └── main.py               # Consumer del tópico 'nuam_events' (simula envío de email/alerta)
````


## 🚀 Instalación y Despliegue

### Prerrequisitos

  * Docker y Docker Compose.
  * Python 3.11+ (opcional, para scripts locales).
  * OpenSSL (para generar certificados).

### Obtener el Repositorio

Antes de comenzar, clona el proyecto y entra en el directorio:

```bash
git clone https://github.com/ToaBollua/BrokerNUAM-INACAP #URL del repositorio
cd BrokerNUAM-INACAP #Nombre del directorio
```

### Opción A: Despliegue Automático (Recomendado)

El script `deploy.sh` se encarga de limpiar, construir, migrar y crear usuarios.

```bash
# Dar permisos de ejecución
chmod +x deploy.sh

# Despliegue limpio (Borra BD anterior y regenera todo)
./deploy.sh --clean
```

### Opción B: Despliegue Manual con Docker Compose

Si necesita integrar esto en un pipeline CI/CD o instalar manualmente:

1.  **Generar Certificados SSL:**

    ```bash
    mkdir -p srv-django-backend/certs
    openssl req -x509 -newkey rsa:4096 -keyout srv-django-backend/certs/key.pem -out srv-django-backend/certs/cert.pem -days 365 -nodes -subj "/C=CL/ST=Santiago/L=Macul/O=NUAM/OU=IT/CN=localhost"
    ```

2.  **Levantar Infraestructura:**

    ```bash
    docker-compose up --build -d
    ```

3.  **Inicializar Base de Datos:**

    ```bash
    docker-compose exec srv-django-backend python manage.py migrate
    docker-compose exec srv-django-backend python manage.py createsuperuser
    ```

-----

## 🖥️ Guía de Uso

### 1\. Acceso al Dashboard

  * **URL:** `https://localhost:8000/` (Acepte la advertencia de certificado autofirmado).
  * **Credenciales:** `admin` / `admin` (o las creadas en el despliegue).

### 2\. Simulación de Bolsa (Kafka)

Para inyectar datos de mercado simulados y ver el flujo asíncrono:

```bash
# Ejecutar desde la raíz del proyecto
python srv-kafka-consumer/simulate_bolsa.py
```

*Observe cómo el Dashboard se actualiza y el servicio Notifier imprime alertas en la consola.*

### 3\. Exportación y Reportes

En el Dashboard, utilice los botones superiores para descargar la nómina de calificaciones en formato Excel o imprimir la vista oficial.

-----

## 🧪 Pruebas y QA

### Tests Unitarios (Integridad)

Valida que el aislamiento de datos entre corredores funcione matemáticamente.

```bash
docker-compose exec srv-django-backend python manage.py test api
```

### Pruebas de Carga (Locust)

Simula 100+ usuarios concurrentes bombardeando el sistema.

```bash
python -m locust -f locustfile.py
# Acceda a http://localhost:8089
```

-----

## 👥 Autores

Proyecto desarrollado para la asignatura de Programación Back End.

  * **Nicolás Anrique** - *Lead Architect & Backend*
  * **Diego Ibeas** - *DevOps & Infrastructure*
  * **Camilo Nuñez** - *Frontend & QA*

### 🤖 Agradecimientos

  * **H0P3 AI** - *Asistencia Técnica, Debugging y Copiloto de Arquitectura.*

-----

*© 2025 NUAM Exchange. Infraestructura Confidencial.*

```
```
