from django import forms
from django.core.exceptions import ValidationError
from .models import TaxQualification
import json

class ManualEntryForm(forms.ModelForm):
    # --- CAMPOS VIRTUALES ---
    monto_base = forms.DecimalField(
        label="Monto Base ($)", 
        max_digits=12, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'bg-gray-700 text-white border-none rounded p-2 w-full', 'placeholder': 'Ej: 1000000'})
    )
    
    factor_credito = forms.DecimalField(
        label="Factor Crédito (Máx 1.0)",
        max_digits=5, 
        decimal_places=4,
        help_text="Debe ser un valor decimal menor o igual a 1.0000",
        widget=forms.NumberInput(attrs={'class': 'bg-gray-700 text-white border-none rounded p-2 w-full', 'step': '0.0001'})
    )
    
    factor_incremento = forms.DecimalField(
        label="Factor Incremento (Máx 1.0)",
        max_digits=5, 
        decimal_places=4,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'bg-gray-700 text-white border-none rounded p-2 w-full', 'step': '0.0001'})
    )

    class Meta:
        model = TaxQualification
        fields = ['instrument', 'payment_date', 'exercise_year', 'source', 'currency']
        widgets = {
            'instrument': forms.TextInput(attrs={'class': 'bg-gray-700 text-white border-none rounded p-2 w-full', 'placeholder': 'Ej: CHILE N.A.'}),
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'bg-gray-700 text-white border-none rounded p-2 w-full'}),
            'exercise_year': forms.NumberInput(attrs={'class': 'bg-gray-700 text-white border-none rounded p-2 w-full'}),
            'source': forms.Select(attrs={'class': 'bg-gray-700 text-white border-none rounded p-2 w-full'}),
            # AQUÍ ESTÁ LA CORRECCIÓN: Forzamos el Select y le damos estilo
            'currency': forms.Select(attrs={'class': 'bg-gray-700 text-white border-none rounded p-2 w-full font-bold border border-gray-600'}),
        }

    # --- VALIDACIONES Y LOGICA JSON ---
    def clean_factor_credito(self):
        factor = self.cleaned_data['factor_credito']
        if factor > 1:
            raise ValidationError("El Factor de Crédito no puede ser mayor a 1.0.")
        if factor < 0:
            raise ValidationError("El factor no puede ser negativo.")
        return factor

    def clean_factor_incremento(self):
        factor = self.cleaned_data.get('factor_incremento')
        if factor and factor > 1:
            raise ValidationError("El Factor de Incremento no puede ser mayor a 1.0.")
        return factor

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        financial_payload = {
            "moneda": instance.currency, 
            "monto_base": float(self.cleaned_data['monto_base']),
            "factores": {
                "credito": float(self.cleaned_data['factor_credito']),
                "incremento": float(self.cleaned_data['factor_incremento'] or 0)
            },
            "calculado_automatico": True
        }
        
        instance.financial_data = financial_payload
        
        if commit:
            instance.save()
        return instance

class CSVUploadForm(forms.Form):
    file = forms.FileField(label='Seleccionar archivo CSV', widget=forms.FileInput(attrs={'class': 'text-white'}))