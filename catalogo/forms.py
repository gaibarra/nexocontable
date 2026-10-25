from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory
from .models import CatalogoCuentas, ManualContable, CatalogoPlantilla, CatalogoPlantillaCuenta

class GenerarManualForm(forms.Form):
    cuentas = forms.ModelMultipleChoiceField(
        queryset=CatalogoCuentas.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-checkbox h-5 w-5 text-blue-600',
        }),
        label="Selecciona las cuentas"
    )
    titulo = forms.CharField(
        max_length=255,
        label="Título del Manual",
        widget=forms.TextInput(attrs={
            'class': 'border-gray-300 focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border rounded-md h-10',
            'placeholder': 'Escribe el título del manual',
        })
    )

class EditarManualForm(forms.ModelForm):
    class Meta:
        model = ManualContable
        fields = ['titulo', 'contenido']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Escribe el título del manual',
            }),
            'contenido': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'rows': 10,
                'placeholder': 'Edita el contenido del manual en formato Markdown...',
            }),
        }
        labels = {
            'titulo': 'Título del Manual',
            'contenido': 'Contenido (en formato Markdown)',
        }


class CatalogoPlantillaForm(forms.ModelForm):
    class Meta:
        model = CatalogoPlantilla
        fields = ['nombre', 'giro', 'regimen_fiscal', 'descripcion', 'activo', 'orden']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'placeholder': 'Nombre de la plantilla',
            }),
            'giro': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
            }),
            'regimen_fiscal': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'rows': 4,
                'placeholder': 'Descripción opcional',
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded',
            }),
            'orden': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'min': 0,
            }),
        }


class BaseCatalogoPlantillaCuentaFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        cuentas_vistas = set()
        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue
            if form.cleaned_data.get('DELETE'):
                continue

            cuenta = (form.cleaned_data.get('cuenta') or '').strip()
            if not cuenta:
                continue

            cuenta_normalizada = cuenta.lower()
            if cuenta_normalizada in cuentas_vistas:
                raise forms.ValidationError('No puedes repetir la misma cuenta dentro de una plantilla.')
            cuentas_vistas.add(cuenta_normalizada)


CatalogoPlantillaCuentaFormSet = inlineformset_factory(
    CatalogoPlantilla,
    CatalogoPlantillaCuenta,
    formset=BaseCatalogoPlantillaCuentaFormSet,
    fields=['cuenta', 'descripcion', 'codigoagrupador', 'nivel1', 'nivel2', 'nivel3', 'nivel4', 'orden', 'es_recomendada', 'activa'],
    extra=1,
    can_delete=True,
    widgets={
        'cuenta': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
        'descripcion': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
        'codigoagrupador': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
        'nivel1': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
        'nivel2': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
        'nivel3': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
        'nivel4': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
        'orden': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md'}),
        'es_recomendada': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded'}),
        'activa': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded'}),
    },
)


class ImportarCatalogoForm(forms.Form):
    archivo = forms.FileField(label='Catálogo propio (CSV o Excel .xlsx)')
    nivel_maximo = forms.TypedChoiceField(
        label='Importar hasta el nivel', required=False, coerce=int, empty_value=None,
        choices=[('', 'Todos los niveles')] + [(i, f'Nivel {i}') for i in range(1, 21)])

    def clean_archivo(self):
        archivo = self.cleaned_data['archivo']
        if not archivo.name.lower().endswith(('.csv', '.xlsx')):
            raise forms.ValidationError('Usa un archivo CSV o Excel .xlsx.')
        return archivo
