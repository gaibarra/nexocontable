from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import PerfilCPC, Tenant, MembresiaTenant, ConstanciaPrivacidad
from .privacidad import VERSION_AVISO, huella_aviso


class RegistroUsuarioForm(forms.ModelForm):
    """Formulario de registro: datos de usuario + perfil CPC."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent',
            'placeholder': 'correo@ejemplo.com'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent',
            'placeholder': 'Mínimo 8 caracteres'
        }),
        label='Contraseña', min_length=8
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent',
            'placeholder': 'Repite la contraseña'
        }),
        label='Confirmar contraseña'
    )

    # Campos del perfil CPC
    nombre_completo = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent',
            'placeholder': 'Tu nombre completo'
        })
    )
    cedula_profesional = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent',
            'placeholder': 'Opcional'
        })
    )
    especialidad = forms.ChoiceField(
        choices=[('', 'Selecciona tu especialidad')] + list(PerfilCPC.ESPECIALIDAD_CHOICES),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent',
        })
    )
    ciudad = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent',
            'placeholder': 'Tu ciudad'
        })
    )
    estado = forms.ChoiceField(
        choices=[('', 'Selecciona tu estado')] + list(PerfilCPC.ESTADOS_MEXICO),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent',
        })
    )
    telefono = forms.CharField(
        max_length=15, required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent',
            'placeholder': 'Número de teléfono'
        })
    )
    version_aviso = forms.CharField(widget=forms.HiddenInput, initial=VERSION_AVISO)
    acepta_terminos = forms.BooleanField(
        label='He leído el aviso de privacidad y consiento el tratamiento de mis datos para las finalidades necesarias descritas',
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-brand-600 rounded'})
    )

    class Meta:
        model = User
        fields = ['email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['autocomplete'] = 'off'
        for nombre in ('password', 'password_confirm'):
            self.fields[nombre].widget.attrs['autocomplete'] = 'new-password'

    def clean_version_aviso(self):
        value = self.cleaned_data['version_aviso']
        if value != VERSION_AVISO:
            raise forms.ValidationError('El aviso de privacidad se actualizó. Recarga el formulario, revisa el aviso y vuelve a confirmar.')
        return value

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo electrónico.')
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password_confirm'):
            self.add_error('password_confirm', 'Las contraseñas no coinciden.')
        return cleaned

    def save(self, commit=True):
        user = User(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['nombre_completo'].split()[0],
            last_name=' '.join(self.cleaned_data['nombre_completo'].split()[1:]),
        )
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            PerfilCPC.objects.create(
                usuario=user,
                nombre_completo=self.cleaned_data['nombre_completo'],
                cedula_profesional=self.cleaned_data.get('cedula_profesional'),
                especialidad=self.cleaned_data['especialidad'],
                ciudad=self.cleaned_data['ciudad'],
                estado=self.cleaned_data['estado'],
                telefono=self.cleaned_data.get('telefono'),
                acepta_terminos=self.cleaned_data['acepta_terminos'],
            )
            ConstanciaPrivacidad.objects.create(usuario=user, version=VERSION_AVISO, contenido_hash=huella_aviso())
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Correo electrónico o Usuario',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent',
            'placeholder': 'correo@ejemplo.com o usuario', 'autofocus': True
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent',
            'placeholder': '••••••••'
        })
    )


INPUT_CLASS = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent'
SELECT_CLASS = INPUT_CLASS


class TenantForm(forms.ModelForm):
    """Formulario para crear/editar una organización (tenant)."""
    class Meta:
        model = Tenant
        fields = ['nombre', 'rfc', 'giro', 'regimen_fiscal', 'direccion', 'ciudad', 'estado', 'codigo_postal', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ej: Despacho García y Asociados'}),
            'rfc': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'XAXX010101000'}),
            'giro': forms.Select(attrs={'class': SELECT_CLASS}),
            'regimen_fiscal': forms.Select(attrs={'class': SELECT_CLASS}),
            'direccion': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 2, 'placeholder': 'Calle, número, colonia'}),
            'ciudad': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Mérida'}),
            'estado': forms.Select(attrs={'class': SELECT_CLASS}),
            'codigo_postal': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '97000'}),
            'telefono': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '999 123 4567'}),
        }


class PerfilCPCForm(forms.ModelForm):
    """Formulario para editar el perfil CPC."""
    class Meta:
        model = PerfilCPC
        fields = [
            'nombre_completo', 'cedula_profesional', 'numero_certificacion',
            'colegio_afiliado', 'especialidad', 'telefono', 'ciudad', 'estado',
            'anios_experiencia', 'linkedin_url'
        ]
        widgets = {
            'nombre_completo': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'cedula_profesional': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Opcional'}),
            'numero_certificacion': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Opcional'}),
            'colegio_afiliado': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ej: CCPEM'}),
            'especialidad': forms.Select(attrs={'class': SELECT_CLASS}),
            'telefono': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'ciudad': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'estado': forms.Select(attrs={'class': SELECT_CLASS}),
            'anios_experiencia': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
            'linkedin_url': forms.URLInput(attrs={'class': INPUT_CLASS, 'placeholder': 'https://linkedin.com/in/...'}),
        }


class RegistrarColegaForm(forms.Form):
    """Formulario para que un propietario registre directamente a un colega."""
    nombre = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Nombre completo'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'correo@ejemplo.com'
        })
    )
    rol = forms.ChoiceField(
        choices=MembresiaTenant.ROL_CHOICES[1:],  # Excluir propietario
        widget=forms.Select(attrs={'class': SELECT_CLASS})
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        # No validamos si existe el usuario aquí, 
        # la vista manejará si lo crea o solo lo vincula.
        return email
