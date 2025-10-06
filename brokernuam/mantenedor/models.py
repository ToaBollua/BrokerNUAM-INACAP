from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Broker(models.Model):
    name = models.CharField(max_length=100, unique=True)
    # Add other fields as needed, e.g., contact info

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
    origen = models.CharField(max_length=50, default='Manual')  # e.g., 'Manual', 'Carga Masiva - Montos', etc.
    montos = models.JSONField(null=True, blank=True)  # dict with keys 'amount1' to 'amount29'
    factores = models.JSONField(null=True, blank=True)  # dict with keys 'factor1' to 'factor29'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('broker', 'mercado', 'instrumento', 'fecha_pago', 'ejercicio')  # Assuming unique key

    def __str__(self):
        return f"{self.mercado} - {self.instrumento} - {self.fecha_pago}"

    def calculate_factors(self):
        # Placeholder for calculation logic
        # Based on document, convert montos to factores
        # For now, assume some simple logic or placeholder
        if self.montos:
            # Example: factor_i = amount_i / 100 or something
            # Need to implement based on homologations
            # Since not specified, set factores to montos for demo
            self.factores = {f'factor{i}': self.montos.get(f'amount{i}', 0) for i in range(1, 30)}
            # Validate sum of factors 8-16 <=1
            sum_factors = sum(self.factores.get(f'factor{i}', 0) for i in range(8, 17))
            if sum_factors > 1:
                raise ValueError("Sum of factors 8 to 16 exceeds 1")
        self.save()

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)  # e.g., 'create', 'update', 'delete', 'bulk_load'
    qualification = models.ForeignKey(Qualification, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField()  # JSON or text details

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"

# Extend User with broker
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    broker = models.ForeignKey(Broker, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.broker.name}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Assume default broker or create one
        broker, _ = Broker.objects.get_or_create(name='Default Broker')
        UserProfile.objects.create(user=instance, broker=broker)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
