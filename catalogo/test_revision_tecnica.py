from types import SimpleNamespace
from unittest.mock import patch
from bs4 import BeautifulSoup
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from cuentas.models import MembresiaTenant
from .models import CodigoAgrupador, ManualContable, UsoIA
from .ia import TextoGenerado
from .revision_tecnica import revisar_contenido
from .templatetags.markdown_filters import render_markdown
from . import tests as base_tests


class ReglasTecnicasTests(SimpleTestCase):
    def test_inventario_ordinario_sugiere_nic2_sin_valor_razonable(self):
        from .prompts import _sugerir_niif_ifrs
        cuenta=SimpleNamespace(cuenta='115',descripcion='Inventario',codigoagrupador=SimpleNamespace(codigoagrupador='115',nombre='Inventario'))
        self.assertEqual(_sugerir_niif_ifrs(cuenta), ['NIC 2 - Inventarios'])

    def test_iva_fronterizo_no_es_tasa_cero(self):
        self.assertIn('iva_fronterizo', {h['codigo'] for h in revisar_contenido('- LIVA: 16% o 0% en regiones fronterizas.')})
        self.assertFalse(revisar_contenido('La tasa cero no equivale al estímulo fronterizo de 8%.'))

    def test_citas_incorrectas_de_inventarios(self):
        for text,code in [('LISR Art. 27, fracciones XI y XII: métodos de valuación PEPS.', 'lisr_metodos'),
                          ('LISR Art. 28, fracc. XIII: destrucción por mermas.', 'lisr_mermas')]:
            self.assertIn(code, {h['codigo'] for h in revisar_contenido(text)})
        self.assertFalse(revisar_contenido('Métodos fiscales: LISR artículo 41. Pérdida de valor: revisar LISR 27 XX.'))

    def test_resico_no_permite_deduccion_futura_por_destruir(self):
        for text in ['Un inventario mal valuado distorsiona el costo deducible.', 'El deterioro no es deducible hasta que el bien se destruya; el efecto fiscal se difiere.']:
            self.assertIn('resico_deducciones', {h['codigo'] for h in revisar_contenido(text, 'pf_resico')})
        self.assertFalse(revisar_contenido('El gasto contable no disminuye la base RESICO del ISR. IVA se revisa por separado.', 'pf_resico'))
        self.assertFalse(revisar_contenido('Costo deducible sujeto a requisitos de ISR.', 'pm_general'))

    def test_aclaraciones_no_se_confunden_con_afirmaciones_incorrectas(self):
        for text in ['Los métodos se revisan en LISR art. 41. No se atribuyen a LISR 27 XI/XII.',
                     'La región fronteriza no determina tasa 0%.',
                     'El estímulo fronterizo puede dar 8%; tasa 0%, exención y estímulo son tratamientos distintos.',
                     'LISR 27 XX: revisar pérdida de valor y destrucción. No se invoca LISR 28 XIII.',
                     'LISR art. 41: métodos permitidos PEPS y promedio. El costeo directo no figura en esa lista.']:
            self.assertFalse(revisar_contenido(text),text)
        self.assertTrue(revisar_contenido('LISR art. 27, fracción XX. Regula la deducción por pérdidas por créditos incobrables.'))
        self.assertTrue(revisar_contenido('LISR artículo 41: métodos de valuación, costeo directo, PEPS.'))

    def test_vnr_no_se_fundamenta_en_niif13(self):
        self.assertIn('vnr_valor_razonable', {h['codigo'] for h in revisar_contenido('NIIF 13 orienta la estimación del valor neto realizable.')})
        self.assertFalse(revisar_contenido('El valor neto realizable no equivale al valor razonable de NIIF 13.'))

    def test_listas_sin_linea_vacia_y_codigo(self):
        html = BeautifulSoup(render_markdown('Documentación:\n- CFDI\n- Recepción\n\n```text\n- conservar literal\n```'), 'html.parser')
        self.assertEqual(len(html.select('ul > li')), 2)
        self.assertIn('- conservar literal', html.select_one('code').get_text())

    def test_documentos_no_cargan_imagenes_remotas_ni_scripts(self):
        html = str(render_markdown('<img src="https://example.invalid/rastreo" /><script>alert(1)</script>'))
        self.assertNotIn('<img', html); self.assertNotIn('<script', html)
        html = str(render_markdown('<div class="bg-[url(https://example.invalid/rastreo)]">Texto</div>'))
        self.assertNotIn('bg-[url', html)

    def test_asiento_multicuenta_no_se_rotula_como_cuenta_t(self):
        from .tablas_documento import ajustar_tablas
        html=BeautifulSoup(render_markdown('**Cuenta T — Inventario**\n\n| Cuenta | Debe | Haber |\n|---|---|---|\n| Inventario | 100 | 0 |\n| IVA acreditable | 16 | 0 |\n| Bancos | 0 | 116 |'), 'html.parser')
        ajustar_tablas(html)
        self.assertIn('Asiento contable',html.find('p').get_text())
        self.assertIn('116',html.get_text())

    def test_mayor_individual_conserva_su_rotulo(self):
        from .tablas_documento import ajustar_tablas
        html=BeautifulSoup(render_markdown('**Cuenta T — Inventario**\n\n| Concepto | Debe | Haber |\n|---|---|---|\n| Compra | 100 | 0 |\n| Consumo | 0 | 50 |'), 'html.parser')
        ajustar_tablas(html)
        self.assertIn('Cuenta T',html.find('p').get_text())


@override_settings(DEBUG=False, SECURE_SSL_REDIRECT=False)
class RevisionIntegracionTests(TestCase):
    setUp = base_tests.CatalogoCuentaDeleteTests.setUp

    def test_borrador_erroneo_no_se_guarda_y_registra_consumo(self):
        texto = TextoGenerado('LIVA: 16% o 0% en regiones fronterizas.', [{'proveedor':'simulado','modelo':'simulado','entrada':10,'salida':10,'total':20,'resultado':'completo'}])
        with patch('catalogo.views.generar_texto', return_value=texto):
            response = self.client.post(reverse('generar_manual'), {'cuentas':self.cuenta.pk})
        self.assertEqual(response.status_code,302)
        self.assertFalse(ManualContable.objects.exists())
        self.assertEqual(UsoIA.objects.get().tokens_total,20)
        self.assertFalse(UsoIA.objects.get().manual_generado)

    def test_no_aprueba_un_borrador_con_error_detectado(self):
        manual=ManualContable.objects.create(tenant=self.tenant,creado_por=self.user,titulo='Inventarios',contenido='LISR Art. 28, fracc. XIII: destrucción de inventario.')
        self.client.post(reverse('aprobar_manual',args=[manual.pk]))
        manual.refresh_from_db();self.assertFalse(manual.aprobado)

    def test_lector_consulta_y_exporta_pero_no_modifica_ni_genera(self):
        lector=User.objects.create_user('lector_revision')
        MembresiaTenant.objects.create(usuario=lector,tenant=self.tenant,rol='solo_lectura')
        manual=ManualContable.objects.create(tenant=self.tenant,creado_por=self.user,titulo='Consulta',contenido='Borrador revisable')
        self.client.force_login(lector);session=self.client.session;session['tenant_id']=self.tenant.pk;session.save()
        for route in ['detalle_manual','exportar_manual']:
            response=self.client.get(reverse(route,args=[manual.pk]))
            self.assertEqual(response.status_code,200)
            self.assertIn('no-store',response.headers['Cache-Control'])
            self.assertIn('private',response.headers['Cache-Control'])
        with patch('catalogo.views.generar_texto') as proveedor:
            for route,payload in [('generar_manual',{'cuentas':self.cuenta.pk}),('editar_manual',{'contenido':'cambio'}),('eliminar_manual',{}),('aprobar_manual',{})]:
                args=[] if route=='generar_manual' else [manual.pk]
                self.assertEqual(self.client.post(reverse(route,args=args),payload).status_code,403)
            proveedor.assert_not_called()
        manual.refresh_from_db();self.assertEqual(manual.contenido,'Borrador revisable')

    def test_variante_historica_no_duplica_el_oficial_aprobado(self):
        self.cuenta.delete()
        legado=CodigoAgrupador.objects.create(nivel=1,codigoagrupador='101.0',nombre='Caja heredada')
        manual=ManualContable.objects.create(tenant=self.tenant,creado_por=self.user,titulo='Legado',contenido='Revisado',aprobado=True)
        manual.codigos_sat.add(legado)
        response=self.client.get(reverse('generar_manual'))
        self.assertNotContains(response,f'value="sat:{legado.pk}"')
        self.assertEqual(response.context['estados_manuales'][f'sat:{self.codigo.pk}']['estado'],'aprobado')
        with patch('catalogo.views.generar_contenido_manual') as generar:
            response=self.client.post(reverse('generar_manual'),{'cuentas':f'sat:{self.codigo.pk}'})
        self.assertRedirects(response,reverse('detalle_manual',args=[manual.pk]));generar.assert_not_called()
