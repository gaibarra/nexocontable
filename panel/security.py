import base64
import hashlib
import hmac
import secrets
import struct
import time
from functools import wraps
from datetime import timedelta
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone
from .models import AccesoPanel, IntentoAcceso


def secreto():
    return base64.b32encode(secrets.token_bytes(20)).decode()


def codigo(secret, paso):
    key = base64.b32decode(secret, casefold=True)
    digest = hmac.new(key, struct.pack('>Q', paso), hashlib.sha1).digest()
    offset = digest[-1] & 15
    return f'{(struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7fffffff) % 1000000:06d}'


def validar_totp(secret, value, ultimo=-1):
    if not value or len(value) != 6 or not value.isascii() or not value.isdigit():
        return None
    paso = int(time.time()) // 30
    for candidato in (paso, paso - 1, paso + 1):
        if candidato > ultimo and hmac.compare_digest(codigo(secret, candidato), value):
            return candidato
    return None


def permitido(user):
    return user.is_authenticated and user.is_active and AccesoPanel.objects.filter(usuario=user, activo=True).exists()


def privado(*roles):
    def decorar(view):
        @wraps(view)
        def inner(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('panel:login')
            if not permitido(request.user):
                raise PermissionDenied
            if request.session.get('panel_2fa') != request.user.pk:
                return redirect('panel:verificar')
            if roles and request.user.acceso_panel.rol not in roles:
                raise PermissionDenied
            request.session.set_expiry(3600)
            return view(request, *args, **kwargs)
        return inner
    return decorar


def consumir_intento(clave):
    """Bloqueo de 15 minutos después de diez intentos; compartido por workers."""
    digest = hashlib.sha256(clave.encode()).hexdigest()
    now = timezone.now()
    with transaction.atomic():
        obj, _ = IntentoAcceso.objects.get_or_create(clave=digest, defaults={'desde': now})
        obj = IntentoAcceso.objects.select_for_update().get(pk=obj.pk)
        if now - obj.desde >= timedelta(minutes=15):
            obj.intentos, obj.desde = 0, now
        if obj.intentos >= 10:
            return False
        obj.intentos += 1
        obj.save(update_fields=['intentos', 'desde'])
    return True
