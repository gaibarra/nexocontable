import io
from bs4 import BeautifulSoup
from django.test import SimpleTestCase,TestCase,override_settings
from django.urls import reverse
from docx import Document
from .estilo_documento import estilizar,LEYES
from . import tests as base_tests
from .models import ManualContable


class EstiloDocumentoTests(SimpleTestCase):
    def test_leyes_solo_aludidas_y_enlaces_oficiales_sin_anidar(self):
        soup=BeautifulSoup('<h2>6. ISR</h2><p>La LISR y la Ley del Impuesto al Valor Agregado requieren revisión.</p><p>https://www.diputados.gob.mx/LeyesBiblio/pdf/LISR.pdf</p>','html.parser')
        estilizar(soup)
        self.assertTrue(soup.select('a[href="'+LEYES[0][2]+'"]'))
        self.assertTrue(soup.select('a[href="'+LEYES[1][2]+'"]'))
        self.assertFalse(soup.select('a[href="'+LEYES[2][2]+'"]'))
        self.assertFalse(soup.select('a a'))
        self.assertIsNotNone(soup.find('a',string=LEYES[0][2]))
        self.assertEqual(soup.h2.get_text(),'01  ISR')
        self.assertEqual(soup.select_one('.document-laws').get('aria-label'),'Acceso a las leyes citadas')
        self.assertTrue(all(a.get('rel')==['noopener','noreferrer'] or a.get('rel')=='noopener noreferrer' for a in soup.find_all('a')))

    def test_enfasis_preserva_negacion_cifras_y_negritas_existentes(self):
        original='El activo por impuesto diferido es 3,000.00; no causa IVA. La tasa hipotética se revisa.'
        soup=BeautifulSoup('<p>'+original+'</p><p><strong>Conservar evidencia.</strong></p>','html.parser')
        estilizar(soup)
        self.assertEqual(soup.p.get_text(),original)
        self.assertIn('no causa IVA',[s.get_text() for s in soup.p.find_all('strong')])
        self.assertFalse(soup.select('strong strong'))
        self.assertLessEqual(len(soup.p.find_all('strong')),3)

    def test_politicas_numeradas_se_convierten_en_lista_real(self):
        soup=BeautifulSoup('<p>Políticas: 1) Conciliar saldos. 2) Conservar soporte. 3) Revisar estimaciones.</p>','html.parser')
        estilizar(soup)
        self.assertEqual([li.get_text() for li in soup.select('ol > li')],['Conciliar saldos.','Conservar soporte.','Revisar estimaciones.'])
        self.assertIn('Políticas:',soup.get_text())

    def test_no_modifica_codigo_ni_enlaces_preexistentes(self):
        soup=BeautifulSoup('<pre>LISR: 1) uno 2) dos 3) tres</pre><p><a href="https://example.com">LISR</a></p>','html.parser')
        estilizar(soup)
        self.assertEqual(soup.pre.get_text(),'LISR: 1) uno 2) dos 3) tres')
        self.assertIsNone(soup.pre.find('a'))
        self.assertIsNotNone(soup.find('a',href='https://example.com'))


@override_settings(SECURE_SSL_REDIRECT=False)
class ExportacionEditorialTests(TestCase):
    setUp=base_tests.CatalogoCuentaDeleteTests.setUp

    def test_word_contiene_hipervinculos_reales_negritas_y_contenido_sin_cambios(self):
        texto='## Tratamiento\n\nEl activo por impuesto diferido es 3,000.00 y no causa IVA.\n\nConsulta LISR, LIVA y CFF.\n\n| Cuenta | Debe | Haber |\n|---|---|---|\n| Activo | 100 | 0 |\n| Resultado | 0 | 100 |\n| Total | 100 | 100 |'
        m=ManualContable.objects.create(tenant=self.tenant,titulo='Manual profesional',contenido=texto,creado_por=self.user)
        response=self.client.get(reverse('exportar_manual',args=[m.pk]))
        self.assertEqual(response.status_code,200)
        doc=Document(io.BytesIO(response.content))
        links=[r.target_ref for r in doc.part.rels.values() if r.reltype.endswith('/hyperlink')]
        for ley in LEYES:self.assertIn(ley[2],links)
        strong=[r.text for p in doc.paragraphs for r in p.runs if r.bold]
        self.assertIn('activo por impuesto diferido',strong)
        self.assertIn('no causa IVA',strong)
        self.assertIn('w:hyperlink',doc.element.xml)
        self.assertIn('18334F',doc.tables[0]._tbl.xml)
        self.assertIn('EAF4F2',doc.tables[0]._tbl.xml)
        m.refresh_from_db();self.assertEqual(m.contenido,texto);self.assertFalse(m.aprobado)
