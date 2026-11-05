"""Consulta limitada a portales oficiales; no ejecuta URLs libres del panel."""
import hashlib
from urllib.parse import urlparse, urljoin
import requests
from django.core.management.base import BaseCommand
from catalogo.models import FuenteNormativa, AlertaFuente
from panel.audit import registrar

HOSTS={'www.diputados.gob.mx','www.dof.gob.mx','dof.gob.mx','sidof.segob.gob.mx','www.sat.gob.mx','wwwmat.sat.gob.mx','sat.gob.mx'}


def obtener(url):
    for _ in range(4):
        p=urlparse(url)
        if p.scheme!='https' or p.hostname not in HOSTS or p.username or p.password or p.port not in (None,443):
            raise ValueError('Solo se monitorizan portales fiscales oficiales HTTPS autorizados.')
        with requests.get(url,timeout=(10,30),stream=True,allow_redirects=False,headers={'User-Agent':'NexoContable-fuentes/1.0'}) as response:
            if response.is_redirect:
                url=urljoin(url,response.headers['Location']); continue
            response.raise_for_status()
            digest=hashlib.sha256(); size=0
            for chunk in response.iter_content(65536):
                size+=len(chunk)
                if size>20*1024*1024: raise ValueError('Documento excede 20 MB.')
                digest.update(chunk)
            if size==0: raise ValueError('Respuesta vacía.')
            return digest.hexdigest()
    raise ValueError('Demasiadas redirecciones.')


class Command(BaseCommand):
    help='Comprueba cambios de archivos fiscales, registra alertas y nunca publica criterios.'

    def handle(self,*args,**options):
        for fuente in FuenteNormativa.objects.filter(fiscal=True):
            versiones=fuente.versiones.filter(publicado=True,retirado=False,consulta='permitido',almacenamiento='permitido').order_by('-pk')
            if not versiones.exists(): continue
            try:
                digest=obtener(fuente.url)
                tipo='cambio'; detalle='Cambió el archivo oficial: revisar edición, transitorios y alcance; no implica automáticamente cambio normativo.'
                if digest in set(versiones.values_list('huella_documento',flat=True)): continue
            except (requests.RequestException,ValueError,KeyError) as exc:
                digest=''; tipo='consulta_fallida'; detalle='No fue posible comprobar la fuente; revisar disponibilidad. Tipo: '+type(exc).__name__
            alerta,created=AlertaFuente.objects.get_or_create(fuente=fuente,tipo=tipo,huella_detectada=digest,resuelta=False,defaults={'detalle':detalle})
            if created: registrar('fuentes','monitor.'+tipo,referencia=alerta.pk,detalle=detalle)
            self.stdout.write(f'{fuente.pk}: {tipo}')
