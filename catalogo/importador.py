"""
Importador de catálogos de cuentas desde CSV y Excel.
Valida cada cuenta contra el Código Agrupador del SAT.
"""
import csv
import io
import logging
import re
from django.core.exceptions import ValidationError
from .sat import asegurar_catalogo_sat, sugerir_relacion
from django.db import models, transaction
from .models import CatalogoCuentas, CodigoAgrupador, CatalogoPlantilla

logger = logging.getLogger(__name__)

# Columnas esperadas en el archivo
COLUMNAS_REQUERIDAS = {'cuenta', 'descripcion'}
COLUMNAS_CON_NIVELES = {'cuenta', 'descripcion', 'codigoagrupador', 'nivel1', 'nivel2', 'nivel3', 'nivel4'}


class ResultadoImportacion:
    """Resultado de la importación con estadísticas."""
    def __init__(self):
        self.creadas = 0
        self.actualizadas = 0
        self.errores = []
        self.total_filas = 0
        self.omitidas = 0
        self.sugeridas = 0
        self.pendientes = 0

    @property
    def exitosas(self):
        return self.creadas + self.actualizadas

    def agregar_error(self, fila, mensaje):
        self.errores.append({'fila': fila, 'mensaje': mensaje})


def obtener_plantilla_catalogo(tenant):
    """
    Devuelve la primera plantilla activa que coincida con el giro del tenant.
    Si la plantilla define régimen fiscal, debe coincidir también.
    """
    if not tenant:
        return None

    return (
        CatalogoPlantilla.objects
        .filter(activo=True, giro=tenant.giro)
        .filter(models.Q(regimen_fiscal__isnull=True) | models.Q(regimen_fiscal=tenant.regimen_fiscal))
        .order_by('orden', 'nombre')
        .first()
    )


def _obtener_filas_plantilla(plantilla):
    if not plantilla:
        return []

    filas = []
    for cuenta in plantilla.cuentas.filter(activa=True).select_related('codigoagrupador').order_by('orden', 'cuenta'):
        filas.append({
            'cuenta': cuenta.cuenta,
            'descripcion': cuenta.descripcion or '',
            'codigoagrupador': cuenta.codigoagrupador.codigoagrupador,
            'nivel1': cuenta.nivel1,
            'nivel2': cuenta.nivel2,
            'nivel3': cuenta.nivel3,
            'nivel4': cuenta.nivel4,
        })
    return filas


def _normalizar_fila(fila):
    normalizada = {}
    for k, v in fila.items():
        clave = str(k).strip().lower()
        if v is None:
            valor = ''
        elif isinstance(v, str):
            valor = v.strip()
        else:
            valor = str(v).strip()
        normalizada[clave] = valor
    return normalizada


def _parsear_niveles(fila):
    niveles = {}
    for nivel in ['nivel1', 'nivel2', 'nivel3', 'nivel4']:
        valor = fila.get(nivel, '')
        if valor is None or valor == '':
            niveles[nivel] = None
            continue

        if isinstance(valor, int):
            niveles[nivel] = valor
            continue

        texto = str(valor).strip()
        niveles[nivel] = int(texto) if texto.isdigit() else None
    return niveles


def _validar_y_guardar_fila(resultado, tenant, fila, fila_numero, codigos_sat):
    cuenta = fila.get('cuenta', '').strip()
    descripcion = fila.get('descripcion', '').strip()
    codigo_agrup = fila.get('codigoagrupador', '').strip()

    if not cuenta:
        resultado.agregar_error(fila_numero, 'Cuenta vacía.')
        return

    if not descripcion:
        resultado.agregar_error(fila_numero, f'Cuenta {cuenta}: descripción vacía.')
        return

    sugerida = not bool(codigo_agrup)
    confianza = None
    codigo_obj = codigos_sat.get(codigo_agrup)
    if codigo_agrup and not codigo_obj:
        resultado.agregar_error(fila_numero, f'Cuenta {cuenta}: código agrupador "{codigo_agrup}" no existe en el catálogo SAT.')
        return
    if sugerida:
        codigo_obj, confianza = sugerir_relacion(descripcion, codigos_sat.values())

    niveles = _parsear_niveles(fila)

    _, created = CatalogoCuentas.objects.update_or_create(
        tenant=tenant,
        cuenta=cuenta,
        defaults={
            'descripcion': descripcion,
            'nivel': obtener_nivel(fila),
            'codigoagrupador': codigo_obj,
            'relacion_sugerida': sugerida,
            'confianza_relacion': confianza,
            'nivel1': niveles.get('nivel1'),
            'nivel2': niveles.get('nivel2'),
            'nivel3': niveles.get('nivel3'),
            'nivel4': niveles.get('nivel4'),
        }
    )

    if sugerida:
        if codigo_obj:
            resultado.sugeridas += 1
        else:
            resultado.pendientes += 1
    if created:
        resultado.creadas += 1
    else:
        resultado.actualizadas += 1


def importar_desde_filas(tenant, filas, headers, resultado=None, start_row=2, nivel_maximo=None):
    """
    Importa filas ya normalizadas con la misma lógica que CSV/Excel.
    """
    if resultado is None:
        resultado = ResultadoImportacion()

    if nivel_maximo not in (None, ''):
        try:
            nivel_maximo = int(nivel_maximo)
            if nivel_maximo < 1 or nivel_maximo > 20:
                raise ValueError
        except (ValueError, TypeError):
            resultado.agregar_error(0, 'El nivel máximo debe estar entre 1 y 20.')
            return resultado
    else:
        nivel_maximo = None

    columnas = {col.strip().lower() for col in headers if col}
    faltantes = COLUMNAS_REQUERIDAS - columnas
    if faltantes:
        resultado.agregar_error(0, f'Columnas faltantes: {", ".join(faltantes)}. Se requieren: cuenta, descripcion')
        return resultado

    asegurar_catalogo_sat()
    codigos_sat = {ca.codigoagrupador: ca for ca in CodigoAgrupador.objects.all()}

    with transaction.atomic():
        for i, fila in enumerate(filas, start=start_row):
            resultado.total_filas += 1
            fila = _normalizar_fila(fila)
            try:
                nivel = obtener_nivel(fila)
                if nivel_maximo and nivel > nivel_maximo:
                    resultado.omitidas += 1
                    continue
                with transaction.atomic():
                    _validar_y_guardar_fila(resultado, tenant, fila, i, codigos_sat)
            except (ValidationError, ValueError) as exc:
                resultado.agregar_error(i, str(exc))

    return resultado


def obtener_nivel(fila):
    if fila.get('nivel'):
        nivel = int(fila['nivel'])
        if nivel < 1 or nivel > 20:
            raise ValueError('El nivel de la cuenta debe estar entre 1 y 20.')
        return nivel
    niveles = _parsear_niveles(fila)
    presentes = [i for i in range(1, 5) if niveles[f'nivel{i}'] is not None]
    if presentes:
        return max(presentes)
    # Para códigos sin separadores el archivo debe indicar nivel explícito.
    return len(re.split(r'[.\-/]', fila.get('cuenta', '')))


def importar_csv(archivo, tenant, plantilla=None, nivel_maximo=None):
    resultado = ResultadoImportacion()
    try:
        contenido = archivo.read()
        if isinstance(contenido, bytes):
            contenido = contenido.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(contenido))
        if not reader.fieldnames:
            resultado.agregar_error(0, 'El archivo está vacío o no tiene encabezados.')
            return resultado
        return importar_desde_filas(tenant, reader, reader.fieldnames, resultado, nivel_maximo=nivel_maximo)
    except (UnicodeDecodeError, csv.Error) as exc:
        resultado.agregar_error(0, f'No se pudo leer el CSV UTF-8: {exc}')
        return resultado


def importar_excel(archivo, tenant, plantilla=None, nivel_maximo=None):
    import openpyxl
    from zipfile import BadZipFile
    resultado = ResultadoImportacion()
    wb = None
    try:
        wb = openpyxl.load_workbook(archivo, read_only=True, data_only=True)
        rows = wb.active.iter_rows(values_only=True)
        first = next(rows, None)
        if first is None:
            resultado.agregar_error(0, 'El archivo Excel está vacío.')
            return resultado
        headers = [str(h).strip().lower() if h is not None else '' for h in first]
        filas = (dict(zip(headers, row)) for row in rows if any(v is not None for v in row))
        return importar_desde_filas(tenant, filas, headers, resultado, nivel_maximo=nivel_maximo)
    except (ValueError, OSError, KeyError, BadZipFile, openpyxl.utils.exceptions.InvalidFileException) as exc:
        resultado.agregar_error(0, f'No se pudo leer Excel (.xlsx): {exc}')
        return resultado
    finally:
        if wb is not None:
            wb.close()


def generar_plantilla_csv():
    """Ejemplo con profundidad explícita y relación SAT opcional."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['cuenta', 'descripcion', 'nivel', 'codigoagrupador'])
    writer.writerow(['1000', 'Caja', '1', ''])
    writer.writerow(['1000.01', 'Caja y efectivo', '2', ''])
    writer.writerow(['1100', 'Bancos', '1', ''])
    writer.writerow(['1100.01', 'Bancos nacionales', '2', ''])
    return output.getvalue()
