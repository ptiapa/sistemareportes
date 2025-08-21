from django import forms
from .models import FlujoCaja

class FlujoCajaForm(forms.ModelForm):
    class Meta:
        model = FlujoCaja
        fields = [
            'tipo', 'anio', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
            'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
        ]
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'anio': forms.NumberInput(attrs={'class': 'form-control'}),
            'enero': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'febrero': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'marzo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'abril': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'mayo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'junio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'julio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'agosto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'septiembre': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'octubre': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'noviembre': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'diciembre': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class ExcelUploadForm(forms.Form):
    archivo = forms.FileField(help_text="Sube un .xlsx")
    hoja = forms.CharField(required=False, help_text="Nombre de la hoja (opcional).")

class EditarCodigoForm(forms.Form):
    codigo_actual = forms.CharField(disabled=True, label="Código actual")
    nuevo_codigo = forms.CharField(label="Nuevo código")

    def clean_nuevo_codigo(self):
        v = self.cleaned_data["nuevo_codigo"].strip()
        if not v:
            raise forms.ValidationError("El nuevo código no puede estar vacío.")
        return v

# Alias para mantener compatibilidad con la vista que importa ImportarExcelForm
class ImportarExcelForm(ExcelUploadForm):
    pass