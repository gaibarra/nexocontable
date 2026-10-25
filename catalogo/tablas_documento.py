"""Distribución compartida de columnas de normas para HTML y Word."""
import re
import unicodedata


def _clave(texto):
    texto = unicodedata.normalize('NFKD', texto).casefold()
    return re.sub(r'[^a-z0-9]', '', texto)


def anchos_normas(encabezados):
    if len(encabezados) != 3:
        return None
    primero, segundo = (_clave(e) for e in encabezados[:2])
    es_norma = primero in ('norma', 'normas', 'niif', 'nif', 'nic', 'ifrs', 'niififrs', 'nifniif', 'codigo')
    return [13, 29, 58] if es_norma and segundo in ('titulo', 'nombre', 'denominacion') else None


def ajustar_tablas(html):
    for tabla in html.find_all('table'):
        fila = tabla.find('tr')
        if fila is None:
            continue
        encabezados = [c.get_text(' ', strip=True) for c in fila.find_all(['th', 'td'], recursive=False)]
        anchos = anchos_normas(encabezados)
        if not anchos:
            continue
        tabla['class'] = list(tabla.get('class', [])) + ['document-standards-table']
        grupo = html.new_tag('colgroup')
        for ancho in anchos:
            col = html.new_tag('col'); col['style'] = f'width: {ancho}%'
            grupo.append(col)
        tabla.insert(0, grupo)
        contenedor = html.new_tag('div')
        contenedor['class'] = 'document-table-scroll'
        contenedor['tabindex'] = '0'
        contenedor['role'] = 'region'
        contenedor['aria-label'] = 'Tabla de normas contables'
        tabla.wrap(contenedor)
