import re
import markdown
import bleach
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# Tags HTML permitidos para el contenido del manual contable
ALLOWED_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'hr',
    'strong', 'em', 'b', 'i', 'u',
    'ul', 'ol', 'li',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'pre', 'code', 'blockquote',
    'a',
    'div', 'span',
    'dl', 'dt', 'dd',
    'sup', 'sub',
]

def clase_codigo_segura(tag, nombre, valor):
    if nombre != 'class':
        return False
    return all(token in ('codehilite', 'highlight') or re.fullmatch(r'language-[a-zA-Z0-9_+-]{1,30}', token) or (tag == 'span' and re.fullmatch(r'[a-z]{1,3}', token)) for token in valor.split())


# Atributos permitidos por tag
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'th': ['colspan', 'rowspan', 'scope'],
    'td': ['colspan', 'rowspan'],
    'code': clase_codigo_segura,
    'pre': clase_codigo_segura,
    'div': clase_codigo_segura,
    'span': clase_codigo_segura,
}


def preparar_listas(texto):
    """Reconoce viñetas tras párrafos sin alterar bloques de código ni HTML."""
    lineas, cerca, html = [], None, False
    for linea in str(texto).splitlines():
        marca = re.match(r'^\s*(`{3,}|~{3,})', linea)
        if marca:
            tipo = marca.group(1)[0]
            cerca = None if cerca == tipo else tipo
        if re.search(r'<(?:pre|code|table|ul|ol)\b', linea, re.I):
            html = True
        if not cerca and not html and re.match(r'^[-+*]\s+\S', linea) and lineas and lineas[-1].strip() and not re.match(r'^\s*[-+*]\s+', lineas[-1]):
            lineas.append('')
        lineas.append(linea)
        if re.search(r'</(?:pre|code|table|ul|ol)>', linea, re.I):
            html = False
    return '\n'.join(lineas)


@register.filter
def render_markdown(value):
    """
    Convierte texto Markdown a HTML sanitizado.
    Primero convierte Markdown → HTML, luego sanitiza con bleach
    para prevenir inyección de scripts (XSS).
    """
    if not value:
        return ''

    # Convertir Markdown a HTML
    html_content = markdown.markdown(
        preparar_listas(value),
        extensions=['extra', 'codehilite', 'tables', 'toc', 'sane_lists']
    )

    # Sanitizar HTML para prevenir XSS
    clean_html = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )

    return mark_safe(clean_html)
