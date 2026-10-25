from time import monotonic
from .audit import actor_actual, registrar


class ActividadMiddleware:
    """Registra rutas por nombre, sin cuerpos, consultas, contraseñas ni tokens de URL."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        actor = request.user.pk if request.user.is_authenticated else None
        token = actor_actual.set(actor)
        inicio = monotonic()
        try:
            response = self.get_response(request)
            match = request.resolver_match
            # El proxy tiene su propio registro dentro del proceso privado.
            if match and match.url_name != 'panel_proxy':
                registrar('http', match.view_name or 'ruta_desconocida', actor=actor,
                          organizacion_id=getattr(getattr(request, 'tenant', None), 'pk', None),
                          detalle=request.method, estado_http=response.status_code,
                          duracion_ms=max(0, int((monotonic() - inicio) * 1000)))
            return response
        finally:
            actor_actual.reset(token)


class PrivacidadPanelMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Cache-Control'] = 'no-store, private'
        response['X-Robots-Tag'] = 'noindex, nofollow'
        response['Referrer-Policy'] = 'same-origin'
        return response
