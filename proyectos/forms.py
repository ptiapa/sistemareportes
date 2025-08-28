from django import forms
from .models import FlujoCaja, Proyecto

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
    archivo = forms.FileField(label="Archivo (.xlsx)")
    hoja = forms.CharField(label="Hoja (opcional)", required=False)

class EditarCodigoForm(forms.Form):
    codigo_actual = forms.CharField(disabled=True, required=False, label="Código actual")
    nuevo_codigo = forms.CharField(label="Nuevo código")

    def __init__(self, *args, **kwargs):
        self.proyecto = kwargs.pop("proyecto", None)
        super().__init__(*args, **kwargs)

def clean_nuevo_codigo(self):
        val = self.cleaned_data["nuevo_codigo"].strip()
        if not val:
            raise forms.ValidationError("El código no puede estar vacío.")
        # Evitar duplicados (el modelo tiene unique=True)
        qs = Proyecto.objects.filter(codigo=val)
        if self.proyecto:
            qs = qs.exclude(pk=self.proyecto.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe un proyecto con ese código.")
        return val


# Alias para mantener compatibilidad con la vista que importa ImportarExcelForm
class ImportarExcelForm(ExcelUploadForm):
    pass