from io import BytesIO
import re
import warnings
from PIL import Image, ImageOps, UnidentifiedImageError
from django import forms
from django.core.files.base import ContentFile
from .forms import INPUT_CLASS
from .models import IdentidadDespacho, PresentacionEmpresa

CAMPOS = [('rfc', 'RFC'), ('ciudad', 'Ciudad'), ('direccion', 'Dirección'),
          ('telefono', 'Teléfono'), ('correo', 'Correo'), ('sitio_web', 'Sitio web')]
CAMPOS_EMPRESA = CAMPOS + [('giro', 'Giro'), ('regimen_fiscal', 'Régimen fiscal')]


def normalizar_logo(upload):
    if upload.size > 2 * 1024 * 1024:
        raise forms.ValidationError('El logo debe pesar como máximo 2 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(upload) as image:
                formato = image.format
                if formato not in ('PNG', 'JPEG'):
                    raise forms.ValidationError('Selecciona un logo PNG o JPG.')
                if max(image.size) > 4096 or min(image.size) < 1 or getattr(image, 'n_frames', 1) != 1:
                    raise forms.ValidationError('Usa una imagen estática de hasta 4096 × 4096 píxeles.')
                image.load()
                clean = ImageOps.exif_transpose(image)
                clean = clean.convert('RGBA' if formato == 'PNG' else 'RGB')
                clean.info.clear()
                output = BytesIO()
                clean.save(output, format=formato, **({'quality': 90} if formato == 'JPEG' else {}))
                return ContentFile(output.getvalue(), name='logo.png' if formato == 'PNG' else 'logo.jpg')
    except forms.ValidationError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise forms.ValidationError('No pudimos leer la imagen. Selecciona otro archivo PNG o JPG.')
    finally:
        upload.seek(0)


class ColorInput(forms.TextInput):
    input_type = 'color'


class FormularioMarca(forms.ModelForm):
    logo_previo = forms.CharField(required=False, widget=forms.HiddenInput)
    archivo_logo = forms.FileField(label='Logo', required=False,
        widget=forms.FileInput(attrs={'accept': 'image/png,image/jpeg'}))
    quitar_logo = forms.BooleanField(label='Quitar el logo actual', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple, forms.FileInput)):
                field.widget.attrs['class'] = INPUT_CLASS
        self.order_fields(['nombre', 'archivo_logo', 'quitar_logo', 'rfc', 'direccion', 'ciudad',
                           'telefono', 'correo', 'sitio_web', 'usar_color_despacho', 'color', 'composicion',
                           'campos_empresa', 'campos_despacho'])

    def clean_archivo_logo(self):
        upload = self.cleaned_data.get('archivo_logo')
        return normalizar_logo(upload) if upload else None

    def clean_color(self):
        color = self.cleaned_data.get('color', '').strip()
        if color and not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
            raise forms.ValidationError('Selecciona un color válido.')
        return color.lower()

    def clean(self):
        data = super().clean()
        if data.get('archivo_logo') and data.get('quitar_logo'):
            self.add_error('quitar_logo', 'Elige subir un logo nuevo o quitar el actual, no ambos.')
        return data


class IdentidadDespachoForm(FormularioMarca):
    class Meta:
        model = IdentidadDespacho
        fields = ['nombre', 'rfc', 'direccion', 'ciudad', 'telefono', 'correo', 'sitio_web', 'color']
        widgets = {'color': ColorInput()}


class PresentacionEmpresaForm(FormularioMarca):
    usar_color_despacho = forms.BooleanField(label='Usar el color del despacho', required=False, initial=True)
    campos_empresa = forms.MultipleChoiceField(label='Datos visibles de la empresa', choices=CAMPOS_EMPRESA,
        widget=forms.CheckboxSelectMultiple, required=False)
    campos_despacho = forms.MultipleChoiceField(label='Datos visibles del despacho', choices=CAMPOS,
        widget=forms.CheckboxSelectMultiple, required=False)

    class Meta:
        model = PresentacionEmpresa
        fields = ['correo', 'sitio_web', 'composicion', 'color', 'campos_empresa', 'campos_despacho']
        widgets = {'color': ColorInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial['usar_color_despacho'] = not bool(self.instance.color)
            if not self.instance.color:
                try:
                    color = self.instance.organizacion.propietario.identidad_despacho.color
                except (AttributeError, IdentidadDespacho.DoesNotExist):
                    color = '#1a365d'
                self.initial['color'] = color

    def clean(self):
        data = super().clean()
        if data.get('usar_color_despacho'):
            data['color'] = ''
        return data

