from django import forms

class CsvUploadForm(forms.Form):
    file = forms.FileField(label='Archivo CSV')

class FactorUpdateForm(forms.Form):
    # Usamos un campo de texto para buscar el broker por código, 
    # simulando tu componente React 'Actualización de Factor Directo'
    broker_code = forms.CharField(label='Código Corredor', max_length=50)
    new_factor = forms.DecimalField(label='Nuevo Factor', max_digits=10, decimal_places=6)