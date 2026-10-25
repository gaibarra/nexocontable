from django import template
from panel.crud import configuracion, protegido

register = template.Library()


@register.inclusion_tag('panel/acciones.html', takes_context=True)
def acciones(context, tipo, registro):
    user = context['request'].user
    config = configuracion(tipo)
    editable = user.acceso_panel.rol in config[3] and bool(config[4]) and not protegido(tipo, registro, user)
    return {'tipo': tipo, 'registro': registro, 'editable': editable, 'nombre': config[1]}
