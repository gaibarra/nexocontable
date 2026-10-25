"""Catálogo oficial del Anexo 24; disponible sin llamadas externas por usuario."""
import json
import re
import unicodedata
from difflib import SequenceMatcher
from html.parser import HTMLParser
from pathlib import Path
from django.db import transaction
from .models import CodigoAgrupador

FUENTE_SAT = 'https://sidof.segob.gob.mx/notas/docFuente/5778160'
ARCHIVO_SAT = Path(__file__).parent / 'data' / 'sat_2026.json'

class TablaSATParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.filas = []
        self.celdas = []
        self.texto = None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.celdas = []
        elif tag == 'td':
            self.texto = []

    def handle_data(self, data):
        if self.texto is not None:
            self.texto.append(data)

    def handle_endtag(self, tag):
        if tag == 'td' and self.texto is not None:
            self.celdas.append(' '.join(''.join(self.texto).split()))
            self.texto = None
        elif tag == 'tr' and len(self.celdas) == 3:
            nivel, codigo, nombre = self.celdas
            if nivel in ('1', '2') and re.fullmatch(r'[1-8]\d{2}(?:\.\d{2})?', codigo):
                self.filas.append(dict(nivel=int(nivel), codigoagrupador=codigo, nombre=nombre))


def asegurar_catalogo_sat():
    """Carga la referencia oficial incluida si aún no se ha inicializado."""
    filas = json.loads(ARCHIVO_SAT.read_text(encoding='utf-8'))['cuentas']
    existentes = set(CodigoAgrupador.objects.values_list('codigoagrupador', flat=True))
    filas = [fila for fila in filas if fila['codigoagrupador'] not in existentes]
    if not filas:
        return
    with transaction.atomic():
        CodigoAgrupador.objects.bulk_create(
            [CodigoAgrupador(**fila) for fila in filas], ignore_conflicts=True)


def normalizar(texto):
    texto = ''.join(c for c in unicodedata.normalize('NFKD', texto.lower()) if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[a-z0-9]+', texto))


def sugerir_relacion(descripcion, codigos):
    """Sugerencia por descripción; nunca interpreta el número propio como SAT."""
    texto = normalizar(descripcion)
    candidatos = []
    for codigo in codigos:
        nombre = normalizar(codigo.nombre)
        exacta = texto == nombre
        palabras = set(texto.split()) & set(nombre.split())
        if not palabras:
            continue
        puntaje = 1.0 if exacta else SequenceMatcher(None, texto, nombre).ratio()
        if puntaje >= 0.60:
            candidatos.append((puntaje, codigo))
    candidatos.sort(key=lambda item: (-item[0], item[1].codigoagrupador))
    if not candidatos or (len(candidatos) > 1 and candidatos[0][0] - candidatos[1][0] < 0.08):
        return None, None
    return candidatos[0][1], round(candidatos[0][0] * 100)
