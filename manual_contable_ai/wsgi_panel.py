import os
from pathlib import Path
from django.core.wsgi import get_wsgi_application
os.environ['DJANGO_SETTINGS_MODULE'] = 'manual_contable_ai.settings_panel'
application = get_wsgi_application()

# Validar también las pantallas privadas antes de aceptar solicitudes. Una
# comprobación anónima solo alcanza el login y no detecta fallos en sus tablas.
from django.template.loader import get_template

for template in sorted((Path(__file__).resolve().parent.parent / 'panel/templates/panel').glob('*.html')):
    get_template('panel/' + template.name)
