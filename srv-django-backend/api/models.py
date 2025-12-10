from django.db import models
from django.contrib.auth.models import User

class Broker(models.Model):
    """El 'Tenant' o Corredor."""
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    """Extensión del usuario para asociarlo a un Broker."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    broker = models.ForeignKey(Broker, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.broker}"

class TaxQualification(models.Model):
    """La Calificación Tributaria (El núcleo del negocio)."""
    broker = models.ForeignKey(Broker, on_delete=models.CASCADE, related_name='qualifications')
    instrument = models.CharField(max_length=120)
    payment_date = models.DateField()
    exercise_year = models.IntegerField()
    
    # Guardamos los 29 montos y factores como JSON para flexibilidad
    # (o podrías crear 29 campos si te gusta sufrir, pero JSONField es más 'cyberpunk')
    amounts = models.JSONField(default=dict) 
    factors = models.JSONField(default=dict)
    
    financial_data = models.JSONField(default=dict, blank=True, null=True, verbose_name="Datos Financieros (JSON)")
    source = models.CharField(max_length=50, default='MANUAL') # MANUAL, CSV_MONTOS, CSV_FACTORES
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('broker', 'instrument', 'payment_date')

class AuditLog(models.Model):
    """El Ojo que Todo lo Ve (Trazabilidad)."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50) # LOGIN, UPLOAD, UPDATE
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.timestamp}] {self.user}: {self.action}"