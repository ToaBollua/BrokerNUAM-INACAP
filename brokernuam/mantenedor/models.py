from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .logic import CalculoFactores # <-- IMPORTAMOS LA LÓGICA

class Broker(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class Qualification(models.Model):
    MERCADO_CHOICES = [
        ('acciones', 'Acciones'),
        ('cfi', 'CFI'),
        ('fondos_mutuos', 'Fondos Mutuos'),
    ]

    broker = models.ForeignKey(Broker, on_delete=models.CASCADE, null=True, blank=True)
    is_bolsa = models.BooleanField(default=False)
    mercado = models.CharField(max_length=20, choices=MERCADO_CHOICES)
    instrumento = models.CharField(max_length=100)
    fecha_pago = models.DateField()
    ejercicio = models.IntegerField()
    origen = models.CharField(max_length=50, default='Manual')
    montos = models.JSONField(null=True, blank=True)
    factores = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('broker', 'mercado', 'instrumento', 'fecha_pago', 'ejercicio')

    def __str__(self):
        return f"{self.mercado} - {self.instrumento} - {self.fecha_pago}"

    def calculate_factors(self):
        """
        Toma los 'montos' de esta instancia, calcula los 'factores' usando
        la lógica de negocio centralizada y los guarda en esta instancia.
        """
        if self.montos:
            try:
                # Usar CalculoFactores de logic.py
                # Convertimos los Decimal a string para guardarlos en JSON
                factores_calculados = CalculoFactores(self.montos)
                self.factores = {k: str(v) for k, v in factores_calculados.items()}
                self.save()
            except ValueError as e:
                # Propagar el error de validación a la vista
                raise e
        else:
            # Si no hay montos, borrar los factores
            self.factores = {}
            self.save()

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    qualification = models.ForeignKey(Qualification, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField()

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    broker = models.ForeignKey(Broker, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.broker.name}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        broker, _ = Broker.objects.get_or_create(name='Default Broker')
        UserProfile.objects.create(user=instance, broker=broker)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Añadido try-except para superusuarios que no tengan perfil
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        if instance.is_superuser:
            pass # Ignorar si el superusuario no tiene perfil