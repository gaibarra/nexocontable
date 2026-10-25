from django.shortcuts import redirect
from django.urls import reverse
from .models import Tenant, MembresiaTenant

# Rutas que NO requieren tenant activo
EXEMPT_URLS = [
    '/admin/',
    '/panel/',
    '/registro/',
    '/aviso-de-privacidad/',
    '/login/',
    '/recuperar-contrasena/',
    '/restablecer/',
    '/logout/',
    '/perfil/',
    '/mi-despacho/',
    '/marca/logos/',
    '/organizaciones/',
    '/donar/',
    '/api/',
    '/invitacion/',
]


class TenantMiddleware:
    """
    Middleware que inyecta el tenant activo en cada request.
    - Lee tenant_id de la sesión
    - Verifica que el usuario tenga acceso
    - Inyecta request.tenant
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = None
        request.user_rol = None

        if request.user.is_authenticated:
            tenant_id = request.session.get('tenant_id')

            if tenant_id:
                try:
                    membresia = MembresiaTenant.objects.select_related('tenant').get(
                        tenant_id=tenant_id,
                        usuario=request.user,
                        tenant__activo=True
                    )
                    request.tenant = membresia.tenant
                    request.user_rol = membresia.rol
                except MembresiaTenant.DoesNotExist:
                    # Tenant inválido, limpiar sesión
                    request.session.pop('tenant_id', None)

            # Si no hay tenant y la ruta lo requiere, redirigir
            if not request.tenant and not self._is_exempt(request.path):
                return redirect('lista_tenants')

        response = self.get_response(request)
        return response

    def _is_exempt(self, path):
        """Verifica si la ruta está exenta de requerir tenant."""
        return any(path.startswith(url) for url in EXEMPT_URLS) or path == '/'
