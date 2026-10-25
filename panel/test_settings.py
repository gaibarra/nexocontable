from manual_contable_ai.settings_panel import *  # noqa: F403
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
SECURE_SSL_REDIRECT = False
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
STORAGES = {'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}, 'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'}}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
# Las migraciones históricas del catálogo contienen SQL exclusivo de PostgreSQL.
# En pruebas rápidas se crea su esquema actual sin ejecutar semillas históricas.
MIGRATION_MODULES = {'cuentas': None, 'catalogo': None, 'donaciones': None}
