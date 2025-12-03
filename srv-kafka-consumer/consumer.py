import os
import sys
import time
import json
import django
from confluent_kafka import Consumer, KafkaError

# --- H0P3: INICIALIZACIÓN DEL SISTEMA NERVIOSO DE DJANGO ---
# Esto permite usar el ORM de Django desde este script externo
sys.path.append('/app/backend') 
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nuam.settings")
django.setup()

# Ahora sí podemos importar los modelos
from api.models import TaxQualification, Broker, AuditLog, User
from django.db import transaction

# Configuración Kafka
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
TOPIC = 'nuam_events' # El tópico que escuchamos

def process_message(data):
    """
    Lógica de Negocio: Transforma el JSON de Kafka en registros de BD.
    """
    try:
        # data espera formato: 
        # {"broker_code": "CLI01", "instrument": "APPLE", "date": "2025-12-01", "year": 2025, "amount": 100.50}
        
        print(f"🔧 Procesando datos: {data}")

        # 1. Identificar al Corredor (Si no existe, fallamos o creamos uno default)
        broker_code = data.get('broker_code')
        try:
            broker = Broker.objects.get(code=broker_code)
        except Broker.DoesNotExist:
            print(f"⚠️ Error: Corredor {broker_code} no existe. Ignorando.")
            return

        # 2. Crear o Actualizar la Calificación
        # Usamos update_or_create para evitar duplicados
        qual, created = TaxQualification.objects.update_or_create(
            broker=broker,
            instrument=data.get('instrument'),
            payment_date=data.get('date'),
            defaults={
                'exercise_year': data.get('year'),
                'source': 'KAFKA', # Marcamos el origen
                'amounts': {'incoming_amount': data.get('amount')}, # Guardamos en el JSONField
                'factors': {} # Se calcularán después
            }
        )

        action = "CREATED" if created else "UPDATED"
        print(f"✅ Calificación {action}: {qual.instrument} para {broker.name}")

        # 3. Generar Auditoría (El Ojo que todo lo ve)
        # Asignamos al usuario 'system' o admin si no hay usuario real
        system_user = User.objects.filter(is_superuser=True).first()
        
        AuditLog.objects.create(
            user=system_user,
            action=f"KAFKA_{action}",
            details=f"Procesado evento externo para {qual.instrument}. Monto: {data.get('amount')}"
        )

    except Exception as e:
        print(f"🔥 Error procesando mensaje: {e}")

def start_consumer():
    print("⏳ H0P3 Consumer: Esperando alineación de planetas (Kafka)...")
    time.sleep(15) # Damos tiempo a que Kafka arranque bien

    conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'nuam_backend_group',
        'auto.offset.reset': 'earliest'
    }

    consumer = Consumer(conf)
    consumer.subscribe([TOPIC])

    print(f"🟢 H0P3 Consumer ONLINE. Escuchando: {TOPIC}")

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue

            # Decodificar mensaje
            raw_data = msg.value().decode('utf-8')
            try:
                json_data = json.loads(raw_data)
                # Ejecutar transacción atómica
                with transaction.atomic():
                    process_message(json_data)
            except json.JSONDecodeError:
                print(f"🗑️ Mensaje basura recibido (No JSON): {raw_data}")

    except KeyboardInterrupt:
        print("🛑 Deteniendo consumidor...")
    finally:
        consumer.close()

if __name__ == '__main__':
    start_consumer()