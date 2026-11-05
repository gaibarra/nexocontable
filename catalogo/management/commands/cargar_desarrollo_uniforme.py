"""Publica guías educativas por perfil y régimen, sin tocar documentos anteriores."""
import io
from django.core.management import BaseCommand, call_command
from django.db import transaction
from django.utils import timezone
from cuentas.models import Tenant
from catalogo.models import VersionFuente, CriterioRevisado
from catalogo.desarrollo_uniforme import PERFILES, VERSION, paquete, EJES


class Command(BaseCommand):
    help='Carga criterios propios por naturaleza de cuenta para el desarrollo uniforme.'

    @transaction.atomic
    def handle(self,*args,**options):
        call_command('cargar_fuentes_abiertas',stdout=io.StringIO())
        creados=0
        for tipo,p in PERFILES.items():
            guia=paquete(tipo)
            v=VersionFuente.objects.filter(fuente__url=guia['fuente']['url'],publicado=True,retirado=False,
                consulta='permitido',almacenamiento='permitido',envio_ia='permitido',reproduccion='permitido').latest('pk')
            for reg,_ in Tenant.REGIMEN_CHOICES:
                if CriterioRevisado.objects.filter(version=v,perfil_tecnico=tipo,regimen=reg,
                    titulo=VERSION,publicado=True,retirado=False).exists():continue
                CriterioRevisado.objects.create(version=v,perfil_tecnico=tipo,familia=p['familia'],regimen=reg,
                    area='contable',titulo=VERSION,localizacion=p['localizacion'],
                    explicacion='\n\n'.join(EJES[k]+': '+t for k,t in p['ejes'].items()),
                    condiciones=guia['alcance']+' Evidencia: '+p['evidencia'],
                    excepciones=p['error']+' Del apéndice 6.6 del volumen 1: no almacenar su texto, enviarlo a IA ni reproducirlo; tampoco texto normativo de terceros. No se declara cobertura normativa completa.',
                    vigente_desde=max(v.vigente_desde,timezone.localdate()),publicado=True,
                    revisado_en=timezone.now(),cobertura='parcial')
                creados+=1
        self.stdout.write(f'{len(PERFILES)} perfiles técnicos; criterios educativos publicados: {creados}.')
