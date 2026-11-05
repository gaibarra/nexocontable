"""Composición de salida sin alterar el contenido ni la identidad aprobada."""
import re
import unicodedata
from bs4 import BeautifulSoup, Tag
from .templatetags.markdown_filters import render_markdown
from .tablas_documento import ajustar_tablas


def _normalizar(texto):
    texto = unicodedata.normalize('NFKC', texto).casefold()
    return re.sub(r'\s+', ' ', texto).strip(' \"“”\'«»')


def componer_manual(manual):
    from .biblioteca import anexo
    html = BeautifulSoup(str(render_markdown(manual.contenido)), 'html.parser')
    bloque_fuentes = html.new_tag('section', attrs={'class': 'document-fundamentos'})
    for nodo in list(BeautifulSoup(str(render_markdown(anexo(manual))), 'html.parser').contents):
        bloque_fuentes.append(nodo)
    html.append(bloque_fuentes)
    titulo = manual.titulo
    automatico = bool(re.match(r'^Manual:\s*', titulo, re.I))
    primero = next((n for n in html.children if isinstance(n, Tag) and n.get_text(strip=True)), None)
    if primero is not None and primero.name in ('h1', 'h2'):
        texto = primero.get_text(' ', strip=True)
        if _normalizar(texto) == _normalizar(titulo) or (automatico and re.match(r'^manual\b', texto, re.I)):
            titulo = texto
            primero.decompose()
    if automatico and titulo == manual.titulo:
        titulo = re.sub(r'^Manual:\s*', 'Manual contable — ', titulo, flags=re.I)

    cuentas = list(manual.cuentas.all()) + list(manual.codigos_sat.all())
    if automatico and cuentas:
        from types import SimpleNamespace
        from .perfil_contable import titulo_cuenta
        c=cuentas[0]
        titulo=titulo_cuenta(SimpleNamespace(cuenta=getattr(c,'cuenta',None) or c.codigoagrupador,descripcion=getattr(c,'descripcion',None) or getattr(c,'nombre','')))
    alcance = []
    descripciones = set()
    for cuenta in cuentas:
        clave = getattr(cuenta, 'cuenta', None) or cuenta.codigoagrupador
        descripcion = getattr(cuenta, 'descripcion', None) or getattr(cuenta, 'nombre', '')
        if descripcion:
            descripciones.add(_normalizar(descripcion))
        alcance.append({'clave': str(clave), 'descripcion': descripcion})

    # Solo abrevia la etiqueta introductoria reconocible; las notas técnicas se conservan.
    vistos = {_normalizar(titulo)}
    for nodo in list(html.children)[:12]:
        if not isinstance(nodo, Tag):
            continue
        texto = nodo.get_text(' ', strip=True)
        if nodo.name not in ('p', 'h1', 'h2', 'h3'):
            break
        if re.match(r'^(?:\d+[.)]\s*)?(introducci[oó]n|objetivo|alcance|nota t[eé]cnica)\b', texto, re.I):
            break
        codigo = re.fullmatch(r'C[oó]digo\s+SAT\s*:\s*([\w.\-]+)\s*[—–-]\s*(.+)', texto, re.I)
        if codigo and _normalizar(codigo.group(2)) in descripciones and _normalizar(codigo.group(2)) in vistos:
            nodo.clear()
            etiqueta = html.new_tag('strong'); etiqueta.string = 'Código SAT: '
            nodo.append(etiqueta); nodo.append(codigo.group(1))
        vistos.add(_normalizar(texto))

    introduccion = _normalizar(html.get_text(' ', strip=True)[:2500])
    faltantes = [c for c in alcance if not c['descripcion'] or _normalizar(c['descripcion']) not in introduccion]
    ajustar_tablas(html)
    for etiqueta in html.find_all('p'):
        texto = etiqueta.get_text(' ', strip=True)
        if len(texto) <= 180 and re.match(r'^(?:Asiento(?:\s+contable|\s+\d+)?|Cuenta\s+T)\b', texto, re.I):
            etiqueta['class'] = list(etiqueta.get('class', [])) + ['document-entry-caption']
    from .estilo_documento import estilizar
    estilizar(html)
    return {'titulo': titulo, 'contenido_html': str(html), 'alcance': faltantes}
