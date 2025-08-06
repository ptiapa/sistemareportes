from django import forms
from .models import EstatusSemanal

class EstatusSemanalForm(forms.ModelForm):
    class Meta:
        model = EstatusSemanal
        fields = '__all__'
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'comentario': forms.Textarea(attrs={'rows': 4}),
        }
