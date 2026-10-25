"""Almacenamiento de logos fuera de los directorios públicos de Nginx."""
import os
import uuid
from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateLogoStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('file_permissions_mode', 0o600)
        kwargs.setdefault('directory_permissions_mode', 0o700)
        super().__init__(*args, **kwargs)

    @property
    def base_location(self):
        return settings.PRIVATE_MEDIA_ROOT

    @property
    def location(self):
        return os.path.abspath(self.base_location)

    def url(self, name):
        raise ValueError('Los logos se sirven mediante una vista autenticada.')


def ruta_logo(instance, filename):
    extension = '.jpg' if filename.lower().endswith(('.jpg', '.jpeg')) else '.png'
    return f'logos/{uuid.uuid4().hex}{extension}'
