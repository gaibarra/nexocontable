from django import forms
from django.contrib.auth import get_user_model
from .models import Contacto, Tarea, ControlPlataforma


class ContactoForm(forms.ModelForm):
    class Meta:
        model = Contacto
        fields = ['nombre', 'email', 'telefono', 'despacho', 'origen', 'etiquetas', 'etapa', 'responsable']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['responsable'].queryset = get_user_model().objects.filter(acceso_panel__activo=True, is_active=True)

    def clean_email(self):
        value = self.cleaned_data['email'].strip().lower()
        if Contacto.objects.filter(email__iexact=value).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya existe un contacto con este correo.')
        return value


class TareaForm(forms.ModelForm):
    class Meta:
        model = Tarea
        fields = ['titulo', 'vence']
        widgets = {'vence': forms.DateInput(attrs={'type': 'date'})}


class ControlForm(forms.ModelForm):
    motivo = forms.CharField(max_length=300, label='Motivo del cambio')

    class Meta:
        model = ControlPlataforma
        fields = ['aviso', 'aviso_activo', 'generacion_habilitada', 'limite_diario_usuario']
