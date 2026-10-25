"""Proveedores de IA configurados exclusivamente en el servidor."""
import logging

from django.conf import settings
from openai import OpenAI, APIError, APIConnectionError, RateLimitError

logger = logging.getLogger(__name__)


class ManualGenerationError(Exception):
    """Mensaje de fallo seguro para la interfaz de usuario."""

    def __init__(self, mensaje, consumos=None):
        super().__init__(mensaje)
        self.consumos = consumos or []


class TextoGenerado(str):
    """Conserva la compatibilidad del texto y adjunta el uso reportado por la API."""

    def __new__(cls, contenido, consumos):
        resultado = super().__new__(cls, contenido)
        resultado.consumos = consumos
        return resultado


def _contador(usage, campo):
    valor = getattr(usage, campo, None)
    return valor if type(valor) is int and valor >= 0 else None


def _consumo(response, proveedor, modelo, completo):
    usage = getattr(response, 'usage', None)
    entrada = _contador(usage, 'prompt_tokens')
    salida = _contador(usage, 'completion_tokens')
    total = _contador(usage, 'total_tokens')
    if total is None and entrada is not None and salida is not None:
        total = entrada + salida
    return {'proveedor': proveedor, 'modelo': modelo, 'entrada': entrada,
            'salida': salida, 'total': total,
            'resultado': 'completo' if completo else 'incompleto'}


def generar_texto(system_prompt, prompt):
    proveedores = {
        'openai': (settings.OPENAI_API_KEY, settings.OPENAI_MODEL,
                   settings.OPENAI_MAX_TOKENS, 'https://api.openai.com/v1'),
        'deepseek': (settings.DEEPSEEK_API_KEY, settings.DEEPSEEK_MODEL,
                     settings.DEEPSEEK_MAX_TOKENS, 'https://api.deepseek.com'),
    }
    orden = [settings.AI_PROVIDER]
    if settings.AI_FALLBACK_PROVIDER and settings.AI_FALLBACK_PROVIDER not in orden:
        orden.append(settings.AI_FALLBACK_PROVIDER)
    if any(nombre not in proveedores for nombre in orden):
        logger.error('Configuración de proveedor de IA inválida')
        raise ManualGenerationError('El servicio de IA requiere configuración. Contacta al administrador.')

    consumos = []
    mensaje = 'No se pudo generar el manual. Intenta más tarde o contacta al administrador.'
    for nombre in orden:
        clave, modelo, max_tokens, base_url = proveedores[nombre]
        if not clave:
            logger.warning('Proveedor de IA sin clave: %s', nombre)
            continue
        try:
            # Sin reintentos internos: el respaldo debe caber en el tiempo de la petición web.
            with OpenAI(api_key=clave, base_url=base_url,
                        timeout=settings.AI_TIMEOUT_SECONDS, max_retries=0) as client:
                opciones = {}
                if nombre == 'deepseek':
                    # El modo de razonamiento está activo por defecto y comparte
                    # el presupuesto de salida. Aquí necesitamos el manual final.
                    opciones['extra_body'] = {'thinking': {'type': 'disabled'}}
                response = client.chat.completions.create(
                    model=modelo,
                    messages=[{'role': 'system', 'content': system_prompt},
                              {'role': 'user', 'content': prompt}],
                    max_tokens=max_tokens,
                    temperature=0.5,
                    **opciones,
                )
            choice = response.choices[0] if response.choices else None
            contenido = choice.message.content if choice else None
            completo = bool(contenido and contenido.strip() and choice.finish_reason == 'stop')
            consumos.append(_consumo(response, nombre, modelo, completo))
            if not completo:
                motivo = choice.finish_reason if choice else 'sin_opciones'
                logger.warning(
                    'Respuesta de IA vacía o incompleta: proveedor=%s modelo=%s motivo=%s '
                    'limite_tokens=%s caracteres=%s tokens_salida=%s',
                    nombre, modelo, motivo, max_tokens, len(contenido or ''),
                    getattr(getattr(response, 'usage', None), 'completion_tokens', None))
                if motivo == 'length':
                    mensaje = ('El manual excedió el límite de extensión y quedó incompleto. '
                               'Selecciona menos cuentas para generar un manual completo; '
                               'el administrador también puede ampliar el límite de generación.')
                elif motivo == 'content_filter':
                    mensaje = ('El servicio de IA no pudo completar esta solicitud por un filtro de contenido. '
                               'Revisa las descripciones de las cuentas seleccionadas.')
                else:
                    mensaje = ('El servicio de IA devolvió una respuesta vacía o incompleta. '
                               'Vuelve a intentarlo; si persiste, contacta al administrador.')
                continue
            logger.info('Manual generado: proveedor=%s modelo=%s tokens=%s',
                        nombre, modelo, getattr(getattr(response, 'usage', None), 'total_tokens', None))
            return TextoGenerado(contenido, consumos)
        except (APIError, APIConnectionError) as exc:
            consumos.append({'proveedor': nombre, 'modelo': modelo, 'entrada': None,
                             'salida': None, 'total': None, 'resultado': 'error'})
            # No registrar cuerpos de respuesta, prompts ni credenciales.
            code = getattr(exc, 'code', None)
            tipo = getattr(exc, 'type', None)
            status = getattr(exc, 'status_code', None)
            logger.warning('Fallo de IA: proveedor=%s status=%s code=%s type=%s',
                           nombre, status, code, tipo)
            if code == 'credit_balance_exhausted' or status == 402:
                mensaje = ('Se agotó el saldo del servicio de IA. '
                           'El administrador debe recargar el saldo.')
            elif tipo == 'insufficient_quota' or code in {
                'insufficient_quota', 'billing_limit_reached',
                'organization_usage_limit_exceeded', 'project_usage_limit_exceeded',
            }:
                mensaje = ('El servicio de IA alcanzó su cuota o límite de gasto. '
                           'El administrador debe revisar la facturación y los límites.')
            elif isinstance(exc, RateLimitError):
                mensaje = 'El servicio de IA recibió demasiadas solicitudes. Espera un minuto y vuelve a intentarlo.'
    raise ManualGenerationError(mensaje, consumos=consumos)
