from decimal import Decimal
from django import forms
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from cuentas.models import PerfilCPC, Tenant
from donaciones.models import Donativo
from .forms import ContactoForm
from .models import Nota, Tarea

User = get_user_model()


class DatosUsuarioMixin:
    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya existe un usuario con este correo.')
        return email

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya existe un usuario con este nombre.')
        return username


class UsuarioCrearForm(DatosUsuarioMixin, UserCreationForm):
    email = forms.EmailField(label='Correo electrónico')
    first_name = forms.CharField(label='Nombre', max_length=150)
    ciudad = forms.CharField(label='Ciudad', max_length=100)
    estado = forms.ChoiceField(label='Estado', choices=PerfilCPC.ESTADOS_MEXICO)
    telefono = forms.CharField(label='Teléfono', max_length=15, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'ciudad', 'estado', 'telefono']


class UsuarioEditarForm(DatosUsuarioMixin, forms.ModelForm):
    email = forms.EmailField(label='Correo electrónico')
    first_name = forms.CharField(label='Nombre', max_length=150)
    ciudad = forms.CharField(label='Ciudad', max_length=100, required=False)
    estado = forms.ChoiceField(label='Estado', choices=[('', 'Sin especificar')] + PerfilCPC.ESTADOS_MEXICO, required=False)
    telefono = forms.CharField(label='Teléfono', max_length=15, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'ciudad', 'estado', 'telefono']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        perfil = getattr(self.instance, 'perfil_cpc', None)
        if perfil:
            for field in ['ciudad', 'estado', 'telefono']:
                self.initial[field] = getattr(perfil, field)


class OrganizacionForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['nombre', 'propietario', 'rfc', 'giro', 'sector', 'regimen_fiscal', 'direccion', 'ciudad', 'estado', 'codigo_postal', 'telefono']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Incluye al propietario actual incluso si su cuenta fue suspendida.
        self.fields['propietario'].queryset = User.objects.filter(
            Q(is_active=True) | Q(pk=getattr(self.instance, 'propietario_id', None)))


class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = ['texto']
        labels = {'texto': 'Nota'}
        widgets = {'texto': forms.Textarea(attrs={'rows': 6})}


class SeguimientoForm(forms.ModelForm):
    class Meta:
        model = Tarea
        fields = ['titulo', 'vence', 'completada', 'responsable']
        labels = {'titulo': 'Título', 'vence': 'Fecha de seguimiento'}
        widgets = {'vence': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['responsable'].queryset = User.objects.filter(is_active=True, acceso_panel__activo=True)


class DonativoManualForm(forms.ModelForm):
    monto = forms.DecimalField(label='Monto en MXN', max_digits=10, decimal_places=2,
                              min_value=Decimal('0.01'), max_value=Decimal('100000'))

    class Meta:
        model = Donativo
        fields = ['nombre_donante', 'email_donante', 'monto', 'estado']
        labels = {'nombre_donante': 'Donante', 'email_donante': 'Correo del donante'}


class ConfirmarEliminarForm(forms.Form):
    motivo = forms.CharField(label='Motivo de eliminación', max_length=300,
                             widget=forms.Textarea(attrs={'rows': 3}))
    confirmacion = forms.CharField(label='Escribe la confirmación indicada', max_length=80)
    token = forms.CharField(widget=forms.HiddenInput)
