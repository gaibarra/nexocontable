import json
import logging
import hmac
import hashlib
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.db.models import Sum

from .models import Donativo

logger = logging.getLogger(__name__)

# Montos sugeridos para donativo (MXN)
MONTOS_SUGERIDOS = [250, 500, 1000, 2000]
MONTO_DEFAULT = 500


def _verify_mercadopago_signature(request, payment_id):
    """Valida firma del webhook de Mercado Pago usando HMAC SHA256."""
    secret = getattr(settings, 'MERCADOPAGO_WEBHOOK_SECRET', '')
    if not secret:
        return settings.DEBUG

    x_signature = request.headers.get('x-signature', '')
    x_request_id = request.headers.get('x-request-id', '')
    if not x_signature or not x_request_id or not payment_id:
        return False

    parts = {}
    for item in x_signature.split(','):
        if '=' in item:
            key, value = item.split('=', 1)
            parts[key.strip()] = value.strip()

    ts = parts.get('ts')
    v1 = parts.get('v1')
    if not ts or not v1:
        return False

    manifest = f"id:{payment_id};request-id:{x_request_id};ts:{ts};"
    expected = hmac.new(
        secret.encode('utf-8'),
        msg=manifest.encode('utf-8'),
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, v1)


def donar(request):
    """Página de donativo con Mercado Pago Checkout Pro."""

    if request.method == 'POST':
        monto_str = request.POST.get('monto', '').strip()
        monto_custom = request.POST.get('monto_custom', '').strip()

        # Determinar monto
        try:
            monto = Decimal(monto_custom) if monto_custom else Decimal(monto_str)
            if monto < 10:
                messages.error(request, 'El monto mínimo es de $10 MXN.')
                return redirect('donar')
            if monto > Decimal('100000.00'):
                messages.error(request, 'El monto máximo permitido es de $100,000 MXN.')
                return redirect('donar')
        except Exception:
            messages.error(request, 'Monto inválido.')
            return redirect('donar')

        # Crear preferencia de Mercado Pago
        try:
            import mercadopago
            sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

            # Crear registro de donativo
            donativo = Donativo.objects.create(
                usuario=request.user if request.user.is_authenticated else None,
                nombre_donante=request.user.get_full_name() if request.user.is_authenticated else 'Anónimo',
                email_donante=request.user.email if request.user.is_authenticated else '',
                monto=monto,
                estado='pendiente',
            )

            base_url = request.build_absolute_uri('/')[:-1]

            preference_data = {
                "items": [{
                    "title": "Donativo - Manual Contable AI",
                    "description": "Apoyo a la comunidad contable de México",
                    "quantity": 1,
                    "unit_price": float(monto),
                    "currency_id": "MXN",
                }],
                "back_urls": {
                    "success": f"{base_url}/donar/exito/?donativo_id={donativo.id}",
                    "failure": f"{base_url}/donar/error/",
                    "pending": f"{base_url}/donar/pendiente/",
                },
                "auto_return": "approved",
                "external_reference": str(donativo.id),
                "notification_url": f"{base_url}/donar/webhook/",
            }

            result = sdk.preference().create(preference_data)
            preference = result.get("response", {})

            if result.get("status") not in [200, 201]:
                logger.error(f"Error MP API: {result}")
                messages.error(request, 'Error al conectar con Mercado Pago (API).')
                return redirect('donar')

            donativo.preference_id = preference.get("id")
            donativo.save()

            # Obtener punto de inicio
            init_point = preference.get("init_point")
            if not init_point:
                init_point = preference.get("sandbox_init_point")

            if init_point:
                return redirect(init_point)
            else:
                logger.error(f"No init_point en respuesta de MP: {result}")
                messages.error(request, 'No se pudo generar el enlace de pago.')

        except ImportError:
            logger.error("mercadopago SDK no instalado")
            messages.error(request, 'Módulo de pagos no configurado. Contacta al administrador.')
        except Exception as e:
            logger.error(f"Error creando preferencia MP: {e}", exc_info=True)
            messages.error(request, 'Error procesando el donativo. Intenta de nuevo.')

        return redirect('donar')

    # GET: mostrar página de donativo
    total_donantes = Donativo.objects.filter(estado='aprobado').values('email_donante').distinct().count()
    total_recaudado = Donativo.objects.filter(estado='aprobado').aggregate(
        total=Sum('monto'))['total'] or 0

    return render(request, 'donaciones/donar.html', {
        'montos_sugeridos': MONTOS_SUGERIDOS,
        'monto_default': MONTO_DEFAULT,
        'total_donantes': total_donantes,
        'total_recaudado': total_recaudado,
    })

def donativo_exito(request):
    """Página de éxito después del pago."""
    donativo_id = request.GET.get('donativo_id')
    messages.success(request, '¡Gracias por tu donativo! 💜 Tu apoyo mantiene esta plataforma en línea.')
    return render(request, 'donaciones/resultado.html', {
        'exito': True,
        'donativo_id': donativo_id,
    })


def donativo_error(request):
    messages.error(request, 'El donativo no se pudo procesar. Puedes intentar de nuevo.')
    return render(request, 'donaciones/resultado.html', {'exito': False})


def donativo_pendiente(request):
    messages.info(request, 'Tu donativo está pendiente de confirmación. ¡Gracias!')
    return render(request, 'donaciones/resultado.html', {'exito': True, 'pendiente': True})


@require_POST
def webhook_mercadopago(request):
    """Webhook de Mercado Pago para confirmar pagos."""
    try:
        data = json.loads(request.body)
        logger.info(f"Webhook MP recibido: {data}")

        if data.get('type') == 'payment':
            payment_id = data.get('data', {}).get('id')
            if payment_id:
                if not _verify_mercadopago_signature(request, payment_id):
                    logger.warning('Webhook MP rechazado: firma inválida o incompleta.')
                    return HttpResponse(status=401)

                import mercadopago
                sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
                payment_info = sdk.payment().get(payment_id)
                payment = payment_info.get("response", {})

                external_ref = payment.get("external_reference")
                status = payment.get("status")

                if external_ref:
                    try:
                        donativo = Donativo.objects.get(id=external_ref)

                        # Idempotencia: evitar reprocesar pagos ya aplicados.
                        if donativo.referencia_mp and donativo.referencia_mp == str(payment_id) and donativo.estado == 'aprobado':
                            logger.info(f"Webhook MP duplicado ignorado para donativo {donativo.id}.")
                            return HttpResponse(status=200)

                        if status == 'approved':
                            donativo.estado = 'aprobado'
                        elif status == 'rejected':
                            donativo.estado = 'rechazado'
                        elif status == 'refunded':
                            donativo.estado = 'reembolsado'
                        donativo.referencia_mp = str(payment_id)
                        donativo.datos_webhook = payment
                        donativo.save()
                        logger.info(f"Donativo {donativo.id} actualizado: {status}")
                    except Donativo.DoesNotExist:
                        logger.warning(f"Donativo no encontrado: {external_ref}")

    except Exception as e:
        logger.error(f"Error procesando webhook MP: {e}", exc_info=True)

    return HttpResponse(status=200)
