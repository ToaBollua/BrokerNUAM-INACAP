# NUAM Exchange - Sistema de Gestión de Calificaciones Tributarias

## 📋 Descripción del Proyecto
Este proyecto implementa una solución de **Arquitectura de Microservicios** para la gestión, procesamiento y auditoría de Calificaciones Tributarias del holding NUAM.

El sistema permite la ingesta de datos financieros (vía carga manual o eventos asíncronos), el cálculo de factores tributarios, la segregación de datos por cliente (Multi-tenancy) y la notificación proactiva de eventos, cumpliendo con estándares de alta disponibilidad, seguridad y desacoplamiento.

## 🏗️ Arquitectura de la Solución

El sistema está orquestado mediante **Docker Compose** y se compone de los siguientes nodos:

### 1. Backend Core (`srv-django-backend`)
* **Tecnología:** Python 3.11, Django 5.0.
* **Función:** API REST, lógica de negocio, cálculo de factores, gestión de usuarios y panel de administración (Jazzmin).
* **Seguridad:** Implementa aislamiento de datos por `Broker` (Corredor). Un corredor no puede ver los datos de otro.
* **Servidor:** Gunicorn + WhiteNoise (para gestión eficiente de archivos estáticos).

### 2. Bus de Eventos (`kafka` + `zookeeper`)
* **Tecnología:** Apache Kafka 7.4 (Confluent), Zookeeper.
* **Función:** Columna vertebral de comunicación asíncrona. Desacopla la ingesta de datos del procesamiento para garantizar resiliencia.

### 3. Consumidor de Persistencia (`srv-kafka-consumer`)
* **Tecnología:** Python Standalone.
* **Función:** Escucha el tópico `nuam_events`. Procesa los mensajes entrantes, valida la existencia del corredor y persiste la calificación en la base de datos PostgreSQL utilizando el ORM de Django inyectado.

### 4. Servicio de Notificaciones (`srv-notifier`)
* **Tecnología:** Python Standalone.
* **Función:** Microservicio reactivo (Patrón Fan-out). Escucha el mismo tópico `nuam_events` y simula el envío de correos electrónicos de alerta a los corredores afectados.

### 5. Persistencia (`postgres`)
* **Tecnología:** PostgreSQL 16.
* **Función:** Almacenamiento relacional transaccional para usuarios, calificaciones y logs de auditoría.

---

## 🚀 Instalación y Despliegue Automatizado

Este proyecto incluye un script de despliegue (`deploy.sh`) que automatiza la construcción, migración y configuración del entorno.

### Prerrequisitos
* Docker y Docker Compose instalados.
* Python 3.x (para ejecutar scripts de simulación localmente).

### Despliegue Rápido
Para levantar el entorno completo, ejecute el script maestro:

```bash
# Dar permisos de ejecución
chmod +x deploy.sh

# Opción 1: Despliegue estándar (Mantiene datos existentes)
./deploy.sh

# Opción 2: Despliegue Nuclear (Borra base de datos y comienza desde cero - Recomendado para primera vez)
./deploy.sh --clean
````

El script se encargará de:

1.  Limpiar volúmenes corruptos (si se usa `--clean`).
2.  Construir los contenedores.
3.  Esperar a que la Base de Datos esté disponible.
4.  Aplicar migraciones y recolectar estáticos.
5.  Crear un Superusuario por defecto (`admin` / `admin`).
6.  Ejecutar pruebas unitarias de integridad.

-----

## 🖥️ Uso del Sistema

### 1\. Panel de Administración y Dashboard

Acceda a la interfaz web:

  * **URL:** `http://localhost:8000/`
  * **Login:** Use las credenciales `admin` / `admin`.
  * **Funcionalidades:**
      * **Dashboard Operativo:** Visualización de calificaciones y logs filtrados por Corredor.
      * **Carga Masiva:** Ingesta de archivos CSV.
      * **Panel Admin (`/admin`):** Gestión avanzada de Usuarios y creación de Brokers (Tenants) con interfaz Jazzmin.

### 2\. Simulación de Eventos de Bolsa (Kafka)

Para probar la integración asíncrona, se incluye un script productor que simula el envío de datos desde la Bolsa de Comercio.

**Requisito:** Instalar librería cliente localmente:

```bash
pip install confluent-kafka
```

**Ejecución:**

```bash
# Asegúrese de tener "127.0.0.1 kafka" en su /etc/hosts o usar localhost
python srv-kafka-consumer/simulate_bolsa.py
```

*Resultado:* Los datos aparecerán automáticamente en el Dashboard y se enviarán notificaciones por consola en el servicio `srv-notifier`.

### 3\. Pruebas de Carga (Locust)

Para validar la resiliencia del sistema bajo estrés:

```bash
# Iniciar Locust
python -m locust -f locustfile.py
```

Acceda a `http://localhost:8089` para configurar el enjambre de usuarios.

-----

## 🧪 Pruebas Unitarias

El proyecto incluye tests automatizados para validar la segregación de datos (Multi-tenancy):

```bash
docker-compose exec srv-django-backend python manage.py test api
```

-----

## 🛠️ Tecnologías y Librerías Clave

  * **Backend:** Django 5.0, Gunicorn.
  * **Frontend/Admin:** Django Templates, Jazzmin, WhiteNoise.
  * **Mensajería:** Confluent Kafka.
  * **Base de Datos:** PostgreSQL.
  * **Infraestructura:** Docker, Docker Compose.
  * **QA/Testing:** Locust, Django Test Framework.

-----

## 👥 Autores

  * **Nicolás Anrique**
  * **Diego Ibeas**
  * **Camilo Nuñez**
  
### Agradecimientos Especiales

  * **H0P3** - *Asistencia Técnica & IA Copilot*

<!-- end list -->
