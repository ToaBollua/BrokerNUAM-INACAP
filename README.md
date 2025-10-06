# Mantenedor de Calificaciones Tributarias - NUAM

Este proyecto es una aplicación Django que implementa un mantenedor de calificaciones tributarias para NUAM, permitiendo a los corredores gestionar calificaciones tributarias de manera segura y eficiente.

## Características

- **Multi-tenancy**: Datos segregados por corredor, con datos de bolsa como base.
- **Gestión CRUD**: Crear, leer, actualizar y eliminar calificaciones.
- **Carga Masiva**: Importar calificaciones desde archivos CSV (montos o factores).
- **Cálculo de Factores**: Conversión automática de montos a factores tributarios.
- **Auditoría**: Registro de todas las operaciones para cumplimiento normativo.
- **Interfaz Web**: Frontend simple con Bootstrap.
- **Autenticación**: Sistema de login requerido.

## Requisitos

- Python 3.8+
- Django 5.2+
- Base de datos: SQLite (por defecto), escalable a PostgreSQL/Oracle

## Instalación

1. Clona el repositorio:
   ```
   git clone <url-del-repositorio>
   cd BrokerNUAM-INACAP
   ```

2. Activa el entorno virtual (ya configurado):
   ```
   .\venv\Scripts\activate  # En Windows
   # o
   source venv/bin/activate  # En Linux/Mac
   ```

3. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

4. Ejecuta las migraciones:
   ```
   cd brokernuam
   python manage.py makemigrations
   python manage.py migrate
   ```

5. Crea un superusuario:
   ```
   python manage.py createsuperuser
   ```

6. Ejecuta el servidor:
   ```
   python manage.py runserver
   ```

7. Accede a la aplicación en http://127.0.0.1:8000/

## Uso

### Autenticación
- Inicia sesión con tu usuario y contraseña.
- Los datos se segregan por corredor.

### Funcionalidades Principales
- **Lista de Calificaciones**: Visualiza y filtra calificaciones.
- **Crear Calificación**: Proceso de 3 pasos (datos básicos, montos, factores).
- **Actualizar/Eliminar**: Modifica o borra calificaciones existentes.
- **Carga Masiva**: Sube archivos CSV para importar múltiples calificaciones.

### Formato CSV para Carga Masiva
- Columnas: mercado, instrumento, fecha_pago, ejercicio, amount1, amount2, ..., amount29 (para montos)
- O: mercado, instrumento, fecha_pago, ejercicio, factor1, factor2, ..., factor29 (para factores)

## Arquitectura

- **Backend**: Django con vistas basadas en clases y funciones.
- **Frontend**: Templates HTML con Bootstrap.
- **Base de Datos**: Modelo relacional con JSON para montos/factores.
- **Seguridad**: Autenticación Django, multi-tenancy por corredor.

## Desarrollo

- El cálculo de factores es un placeholder; implementar lógica real basada en homologaciones del documento.
- Datos de bolsa deben cargarse manualmente o vía admin.

## Contribución

1. Crea una rama para tu feature.
2. Realiza commits descriptivos.
3. Envía un pull request.

## Licencia

[Especificar licencia si aplica]
