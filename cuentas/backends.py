from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailOrUsernameBackend(ModelBackend):
    """
    Backend de autenticación que permite usar el correo electrónico
    o el nombre de usuario (username).
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            # Buscamos por username O por email
            user = UserModel.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except UserModel.DoesNotExist:
            return None
        except UserModel.MultipleObjectsReturned:
            # Si hay varios, usamos el que coincida exactamente con username
            user = UserModel.objects.filter(Q(username__iexact=username) | Q(email__iexact=username)).order_by('id').first()

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
