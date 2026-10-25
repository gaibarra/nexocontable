"""Puerta de enlace local mientras Nginx no enruta directamente al socket privado.
El proceso privado valida su propia sesión, segundo factor y CSRF.
"""
import fcntl
import http.client
import logging
import os
import socket
import subprocess
import time
from http.cookies import SimpleCookie
from pathlib import Path
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)


class ConexionPanel(http.client.HTTPConnection):
    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(str(settings.BASE_DIR / 'panel.sock'))


def iniciar_panel():
    """Arranque idempotente, bajo bloqueo y con argumentos fijos del proyecto."""
    base = Path(settings.BASE_DIR)
    with open(base / '.panel-start.lock', 'a') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        probe = ConexionPanel('localhost', timeout=1)
        try:
            probe.connect()
            return
        except OSError:
            pass
        finally:
            probe.close()
        subprocess.run([str(base / 'venv/bin/gunicorn'), 'manual_contable_ai.wsgi_panel:application',
                        '--chdir', str(base), '--bind', 'unix:' + str(base / 'panel.sock'),
                        '--workers', '2', '--threads', '2', '--timeout', '45', '--umask', '0077',
                        '--daemon', '--pid', str(base / 'panel.pid'),
                        '--error-logfile', str(base / 'panel-error.log')],
                       check=True, timeout=15, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(40):
            probe = ConexionPanel('localhost', timeout=1)
            try:
                probe.connect()
                return
            except OSError:
                time.sleep(.1)
            finally:
                probe.close()
        raise OSError('El proceso privado no respondió a tiempo')


@csrf_exempt
@require_http_methods(['GET', 'HEAD', 'POST'])
def proxy(request, ruta=''):
    # El proxy no interpreta ni registra credenciales o códigos del formulario.
    if len(request.body) > 65536:
        return HttpResponse('Solicitud demasiado grande.', status=413)
    conn = ConexionPanel('localhost', timeout=45)
    cookies = SimpleCookie()
    for name in ('panel_sessionid', 'panel_csrftoken'):
        if name in request.COOKIES:
            cookies[name] = request.COOKIES[name]
    headers = {'Host': request.get_host(), 'X-Forwarded-Proto': 'https' if request.is_secure() else 'http',
               'Content-Type': request.content_type or 'application/x-www-form-urlencoded',
               'Cookie': cookies.output(header='', sep=';').strip()}
    # Nginx fija X-Real-IP y no se usa para autorizar usuarios.
    headers['X-Real-IP'] = request.META.get('HTTP_X_REAL_IP', request.META.get('REMOTE_ADDR', ''))
    for src, dst in [('HTTP_ORIGIN', 'Origin'), ('HTTP_REFERER', 'Referer'), ('HTTP_X_CSRFTOKEN', 'X-CSRFToken')]:
        if request.META.get(src):
            headers[dst] = request.META[src]
    try:
        try:
            conn.connect()
        except OSError:
            iniciar_panel()
            conn.connect()
        conn.request(request.method, request.get_full_path(), body=request.body or None, headers=headers)
        upstream = conn.getresponse()
        response = HttpResponse(upstream.read(), status=upstream.status)
        for name, value in upstream.getheaders():
            if name.lower() == 'set-cookie':
                response.cookies.load(value)
            elif name.lower() not in {'connection', 'content-length', 'transfer-encoding', 'server', 'date'}:
                response[name] = value
        return response
    except (OSError, http.client.HTTPException, subprocess.SubprocessError):
        logger.exception('El servicio privado del panel no está disponible')
        return HttpResponse('El panel está reiniciando. Vuelve a intentar en unos segundos.', status=503)
    finally:
        conn.close()
