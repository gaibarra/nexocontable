"""Aplicación educativa con trazabilidad y sin presentar fuentes abiertas como NIF."""
import io
from types import SimpleNamespace
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from .perfil_contable import perfil, secciones_normativas
from .guia_caja import DESARROLLO
from . import test_biblioteca as biblioteca_tests
from .biblioteca import seleccionar, validar_respuesta, instrucciones, pendientes_manual
from .test_biblioteca import respuesta
from .models import VersionFuente, ManualContable


def caja():
    return SimpleNamespace(cuenta='101',descripcion='Caja',codigoagrupador=SimpleNamespace(codigoagrupador='101',nombre='Caja'))


class GuiaCajaTests(SimpleTestCase):
    def test_norma_principal_y_complementarias_condicionadas(self):
        p=perfil(caja(),'bancos')
        self.assertEqual([n['clave'] for n in p['normas']],['NIF C-1','NIF B-6','NIF B-2','NIF B-15'])
        self.assertIn('Condicionada',p['normas'][-1]['razon'])
        self.assertIn('moneda extranjera',p['normas'][-1]['razon'])
        self.assertNotIn('aplicacion_propia',perfil(SimpleNamespace(cuenta='102',descripcion='Bancos'),'bancos'))

    def test_desarrollo_incluye_decisiones_y_no_afirma_consulta_autorizada(self):
        texto=secciones_normativas(perfil(caja(),'bancos'))
        for tema in ('importe nominal','restricción contractual','revelaciones','vales','arqueo','cargo','abono','CC BY 4.0','172–176','no acredita haber consultado','Referencia pendiente de revisión profesional en ejemplar autorizado'):
            self.assertIn(tema,texto)
        self.assertGreater(len(DESARROLLO.split()),800)
        self.assertIn('https://cinif.org.mx/normatividad_NIF2026.php',texto)


class FuentesCajaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        biblioteca_tests.BibliotecaTests.setUpTestData.__func__(cls)

    def test_fuente_delimitada_e_idempotente(self):
        # Simula la publicación histórica amplia, conservada al retirarse.
        fuente=VersionFuente.objects.filter(fuente__titulo__contains='Volume 1').first()
        anterior=VersionFuente.objects.create(fuente=fuente.fuente,edicion='2021-A',publicada_el=fuente.publicada_el,
            vigente_desde=fuente.vigente_desde,publicado=True,revisado_en=fuente.revisado_en,
            consulta='permitido',almacenamiento='permitido',envio_ia='permitido',reproduccion='permitido',
            evidencia_permisos='Publicación histórica amplia, con atribución CC BY.',
            huella_documento=fuente.huella_documento,evidencia_vigencia='Edición educativa.')
        call_command('cargar_fuentes_abiertas',stdout=io.StringIO())
        anterior.refresh_from_db(); self.assertTrue(anterior.retirado)
        self.assertEqual(anterior.evidencia_permisos,'Publicación histórica amplia, con atribución CC BY.')
        n=VersionFuente.objects.count()
        call_command('cargar_fuentes_abiertas',stdout=io.StringIO())
        self.assertEqual(n,VersionFuente.objects.count())
        snap=seleccionar(caja(),self.tenant)
        refs=[f for f in snap['fuentes'] if 'Volume 1' in f['norma']]
        self.assertEqual(len(refs),1)
        self.assertIn('6.2.1',refs[0]['localizacion'])
        self.assertIn('excluye',refs[0]['edicion'])
        self.assertIn('no al PDF íntegro',refs[0]['atribucion'])
        self.assertIn('no almacenar su texto',refs[0]['excepciones'])


    def test_generacion_snapshot_y_exportacion_conservan_desarrollo(self):
        from docx import Document
        from .documento_word import generar_docx
        snap=seleccionar(caja(),self.tenant)
        self.assertIn('Comprueba que el sentido de cargos y abonos',instrucciones(snap))
        import json
        result=validar_respuesta(json.dumps(respuesta(snap)),snap)
        self.assertIn('Guía de aplicación: criterios y decisiones',result)
        self.assertIn('restricciones comprobadas',result)
        m=ManualContable.objects.create(tenant=self.tenant,creado_por=self.user,titulo='Caja ficticia',contenido=result,
            fundamentos_snapshot=result.fundamentos_snapshot,fecha_referencia=snap['fecha'])
        self.assertTrue(any(p['id']=='contable' for p in pendientes_manual(m)))
        doc=Document(io.BytesIO(generar_docx(m)))
        txt=' '.join(p.text for p in doc.paragraphs)
        self.assertIn('importe nominal',txt)
        self.assertIn('Referencia pendiente de revisión profesional',txt)
        links=[r.target_ref for r in doc.part.rels.values() if r.reltype.endswith('/hyperlink')]
        self.assertIn('https://cinif.org.mx/normatividad_NIF2026.php',links)
