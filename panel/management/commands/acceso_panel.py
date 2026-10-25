from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from panel.audit import registrar
from panel.models import AccesoPanel


class Command(BaseCommand):
    help = 'Autoriza explícitamente una cuenta existente. No modifica su contraseña.'

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('--rol', choices=[r for r, _ in AccesoPanel.ROLES], default='propietario')
        parser.add_argument('--revocar', action='store_true')
        parser.add_argument('--restablecer-2fa', action='store_true')

    def handle(self, username, rol, revocar, restablecer_2fa, **options):
        try:
            user = get_user_model().objects.get(username=username, is_active=True)
        except get_user_model().DoesNotExist:
            raise CommandError('No existe una cuenta activa con ese nombre de usuario.')
        obj, _ = AccesoPanel.objects.get_or_create(usuario=user)
        obj.rol, obj.activo = rol, not revocar
        if restablecer_2fa:
            from django.contrib.sessions.models import Session
            for session in Session.objects.filter(expire_date__gt=timezone.now()).iterator():
                datos = session.get_decoded()
                if datos.get('panel_2fa') == user.pk or datos.get('_auth_user_id') == str(user.pk):
                    session.delete()
            obj.secreto_totp, obj.ultimo_paso = '', -1
        obj.save()
        registrar('panel', 'acceso.revocado' if revocar else 'acceso.autorizado', referencia=user.pk, detalle=rol)
        self.stdout.write(self.style.SUCCESS('Acceso actualizado. Se conserva la contraseña existente.'))
