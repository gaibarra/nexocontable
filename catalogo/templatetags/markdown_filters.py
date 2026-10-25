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
    'a', 'img',
    'div', 'span',
    'dl', 'dt', 'dd',
    'sup', 'sub',
]

# Atributos permitidos por tag
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'th': ['colspan', 'rowspan', 'scope'],
    'td': ['colspan', 'rowspan'],
    'code': ['class'],
    'pre': ['class'],
    'div': ['class'],
    'span': ['class'],
}


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
        value,
        extensions=['extra', 'codehilite', 'tables', 'toc']
    )

    # Sanitizar HTML para prevenir XSS
    clean_html = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )

    return mark_safe(clean_html)
