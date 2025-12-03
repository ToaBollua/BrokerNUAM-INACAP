from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Broker, UserProfile, TaxQualification, AuditLog

# 1. Configuración de Broker
@admin.register(Broker)
class BrokerAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'id')
    search_fields = ('name', 'code')

# 2. Configuración de UserProfile (Para vincular Usuario -> Broker)
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Corredor'

# Extendemos el UserAdmin nativo para que muestre el Broker ahí mismo
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'get_broker', 'is_staff')

    def get_broker(self, instance):
        # Manejo de error por si el usuario no tiene perfil aún
        try:
            return instance.userprofile.broker.name
        except:
            return "Sin Asignar"
    get_broker.short_description = 'Corredor Asignado'

# Re-registramos el User con nuestra personalización
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# 3. Visualización de Calificaciones
@admin.register(TaxQualification)
class TaxQualificationAdmin(admin.ModelAdmin):
    list_display = ('instrument', 'payment_date', 'broker', 'exercise_year', 'source')
    list_filter = ('broker', 'source', 'exercise_year')
    search_fields = ('instrument',)

# 4. Auditoría (Solo lectura para seguridad)
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'details_short')
    list_filter = ('action', 'user')
    readonly_fields = ('timestamp', 'user', 'action', 'details')

    def details_short(self, obj):
        return obj.details[:50] + "..." if len(obj.details) > 50 else obj.details
    details_short.short_description = 'Detalles'