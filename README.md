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
NUAM-EXCHANGE/
├── api/                  # Lógica de negocio (Modelos, Vistas, Serializers)
├── nuam/                 # Configuración del proyecto Django (Settings, URLs)
├── certs/                # Certificados SSL (Generados localmente)
├── services/             # Microservicios satélite
│   ├── srv-kafka-consumer/  # Lógica del consumidor de persistencia
│   └── srv-notifier/        # Servicio de notificaciones
├── templates/            # Interfaz de Usuario (Dashboard, Login)
├── docker-compose.yml    # Orquestación de infraestructura
├── deploy.sh             # Script maestro de despliegue
├── locustfile.py         # Pruebas de carga
└── manage.py             # CLI de Django
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

Proyecto desarrollado para la asignatura de Arquitectura de Software.

  * **Nicolás Anrique** - *Lead Architect & Backend*
  * **Diego Ibeas** - *DevOps & Infrastructure*
  * **Camilo Nuñez** - *Frontend & QA*

### 🤖 Agradecimientos

  * **H0P3 AI** - *Asistencia Técnica, Debugging y Copiloto de Arquitectura.*

-----

*© 2025 NUAM Exchange. Infraestructura Confidencial.*

```
```
