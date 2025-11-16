from django.contrib import admin
from .models import Broker, Qualification, AuditLog, UserProfile

# Registra UserProfile para verlo en el admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'broker')

# Registra Broker
@admin.register(Broker)
class BrokerAdmin(admin.ModelAdmin):
    list_display = ('name',)

# Registra Qualification con filtros útiles
@admin.register(Qualification)
class QualificationAdmin(admin.ModelAdmin):
    list_display = ('instrumento', 'mercado', 'fecha_pago', 'ejercicio', 'broker', 'is_bolsa')
    list_filter = ('mercado', 'broker', 'is_bolsa', 'ejercicio')
    search_fields = ('instrumento',)

# Registra AuditLog (útil para depurar)
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp', 'qualification')
    list_filter = ('user', 'action')