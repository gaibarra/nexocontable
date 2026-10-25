"""Conciliación autoritativa por recurso de pago, sin acciones de cobro o devolución."""
import hashlib
import hmac
import logging
import re
import time
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import connection, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .models import Donativo, PagoMercadoPago

logger = logging.getLogger(__name__)
ESTADOS = {'approved': 'aprobado', 'rejected': 'rechazado', 'refunded': 'reembolsado',
           'cancelled': 'cancelado', 'charged_back': 'contracargo', 'pending': 'pendiente',
           'in_process': 'pendiente', 'authorized': 'pendiente', 'in_mediation': 'en_revision'}


class ErrorProveedor(Exception):
    pass


class PagoInconsistente(Exception):
    pass


def importe(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)) or len(str(value)) > 32:
        raise ValueError('Importe inválido')
    try:
        result = Decimal(str(value))
        if not result.is_finite() or result < 0 or result > Decimal('100000.00'):
            raise ValueError('Importe fuera de rango')
        if result != result.quantize(Decimal('.01')):
            raise ValueError('Máximo dos decimales')
    except InvalidOperation:
        raise ValueError('Importe inválido')
    return result


def sdk_mp():
    import mercadopago
    from mercadopago.config import RequestOptions
    if not settings.MERCADOPAGO_ACCESS_TOKEN:
        raise ErrorProveedor('Falta configuración de API')
    return mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN,
                          request_options=RequestOptions(connection_timeout=6.0, max_retries=0))


def respuesta_api(result, success=(200,)):
    if not isinstance(result, dict) or result.get('status') not in success or not isinstance(result.get('response'), dict):
        raise ErrorProveedor('Respuesta de API no disponible o inválida')
    return result['response']


def checkout_url(value):
    if not isinstance(value, str) or len(value) > 2048:
        return ''
    try:
        parsed = urlparse(value)
        host = parsed.hostname or ''
        trusted = any(host == domain or host.endswith('.' + domain) for domain in ('mercadopago.com.mx', 'mercadopago.com'))
        if parsed.scheme != 'https' or not trusted or parsed.username or parsed.password or parsed.port not in (None, 443):
            return ''
    except ValueError:
        return ''
    return value


def firma_valida(request, payment_id):
    secret = settings.MERCADOPAGO_WEBHOOK_SECRET
    if not secret:
        return False
    signature = request.headers.get('x-signature', '')
    request_id = request.headers.get('x-request-id', '')
    if len(signature) > 512 or not request_id or len(request_id) > 200:
        return False
    parts = {}
    for part in signature.split(','):
        key, sep, value = part.strip().partition('=')
        if not sep or key in parts:
            return False
        parts[key] = value
    ts, v1 = parts.get('ts', ''), parts.get('v1', '')
    if not re.fullmatch(r'[0-9]{1,16}', ts) or not re.fullmatch(r'[0-9a-fA-F]{64}', v1):
        return False
    tolerance = settings.MERCADOPAGO_WEBHOOK_TOLERANCE_SECONDS
    if tolerance:
        timestamp = int(ts) / (1000 if len(ts) > 11 else 1)
        if abs(time.time() - timestamp) > tolerance:
            return False
    manifest = f'id:{str(payment_id).lower()};request-id:{request_id};ts:{ts};'
    digest = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, v1.lower())


def limitar_espera_bloqueo():
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL lock_timeout = '3s'")


def validar_pago(payment, payment_id, obj, collector):
    if str(payment.get('id')) != payment_id or payment.get('external_reference') != str(obj.pk):
        raise PagoInconsistente('ID o referencia no coinciden')
    try:
        monto = importe(payment.get('transaction_amount'))
        reembolsado = importe(payment.get('transaction_amount_refunded', 0))
        fecha = parse_datetime(str(payment.get('date_last_updated', '')))
    except (ValueError, TypeError):
        raise PagoInconsistente('Importe o fecha inválidos')
    if fecha is None or timezone.is_naive(fecha):
        raise ErrorProveedor('No hay fecha de actualización verificable')
    if monto != obj.monto or reembolsado > monto or payment.get('currency_id') != 'MXN':
        raise PagoInconsistente('Monto o moneda no coinciden')
    if payment.get('live_mode') is not (not settings.MERCADOPAGO_SANDBOX):
        raise PagoInconsistente('Entorno de pago incorrecto')
    if not collector or str(payment.get('collector_id')) != collector:
        raise PagoInconsistente('Receptor del pago no coincide')
    if settings.MERCADOPAGO_COLLECTOR_ID and collector != settings.MERCADOPAGO_COLLECTOR_ID:
        raise PagoInconsistente('Receptor distinto al configurado')
    status = payment.get('status')
    if status not in ESTADOS:
        raise PagoInconsistente('Estado no reconocido')
    if status == 'refunded':
        reembolsado = monto
    resumen = {key: payment.get(key) for key in ('id', 'status', 'status_detail', 'transaction_amount',
        'transaction_amount_refunded', 'currency_id', 'collector_id', 'live_mode', 'date_last_updated')}
    return {'estado': status, 'monto': monto, 'reembolsado': reembolsado, 'actualizado_en': fecha, 'resumen': resumen}


def guardar_intento(obj, payment_id, datos):
    pago = PagoMercadoPago.objects.select_for_update().filter(pago_id=payment_id).first()
    if pago:
        if pago.donativo_id != obj.pk:
            raise PagoInconsistente('El pago pertenece a otro donativo')
        if datos['actualizado_en'] <= pago.actualizado_en:
            return False
        for key, value in datos.items():
            setattr(pago, key, value)
        pago.save(update_fields=list(datos))
    else:
        PagoMercadoPago.objects.create(pago_id=payment_id, donativo=obj, **datos)
    return True


def resumir_intentos(obj):
    pagos = list(obj.pagos_mp.all())
    aprobados = [p for p in pagos if p.estado == 'approved' and p.monto > p.reembolsado]
    obj.monto_confirmado = sum((p.monto - p.reembolsado for p in aprobados), Decimal('0'))
    obj.monto_reembolsado = sum((p.reembolsado for p in pagos), Decimal('0'))
    if aprobados:
        obj.estado = 'parcial' if obj.monto_reembolsado else 'aprobado'
        principal = max(aprobados, key=lambda p: p.actualizado_en)
    else:
        principal = max(pagos, key=lambda p: p.actualizado_en)
        obj.estado = ESTADOS[principal.estado]
        if principal.estado == 'approved' and principal.reembolsado == principal.monto:
            obj.estado = 'reembolsado'
    obj.referencia_mp = principal.pago_id
    obj.pago_actualizado_en = max(p.actualizado_en for p in pagos)
    obj.datos_webhook = principal.resumen


def conciliar(payment_id):
    sdk = sdk_mp()
    payment = respuesta_api(sdk.payment().get(payment_id))
    ref = payment.get('external_reference')
    if not isinstance(ref, str) or not re.fullmatch(r'[0-9]{1,18}', ref):
        raise PagoInconsistente('Referencia de donativo inválida')
    with transaction.atomic():
        limitar_espera_bloqueo()
        obj = Donativo.objects.select_for_update().filter(pk=int(ref)).first()
        if obj is None:
            return 'sin_registro'
        if not obj.preference_id:
            raise PagoInconsistente('El donativo no tiene checkout asociado')
        collector = obj.collector_mp
        if not collector:
            preference = respuesta_api(sdk.preference().get(obj.preference_id))
            if str(preference.get('id')) != obj.preference_id or preference.get('external_reference') != str(obj.pk):
                raise PagoInconsistente('La preferencia no coincide')
            collector = str(preference.get('collector_id') or '')
        datos = validar_pago(payment, payment_id, obj, collector)
        # Un intento rechazado distinto no invalida una aprobación histórica.
        if obj.referencia_mp and obj.referencia_mp != payment_id and not obj.pagos_mp.exists() and obj.estado in ('aprobado', 'parcial', 'reembolsado', 'contracargo'):
            if payment.get('status') != 'approved':
                return 'otro_intento_ignorado'
            if not re.fullmatch(r'[0-9]{1,64}', obj.referencia_mp):
                raise PagoInconsistente('Referencia histórica requiere revisión')
            anterior = respuesta_api(sdk.payment().get(obj.referencia_mp))
            guardar_intento(obj, obj.referencia_mp, validar_pago(anterior, obj.referencia_mp, obj, collector))
        if not guardar_intento(obj, payment_id, datos):
            return 'duplicado_o_anterior'
        resumir_intentos(obj)
        obj.collector_mp = collector
        payer = payment.get('payer')
        email = payer.get('email') if isinstance(payer, dict) else None
        if not obj.email_donante and isinstance(email, str) and len(email) <= 254:
            try:
                validate_email(email.strip())
                obj.email_donante = email.strip().lower()
            except ValidationError:
                pass
        obj.save(update_fields=['estado', 'referencia_mp', 'collector_mp', 'pago_actualizado_en', 'monto_confirmado', 'monto_reembolsado', 'datos_webhook', 'email_donante'])
    return 'actualizado'
