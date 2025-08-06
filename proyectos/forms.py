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
