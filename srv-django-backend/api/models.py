from django.db import models
from django.contrib.auth.models import User

class Broker(models.Model):
    """El 'Tenant' o Corredor (Entidad Financiera)."""
    name = models.CharField(max_length=255, unique=True, verbose_name="Nombre Corredor")
    code = models.CharField(max_length=50, unique=True, verbose_name="Código Bolsa")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Corredor"
        verbose_name_plural = "Corredores"

class UserProfile(models.Model):
    """Extensión del usuario para asociarlo a un Broker (Seguridad Multi-tenant)."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuario Sistema")
    broker = models.ForeignKey(Broker, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Corredor Asociado")

    def __str__(self):
        broker_name = self.broker.name if self.broker else "Sin Asignar"
        return f"{self.user.username} - {broker_name}"

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"

class TaxQualification(models.Model):
    """La Calificación Tributaria (El núcleo del negocio)."""
    
    # --- CONSTANTES DE NEGOCIO (NUAM REGIONAL) ---
    CURRENCY_CHOICES = [
        ('CLP', 'CLP - Peso Chileno'),
        ('COP', 'COP - Peso Colombiano'),
        ('PEN', 'PEN - Sol Peruano'),
        ('USD', 'USD - Dólar Estadounidense'),
    ]

    SOURCE_CHOICES = [
        ('MANUAL', 'Ingreso Manual (Operador)'),
        ('CSV', 'Carga Masiva (Archivo)'),
        ('API', 'Integración Bolsa (Automático)'),
    ]

    # Relaciones y Datos Generales
    broker = models.ForeignKey(Broker, on_delete=models.CASCADE, related_name='qualifications', verbose_name="Corredor")
    instrument = models.CharField(max_length=120, verbose_name="Instrumento / Nemotécnico")
    payment_date = models.DateField(verbose_name="Fecha de Pago")
    exercise_year = models.IntegerField(verbose_name="Año Ejercicio")
    
    # --- NUEVO: MONEDA ---
    currency = models.CharField(
        max_length=3, 
        choices=CURRENCY_CHOICES, 
        default='CLP',
        verbose_name="Moneda"
    )

    # --- DATOS FINANCIEROS (JSON POWER) ---
    # Aquí guardamos Monto Base, Factores, Créditos, etc.
    # Eliminamos 'amounts' y 'factors' separados para usar una sola fuente de verdad.
    financial_data = models.JSONField(
        default=dict, 
        blank=True, 
        null=True, 
        verbose_name="Datos Financieros (JSON)"
    )
    
    source = models.CharField(
        max_length=50, 
        choices=SOURCE_CHOICES, # <--- ESTO CONECTA EL DROPDOWN
        default='MANUAL', 
        verbose_name="Origen Dato"
    )

    # Auditoría interna del registro
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")

    class Meta:
        # Evita duplicados: Un broker no puede tener dos registros para el mismo instrumento en la misma fecha
        unique_together = ('broker', 'instrument', 'payment_date')
        verbose_name = "Calificación Tributaria"
        verbose_name_plural = "Calificaciones Tributarias"
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.instrument} ({self.currency}) - {self.exercise_year}"

class AuditLog(models.Model):
    """El Ojo que Todo lo Ve (Trazabilidad Inmutable)."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Operador")
    action = models.CharField(max_length=50, verbose_name="Acción Realizada") # LOGIN, EXPORT, CREATE
    details = models.TextField(verbose_name="Detalles Técnicos")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Marca de Tiempo")

    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.action}"

    class Meta:
        verbose_name = "Log de Auditoría"
        verbose_name_plural = "Logs de Auditoría"
        ordering = ['-timestamp']