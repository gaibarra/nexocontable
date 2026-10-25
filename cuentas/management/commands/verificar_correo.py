from django.conf import settings
from django.core.mail import get_connection
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Comprueba conexión, cifrado y autenticación SMTP sin enviar mensajes.'

    def handle(self, *args, **options):
        if not settings.EMAIL_BACKEND.endswith('.smtp.EmailBackend'):
            raise CommandError('Configura el backend SMTP de producción para verificar el envío real.')
        conexion = get_connection()
        try:
            conexion.open()
        except Exception as exc:
            raise CommandError(f'No se pudo autenticar el correo ({type(exc).__name__}). Revisa las credenciales de Gmail en el servidor.') from None
        finally:
            try:
                conexion.close()
            except Exception:
                pass
        self.stdout.write(self.style.SUCCESS('Conexión y autenticación SMTP verificadas. No se enviaron mensajes.'))
