"""Fuente común de identidad para pantalla, impresión y Word."""
import copy
import re
from uuid import UUID
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from cuentas.models import LogoDocumento

ETIQUETAS = {'rfc': 'RFC', 'direccion': 'Dirección', 'ciudad': 'Ciudad', 'telefono': 'Teléfono',
             'correo': 'Correo', 'sitio_web': 'Sitio web', 'giro': 'Giro', 'regimen_fiscal': 'Régimen fiscal'}


def relacion(obj, nombre):
    try:
        return getattr(obj, nombre)
    except (ObjectDoesNotExist, AttributeError):
        return None


def bloque(obj, rol, campos, empresa=False, logo=None):
    lineas = []
    for campo in campos:
        if campo not in ETIQUETAS:
            continue
        if empresa and campo in ('giro', 'regimen_fiscal'):
            valor = getattr(obj, f'get_{campo}_display')()
        else:
            valor = getattr(obj, campo, '') or ''
        if valor:
            lineas.append({'etiqueta': ETIQUETAS[campo], 'valor': str(valor)})
    return {'rol': rol, 'nombre': obj.nombre, 'logo': str(logo.pk) if logo else None, 'lineas': lineas}


def construir_presentacion(tenant, despacho=None, empresa=None):
    despacho = despacho if despacho is not None else relacion(tenant.propietario, 'identidad_despacho')
    empresa = empresa if empresa is not None else relacion(tenant, 'presentacion_documentos')
    modo = empresa.composicion if empresa else 'ambos'
    color = (empresa.color if empresa else '') or (despacho.color if despacho else '') or '#1a365d'
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
        color = '#1a365d'
    bloques = []
    if modo in ('ambos', 'despacho') and despacho and despacho.nombre:
        campos = empresa.campos_despacho if empresa else ['rfc', 'ciudad', 'telefono', 'correo', 'sitio_web']
        bloques.append(bloque(despacho, 'Elaborado por', campos, logo=despacho.logo))
    if modo in ('ambos', 'empresa') or not bloques:
        campos = empresa.campos_empresa if empresa else ['rfc', 'ciudad']
        datos = copy.copy(tenant)
        datos.correo = empresa.correo if empresa else ''
        datos.sitio_web = empresa.sitio_web if empresa else ''
        bloques.append(bloque(datos, 'Preparado para', campos, empresa=True, logo=empresa.logo if empresa else None))
    return {'version': 1, 'color': color, 'empresa_nombre': tenant.nombre, 'bloques': bloques}


def presentacion_anterior(tenant):
    return {'version': 0, 'color': '#1a365d', 'empresa_nombre': tenant.nombre,
            'bloques': [bloque(tenant, 'Organización', ['giro', 'regimen_fiscal'], empresa=True)]}


def datos_manual(manual):
    if manual.aprobado:
        return copy.deepcopy(manual.presentacion_snapshot or presentacion_anterior(manual.tenant))
    return construir_presentacion(manual.tenant)


def logo_disponible(identificador):
    try:
        UUID(str(identificador))
    except (ValueError, TypeError, AttributeError):
        return None
    logo = LogoDocumento.objects.filter(pk=identificador).first()
    return logo if logo and logo.imagen and logo.imagen.storage.exists(logo.imagen.name) else None


def contexto_presentacion(datos, previews=None):
    datos = copy.deepcopy(datos)
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', str(datos.get('color', ''))):
        datos['color'] = '#1a365d'
    for item in datos['bloques']:
        logo = logo_disponible(item.get('logo')) if item.get('logo') else None
        item['logo_src'] = reverse('logo_documento', args=[logo.pk]) if logo else ''
        if previews and item['rol'] in previews:
            item['logo_src'] = previews[item['rol']]
    return datos
