from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Broker, UserProfile, TaxQualification, AuditLog
from .resources import TaxQualificationResource

# ==============================================================================
# 1. RECURSOS DE EXPORTACIÓN (Define cómo se ve el Excel)
# ==============================================================================
class TaxQualificationResource(resources.ModelResource):
    class Meta:
        model = TaxQualification
        # Definimos qué campos salen en el reporte y usamos notación __ para acceder a relaciones
        fields = ('id', 'broker__name', 'instrument', 'payment_date', 'exercise_year', 'source', 'financial_data')
        export_order = ('id', 'instrument', 'broker__name', 'payment_date', 'exercise_year', 'financial_data')

# ==============================================================================
# 2. CONFIGURACIÓN DE MODELOS
# ==============================================================================

@admin.register(Broker)
class BrokerAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'id')
    search_fields = ('name', 'code')  # <--- CRÍTICO: Habilita la barra de búsqueda y el autocomplete
    ordering = ('name',)

# 2. Inline Mejorado con Autocomplete
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Corredor'
    
    # H0P3 UX FIX: Usar widget de búsqueda en lugar de dropdown simple
    autocomplete_fields = ['broker']

# Extendemos el UserAdmin nativo para que muestre el Broker ahí mismo
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'get_broker', 'is_staff')

    def get_broker(self, instance):
        try:
            return instance.userprofile.broker.name
        except:
            return "Sin Asignar"
    get_broker.short_description = 'Corredor Asignado'

# Re-registramos el User con nuestra personalización
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# ==============================================================================
# 3. MANTENEDOR PRINCIPAL (TAX QUALIFICATION) - MEJORADO
# ==============================================================================
@admin.register(TaxQualification)
class TaxQualificationAdmin(ImportExportModelAdmin):
    # Vinculamos la clase de recurso para permitir Exportar/Importar
    resource_class = TaxQualificationResource
    
    # Lista de visualización
    list_display = ('instrument', 'payment_date', 'broker', 'exercise_year', 'source', 'short_financial_data')
    list_filter = ('broker', 'source', 'exercise_year')
    search_fields = ('instrument', 'broker__name')
    date_hierarchy = 'payment_date' # Navegación por fechas rápida

    # --- CARGA MANUAL AVANZADA (FIELDSETS) ---
    # Esto organiza el formulario en secciones visuales para facilitar el ingreso manual
    fieldsets = (
        ('Información General', {
            'fields': ('broker', 'instrument', 'source'),
            'description': 'Datos básicos del instrumento financiero.'
        }),
        ('Detalles del Periodo', {
            'fields': ('payment_date', 'exercise_year')
        }),
        ('Cálculo y Factores (JSON)', {
            'classes': ('collapse',), # Hace que esta sección sea colapsable
            'fields': ('financial_data',),
            'description': 'Ingrese aquí el objeto JSON con los factores calculados o montos brutos.'
        }),
    )

    # Helper para no llenar la tabla con un JSON gigante
    def short_financial_data(self, obj):
        if not obj.financial_data:
            return "-"
        data_str = str(obj.financial_data)
        return data_str[:50] + "..." if len(data_str) > 50 else data_str
    short_financial_data.short_description = "Datos (Vista Previa)"

# ==============================================================================
# 4. AUDITORÍA (SOLO LECTURA)
# ==============================================================================
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'details_short')
    list_filter = ('action', 'user')
    # Importante: Los logs no deben poder editarse, solo leerse
    readonly_fields = ('timestamp', 'user', 'action', 'details')

    def details_short(self, obj):
        return str(obj.details)[:50]
    details_short.short_description = 'Detalles'