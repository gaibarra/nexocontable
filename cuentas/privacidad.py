"""Aviso versionado y constancia de la manifestación de consentimiento."""
import hashlib
from django.conf import settings
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.decorators.http import require_safe

VERSION_AVISO = '2026-10-25'
PLANTILLA_AVISO = 'legal/aviso_2026_10_25.html'


def datos_aviso():
    nombres = {'openai': 'OpenAI', 'deepseek': 'DeepSeek'}
    return {
        'responsable': settings.PRIVACY_CONTROLLER_NAME,
        'domicilio': settings.PRIVACY_CONTROLLER_ADDRESS,
        'correo': settings.PRIVACY_CONTACT_EMAIL,
        'version': VERSION_AVISO,
        'fecha': '25 de octubre de 2026',
        'proveedor_ia': nombres.get(settings.AI_PROVIDER, 'Proveedor configurado de IA'),
        'respaldo_ia': nombres.get(settings.AI_FALLBACK_PROVIDER, ''),
    }


def contexto_privacidad(request):
    return {'privacidad': datos_aviso()}


def huella_aviso():
    return hashlib.sha256(render_to_string(PLANTILLA_AVISO, {'privacidad': datos_aviso()}).encode()).hexdigest()


@require_safe
def aviso_privacidad(request):
    return render(request, 'legal/privacidad.html', {'privacidad': datos_aviso()})
