import io
import json
from pathlib import Path
from django.core.management import BaseCommand, call_command
from django.db import transaction
from django.utils import timezone
from cuentas.models import Tenant
from catalogo.models import VersionFuente, CriterioRevisado
from catalogo.desarrollo_uniforme import PERFILES
from catalogo.comparacion_internacional import VERSION, paquete


class Command(BaseCommand):
    help='Publica comparaciones educativas internacionales, con fuentes y límites de uso.'

    @transaction.atomic
    def handle(self,*args,**options):
        call_command('cargar_desarrollo_uniforme',stdout=io.StringIO())
        datos=json.loads((Path(__file__).parents[2]/'data/fuentes_abiertas_2026_10_29.json').read_text())
        creados=0
        for tipo,p in PERFILES.items():
            guia=paquete(tipo,{'codigo':'','descripcion':tipo})
            url=next(f['url'] for f in datos if f['volumen']==guia['volumen'])
            v=VersionFuente.objects.filter(fuente__url=url,publicado=True,retirado=False,
                consulta='permitido',almacenamiento='permitido',envio_ia='permitido',reproduccion='permitido').latest('pk')
            for reg,_ in Tenant.REGIMEN_CHOICES:
                if CriterioRevisado.objects.filter(version=v,perfil_tecnico=tipo,regimen=reg,titulo=VERSION,publicado=True,retirado=False).exists():continue
                CriterioRevisado.objects.create(version=v,perfil_tecnico=tipo,familia=p['familia'],regimen=reg,area='contable',
                    titulo=VERSION,localizacion=guia['localizacion'],
                    explicacion='\n\n'.join(guia[k] for k in ('alcance','contraste','caso')),
                    condiciones=guia['revision'],
                    excepciones='Comparación educativa propia: no reproduce normas IFRS ni acredita convergencia literal. La ficha oficial se conserva como identificación, sin incorporar su texto a IA. Se excluyen opciones ASPE, sección 6.6 del volumen 1 y materiales de terceros con licencia distinta.',
                    vigente_desde=max(v.vigente_desde,timezone.localdate()),publicado=True,revisado_en=timezone.now(),cobertura='parcial')
                creados+=1
        self.stdout.write(f'Comparaciones internacionales: {len(PERFILES)} perfiles; criterios nuevos: {creados}.')
