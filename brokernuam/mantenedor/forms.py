from django import forms
from .models import Qualification, Broker

class QualificationForm(forms.ModelForm):
    class Meta:
        model = Qualification
        fields = ['mercado', 'instrumento', 'fecha_pago', 'ejercicio', 'origen']
        widgets = {
            'fecha_pago': forms.DateInput(attrs={'type': 'date'}),
        }

class QualificationAmountsForm(forms.Form):
    # Dynamic fields for amounts 1 to 29
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for i in range(1, 30):
            self.fields[f'amount{i}'] = forms.DecimalField(
                max_digits=10, decimal_places=2, required=False,
                label=f'Amount {i}'
            )

class QualificationFactorsForm(forms.Form):
    # Dynamic fields for factors 1 to 29
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for i in range(1, 30):
            self.fields[f'factor{i}'] = forms.DecimalField(
                max_digits=10, decimal_places=2, required=False,
                label=f'Factor {i}'
            )

class BulkLoadForm(forms.Form):
    csv_file = forms.FileField(label='Select CSV file')
    load_type = forms.ChoiceField(choices=[('montos', 'Montos'), ('factores', 'Factores')], label='Load Type')
