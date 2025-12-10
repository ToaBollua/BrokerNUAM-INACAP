from import_export import resources
from .models import TaxQualification

class TaxQualificationResource(resources.ModelResource):
    class Meta:
        model = TaxQualification
        fields = ('instrument', 'payment_date', 'exercise_year', 'source', 'financial_data')
        export_order = ('instrument', 'payment_date', 'exercise_year', 'source', 'financial_data')
        
    # --- FIX H0P3: Agregamos **kwargs para absorber argumentos extra de la librería ---
    def get_export_headers(self, selected_fields=None, **kwargs):
        return ['Instrumento', 'Fecha Pago', 'Año', 'Origen', 'Datos Financieros']