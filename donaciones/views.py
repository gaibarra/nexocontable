import json
import logging
import re
import secrets
from decimal import Decimal
from uuid import UUID, uuid4
from urllib.parse import urlencode, urlparse
from django.conf import settings
from django.contrib import messages
from django.core import signing
from django.db import transaction, DatabaseError
from django.db.models import F, Value, Case, When, CharField
from django.db.models.functions import Lower, Trim, Concat, Cast
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods, require_safe
from .models import Donativo
from .mercadopago_service import (importe, sdk_mp, respuesta_api, checkout_url,
                                 firma_valida, conciliar, limitar_espera_bloqueo, ErrorProveedor, PagoInconsistente)

logger = logging.getLogger(__name__)
MONTOS_SUGERIDOS = [250, 500, 1000, 2000]
MONTO_DEFAULT = 500
COLABORADORES_BASE = 40


def _verify_mercadopago_signature(request, payment_id):
    return firma_valida(request, str(payment_id))


def contar_colaboradores():
    # El correo vacío no identifica a todos los anónimos como la misma persona.
    qs = Donativo.objects.filter(estado__in=['aprobado', 'parcial'])
    return qs.annotate(email_normalizado=Lower(Trim('email_donante'))).annotate(persona=Case(
        When(email_normalizado__gt='', then=Concat(Value('email:'), F('email_normalizado'))),
        When(usuario__isnull=False, then=Concat(Value('usuario:'), Cast('usuario_id', CharField()))),
        default=Concat(Value('anonimo:'), Cast('pk', CharField())), output_field=CharField()
    )).order_by().values('persona').distinct().count()


def _checkout_token(request):
    if 'donation_checkout_nonce' not in request.session:
        request.session['donation_checkout_nonce'] = secrets.token_urlsafe(24)
    return signing.dumps({'nonce': request.session['donation_checkout_nonce'], 'clave': str(uuid4())}, salt='mp-checkout')


def _checkout_key(request):
    try:
        data = signing.loads(request.POST.get('checkout_token', ''), salt='mp-checkout', max_age=3600)
        nonce = request.session.get('donation_checkout_nonce')
        if not isinstance(data, dict) or not nonce or data.get('nonce') != nonce:
            return None
        return UUID(data['clave'])
    except (signing.BadSignature, KeyError, TypeError, ValueError):
        return None


def _retorno_params(obj):
    return urlencode({'donativo_id': obj.pk, 'token': signing.dumps({'id': obj.pk}, salt='mp-retorno')})


@never_cache
@require_http_methods(['GET', 'POST'])
def donar(request):
    if request.method == 'POST':
        try:
            raw = request.POST.get('monto_custom', '').strip() or request.POST.get('monto', '').strip()
            monto = importe(raw)
            if monto < Decimal('10'):
                raise ValueError('Mínimo 10 MXN')
        except ValueError:
            messages.error(request, 'Indica un monto entre $10 y $100,000 MXN, con un máximo de dos decimales.')
            return redirect('donar')
        clave = _checkout_key(request)
        if clave is None:
            messages.warning(request, 'El formulario de donativo caducó. Selecciona de nuevo el monto para continuar.')
            return redirect('donar')
        if not settings.MERCADOPAGO_ACCESS_TOKEN or not settings.MERCADOPAGO_WEBHOOK_SECRET:
            messages.error(request, 'Los donativos con Mercado Pago no están disponibles temporalmente. Intenta más tarde.')
            return redirect('donar')
        base = settings.MERCADOPAGO_BASE_URL
        parsed = urlparse(base)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.query or parsed.fragment or parsed.path not in ('', '/'):
            logger.error('MP: URL de retorno no válida')
            messages.error(request, 'No se pudo preparar el donativo. Contacta al administrador.')
            return redirect('donar')
        try:
            with transaction.atomic():
                limitar_espera_bloqueo()
                obj, _ = Donativo.objects.get_or_create(checkout_clave=clave, defaults={
                    'usuario': request.user if request.user.is_authenticated else None,
                    'nombre_donante': request.user.get_full_name() if request.user.is_authenticated else 'Anónimo',
                    'email_donante': request.user.email if request.user.is_authenticated else '', 'monto': monto})
                obj = Donativo.objects.select_for_update().get(pk=obj.pk)
                expected_user = request.user.pk if request.user.is_authenticated else None
                if obj.monto != monto or obj.usuario_id != expected_user:
                    messages.warning(request, 'El monto o la cuenta cambió. Abre de nuevo el formulario de donativo.')
                    return redirect('donar')
                if obj.estado not in ('pendiente', 'error_checkout'):
                    messages.info(request, 'Esta solicitud ya fue procesada. Revisa su resultado antes de iniciar otro donativo.')
                    return redirect('donar')
                if obj.checkout_url and obj.estado == 'pendiente':
                    target = checkout_url(obj.checkout_url)
                    if target:
                        return redirect(target)
                    raise ErrorProveedor('URL guardada inválida')
                params = _retorno_params(obj)
                preference_data = {'items': [{'title': 'Donativo - Manual Contable AI', 'description': 'Apoyo a la comunidad contable de México',
                    'quantity': 1, 'unit_price': float(monto), 'currency_id': 'MXN'}],
                    'external_reference': str(obj.pk), 'auto_return': 'approved',
                    'back_urls': {'success': f'{base}/donar/exito/?{params}', 'failure': f'{base}/donar/error/?{params}', 'pending': f'{base}/donar/pendiente/?{params}'},
                    'notification_url': f'{base}/donar/webhook/'}
                try:
                    from mercadopago.config import RequestOptions
                    options = RequestOptions(connection_timeout=6.0, max_retries=0,
                                             custom_headers={'x-idempotency-key': str(clave)})
                    result = sdk_mp().preference().create(preference_data, request_options=options)
                    pref = respuesta_api(result, (200, 201))
                    target = checkout_url(pref.get('sandbox_init_point') if settings.MERCADOPAGO_SANDBOX else pref.get('init_point'))
                    collector = str(pref.get('collector_id') or '')
                    preference_id = pref.get('id')
                    if not target or not isinstance(preference_id, str) or not 1 <= len(preference_id) <= 100 or not collector:
                        raise ErrorProveedor('Preferencia incompleta')
                    if settings.MERCADOPAGO_COLLECTOR_ID and collector != settings.MERCADOPAGO_COLLECTOR_ID:
                        raise ErrorProveedor('Receptor distinto al configurado')
                    obj.preference_id = preference_id
                    obj.checkout_url = target
                    obj.collector_mp = collector
                    obj.estado = 'pendiente'
                    obj.save(update_fields=['preference_id', 'checkout_url', 'collector_mp', 'estado'])
                    return redirect(target)
                except Exception as exc:
                    # Conserva la referencia para reintentos ante resultados remotos inciertos.
                    obj.estado = 'error_checkout'
                    obj.save(update_fields=['estado'])
                    logger.error('MP checkout no disponible: donativo=%s tipo=%s', obj.pk, type(exc).__name__)
                    messages.error(request, 'No se pudo abrir Mercado Pago. No se ha confirmado ningún cargo; vuelve a intentarlo.')
        except (DatabaseError, ErrorProveedor) as exc:
            logger.error('MP: no se pudo preparar el checkout, tipo=%s', type(exc).__name__)
            messages.error(request, 'No se pudo preparar el donativo. Inténtalo de nuevo.')
        return redirect('donar')
    total = contar_colaboradores()
    return render(request, 'donaciones/donar.html', {'montos_sugeridos': MONTOS_SUGERIDOS,
        'monto_default': MONTO_DEFAULT, 'total_donantes': total, 'total_colaboradores': total + COLABORADORES_BASE,
        'base_colaboradores': COLABORADORES_BASE, 'checkout_token': _checkout_token(request)})


def _resultado(request):
    obj = None
    try:
        data = signing.loads(request.GET.get('token', ''), salt='mp-retorno', max_age=7*86400)
        ref = request.GET.get('donativo_id', '')
        if isinstance(data, dict) and re.fullmatch(r'[0-9]{1,18}', ref) and data.get('id') == int(ref):
            obj = Donativo.objects.filter(pk=int(ref)).first()
    except (signing.BadSignature, TypeError, ValueError):
        pass
    estado = obj.estado if obj else 'pendiente'
    return render(request, 'donaciones/resultado.html', {'estado_pago': estado,
        'exito': estado in ('aprobado', 'parcial'), 'pendiente': estado in ('pendiente', 'error_checkout'),
        'verificable': obj is not None})


@never_cache
@require_safe
def donativo_exito(request):
    return _resultado(request)


@never_cache
@require_safe
def donativo_error(request):
    return _resultado(request)


@never_cache
@require_safe
def donativo_pendiente(request):
    return _resultado(request)


@csrf_exempt
@require_POST
def webhook_mercadopago(request):
    # HMAC autentica servidor a servidor; el formulario público conserva CSRF.
    if not settings.MERCADOPAGO_WEBHOOK_SECRET or not settings.MERCADOPAGO_ACCESS_TOKEN:
        return HttpResponse(status=503)
    try:
        if len(request.body) > 65536:
            return HttpResponse(status=413)
        data = json.loads(request.body)
        if not isinstance(data, dict) or not isinstance(data.get('data', {}), dict):
            return HttpResponse(status=400)
        topic = data.get('type') or request.GET.get('type')
        if topic != 'payment':
            return HttpResponse(status=200)
        body_id = data.get('data', {}).get('id')
        query_ids = request.GET.getlist('data.id')
        if len(query_ids) > 1:
            return HttpResponse(status=400)
        payment_id = query_ids[0] if query_ids else str(body_id or '')
        if not re.fullmatch(r'[0-9]{1,64}', payment_id) or (body_id is not None and str(body_id) != payment_id):
            return HttpResponse(status=400)
        if not firma_valida(request, payment_id):
            logger.warning('MP: webhook rechazado por firma inválida')
            return HttpResponse(status=401)
        resultado = conciliar(payment_id)
        logger.info('MP: notificación procesada, resultado=%s', resultado)
        return HttpResponse(status=200)
    except (ValueError, UnicodeDecodeError):
        return HttpResponse(status=400)
    except PagoInconsistente as exc:
        logger.warning('MP: conciliación rechazada, motivo=%s', str(exc))
        return HttpResponse(status=409)
    except Exception as exc:
        logger.error('MP: notificación reintentable, tipo=%s', type(exc).__name__)
        return HttpResponse(status=503)
