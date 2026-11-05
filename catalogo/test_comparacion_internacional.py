import copy
import io
import json
from types import SimpleNamespace
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from docx import Document
from . import test_biblioteca as base
from .comparacion_internacional import paquete, renderizar, VERSION, NORMAS
from .desarrollo_uniforme import PERFILES
from .biblioteca import seleccionar, validar_respuesta, huella
from .models import CriterioRevisado, ManualContable


class ComparacionTests(SimpleTestCase):
    def test_todos_los_perfiles_desarrollan_comparacion_sin_forzar_equivalencia(self):
        for tipo in PERFILES:
            with self.subTest(tipo=tipo):
                p=paquete(tipo,{'codigo':'FICTICIA','descripcion':tipo})
                texto=renderizar(p)
                for parte in ['Alcance y utilidad','Relación y diferencias','Ejemplo de aplicación','Evidencia y límites']:
                    self.assertIn(parte,texto)
                self.assertGreater(len(texto.split()),240)
                if tipo in ('general','orden','impuestos','gastos','anticipos','especializada'):
                    self.assertEqual(p['normas'],[])
                    self.assertIn('Sin equivalencia automática',texto)

    def test_caja_explica_flujos_conciliacion_y_transicion_sin_trasladar_normas(self):
        texto=renderizar(paquete('caja',{'codigo':'101','descripcion':'Caja'}))
        for tema in ['B-2','C-1','método directo','indirecto','$7,200','$9,200','−$6,000','2027','2026','operaciones relevantes sin movimiento monetario']:
            self.assertIn(tema.lower(),texto.lower())
        self.assertEqual(4000+11600-2400-6000,7200)
        self.assertIn('ias-7-statement-of-cash-flows',texto)


class ComparacionBibliotecaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        base.BibliotecaTests.setUpTestData.__func__(cls)

    def test_publicacion_idempotente_y_criterio_internacional_trazable(self):
        n=CriterioRevisado.objects.filter(titulo=VERSION).count()
        call_command('cargar_comparaciones_internacionales',stdout=io.StringIO())
        self.assertEqual(n,CriterioRevisado.objects.filter(titulo=VERSION).count())
        snap=seleccionar(self.cuenta,self.tenant)
        p=snap['perfil_contable']['comparacion_internacional']
        self.assertEqual(p['normas'][0]['clave'],'NIC 2')
        self.assertTrue(all(f['titulo']==VERSION and f['perfil_tecnico']=='inventarios' for f in p['fuentes']))
        r=validar_respuesta(json.dumps(base.respuesta(snap)),snap)
        self.assertTrue({f['id'] for f in p['fuentes']} <= set(r.fundamentos_snapshot['referencias_usadas']))

    def test_retiro_y_periodo_excluyen_comparacion_sin_alterar_snapshot_historico(self):
        snap=seleccionar(self.cuenta,self.tenant)
        f=snap['perfil_contable']['comparacion_internacional']['fuentes'][0]
        c=CriterioRevisado.objects.get(pk=f['criterio']);c.retirado=True;c.save(update_fields=['retirado'])
        nuevo=seleccionar(self.cuenta,self.tenant)
        self.assertNotIn('comparacion_internacional',nuevo['perfil_contable'])
        self.assertIn('comparacion_internacional',snap['perfil_contable'])
        self.assertIn('guia_tecnica',nuevo['perfil_contable'])

    def test_pantalla_y_word_comparten_comparacion_y_enlaces_reales(self):
        from .documento_word import generar_docx
        from .composicion_documento import componer_manual
        c=SimpleNamespace(cuenta='101',descripcion='Caja',codigoagrupador=SimpleNamespace(codigoagrupador='101',nombre='Caja'))
        snap=seleccionar(c,self.tenant)
        r=validar_respuesta(json.dumps(base.respuesta(snap)),snap)
        m=ManualContable.objects.create(tenant=self.tenant,creado_por=self.user,titulo='Caja ficticia',contenido=str(r),fundamentos_snapshot=r.fundamentos_snapshot,fecha_referencia=snap['fecha'])
        original=huella(m)
        html=componer_manual(m)['contenido_html'];self.assertIn('$7,200',html)
        doc=Document(io.BytesIO(generar_docx(m)))
        texto=' '.join(p.text for p in doc.paragraphs)
        for parte in ['Relación y diferencias','$7,200','B-2','financiamiento']:
            self.assertIn(parte,texto)
        enlaces=[r.target_ref for r in doc.part.rels.values() if r.reltype.endswith('/hyperlink')]
        self.assertIn(NORMAS['NIC 7'] and 'https://www.ifrs.org/issued-standards/list-of-standards/ias-7-statement-of-cash-flows/',enlaces)
        m.refresh_from_db();self.assertEqual(huella(m),original);self.assertFalse(m.aprobado)
