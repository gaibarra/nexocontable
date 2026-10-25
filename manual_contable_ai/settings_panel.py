"""Proceso privado: misma fuente de datos, sesión y rutas independientes."""
from .settings import *  # noqa: F403

ROOT_URLCONF = 'panel.root_urls'
SESSION_COOKIE_NAME = 'panel_sessionid'
SESSION_COOKIE_PATH = '/panel/'
SESSION_COOKIE_AGE = 3600
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CSRF_COOKIE_NAME = 'panel_csrftoken'
CSRF_COOKIE_PATH = '/panel/'
CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'
LOGIN_URL = '/panel/login/'
MIDDLEWARE = [m for m in MIDDLEWARE if m != 'cuentas.middleware.TenantMiddleware']  # noqa: F405
MIDDLEWARE = ['panel.middleware.PrivacidadPanelMiddleware'] + MIDDLEWARE
# Cuenta real del proxy para limitar intentos; no se usa como identidad de usuario.
