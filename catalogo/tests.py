from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from cuentas.models import Tenant, MembresiaTenant
from .models import CatalogoCuentas, CodigoAgrupador, CatalogoPlantilla, CatalogoPlantillaCuenta


@override_settings(DEBUG=True, SECURE_SSL_REDIRECT=False)
class CatalogoCuentaDeleteTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='owner@example.com', email='owner@example.com', password='StrongPass123!')
		self.tenant = Tenant.objects.create(nombre='Tenant Demo', propietario=self.user)
		MembresiaTenant.objects.create(tenant=self.tenant, usuario=self.user, rol='propietario')
		self.codigo = CodigoAgrupador.objects.create(nivel=1, codigoagrupador='101', nombre='Caja')
		self.cuenta = CatalogoCuentas.objects.create(
			tenant=self.tenant,
			cuenta='1000',
			descripcion='Caja general',
			codigoagrupador=self.codigo,
		)

		self.client.login(username='owner@example.com', password='StrongPass123!')
		session = self.client.session
		session['tenant_id'] = self.tenant.id
		session.save()

	def test_eliminar_cuenta_por_get_rechazado(self):
		url = reverse('eliminar_cuenta', args=[self.cuenta.pk])
		response = self.client.get(url)

		self.assertEqual(response.status_code, 405)
		self.assertTrue(CatalogoCuentas.objects.filter(pk=self.cuenta.pk).exists())

	def test_eliminar_cuenta_por_post_elimina(self):
		url = reverse('eliminar_cuenta', args=[self.cuenta.pk])
		response = self.client.post(url)

		self.assertEqual(response.status_code, 302)
		self.assertFalse(CatalogoCuentas.objects.filter(pk=self.cuenta.pk).exists())


@override_settings(DEBUG=True, SECURE_SSL_REDIRECT=False)
class CatalogoPlantillaTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='owner2@example.com', email='owner2@example.com', password='StrongPass123!')
		self.tenant = Tenant.objects.create(nombre='Tenant Comercial', propietario=self.user, giro='comercial')
		MembresiaTenant.objects.create(tenant=self.tenant, usuario=self.user, rol='propietario')
		self.codigo = CodigoAgrupador.objects.create(nivel=1, codigoagrupador='101', nombre='Caja')
		self.plantilla = CatalogoPlantilla.objects.create(nombre='Plantilla Comercial', giro='comercial', activo=True)
		CatalogoPlantillaCuenta.objects.create(
			plantilla=self.plantilla,
			cuenta='1000',
			descripcion='Caja general',
			codigoagrupador=self.codigo,
		)

	def test_plantilla_se_relaciona_con_cuentas(self):
		self.assertEqual(self.plantilla.cuentas.count(), 1)
		self.assertEqual(self.plantilla.cuentas.first().cuenta, '1000')


from types import SimpleNamespace
from unittest.mock import patch
import httpx
from openai import RateLimitError
from django.test import SimpleTestCase, RequestFactory
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.template.loader import render_to_string
from catalogo.views import generar_contenido_manual, generar_manual, ManualGenerationError


@override_settings(AI_PROVIDER='openai', AI_FALLBACK_PROVIDER='', OPENAI_API_KEY='test-key')
class ManualGenerationErrorTests(SimpleTestCase):
    def test_api_limits_have_actionable_messages(self):
        cases = [
            ('credit_balance_exhausted', 'insufficient_quota', 'recargar el saldo'),
            ('insufficient_quota', 'insufficient_quota', 'facturación'),
            ('project_usage_limit_exceeded', 'insufficient_quota', 'facturación'),
            ('rate_limit_exceeded', 'rate_limit_error', 'Espera un minuto'),
        ]
        for code, error_type, expected in cases:
            with self.subTest(code=code):
                error = RateLimitError('test', response=httpx.Response(
                    429, request=httpx.Request('POST', 'https://api.openai.com/v1/chat/completions')
                ), body={'code': code, 'type': error_type})
                with patch('catalogo.views.build_manual_prompts', return_value=('system', 'user')), \
                     patch('catalogo.ia.OpenAI', side_effect=error):
                    with self.assertRaisesRegex(ManualGenerationError, expected):
                        generar_contenido_manual([], SimpleNamespace(nombre='Demo'))

    def test_successful_generation_is_preserved(self):
        response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='Manual'), finish_reason='stop')],
                                   usage=SimpleNamespace(total_tokens=10))
        with patch('catalogo.views.build_manual_prompts', return_value=('system', 'user')), \
             patch('catalogo.ia.OpenAI') as factory:
            factory.return_value.__enter__.return_value.chat.completions.create.return_value = response
            self.assertEqual(generar_contenido_manual([], SimpleNamespace(nombre='Demo')), 'Manual')

    def test_generation_error_is_displayed_without_creating_manual(self):
        request = RequestFactory().post('/catalogo/generar-manual/', {'cuentas': ['1']})
        request.user = SimpleNamespace(is_authenticated=True)
        request.tenant = SimpleNamespace(nombre='Demo')
        request.session = {}
        request._messages = FallbackStorage(request)
        with patch('catalogo.views.asegurar_catalogo_sat'), \
             patch('catalogo.views.CatalogoCuentas.objects') as cuentas, \
             patch('catalogo.views.ManualContable.objects') as manuals, \
             patch('catalogo.views.buscar_manual_existente', return_value=None), \
             patch('panel.controls.reservar_generacion', return_value=''), \
             patch('catalogo.views.generar_contenido_manual', side_effect=ManualGenerationError('Saldo agotado')):
            cuentas.filter.return_value.select_related.return_value.exists.return_value = True
            cuentas.filter.return_value.select_related.return_value.__iter__.return_value = iter([SimpleNamespace(codigoagrupador=object(), relacion_sugerida=False)])
            response = generar_manual(request)
            self.assertEqual(response.status_code, 302)
            self.assertEqual([str(m) for m in get_messages(request)], ['Saldo agotado'])
            manuals.create.assert_not_called()

    def test_message_template_renders_only_correct_icon(self):
        from django.contrib.messages.storage.base import Message
        from django.template import Context, Template
        for level, icon in [(25, 'success'), (40, 'error'), (30, 'warning'), (20, 'info')]:
            with self.subTest(icon=icon):
                html = Template('{% load notifications %}{% app_notifications %}').render(
                    Context({'messages': [Message(level, 'Mensaje de prueba')]}))
                self.assertNotIn('{%', html)
                self.assertIn('Mensaje de prueba', html)
                for candidate in ['success', 'error', 'warning', 'info']:
                    self.assertEqual(f'"icon": "{candidate}"' in html, candidate == icon)


import io
from django.core.files.uploadedfile import SimpleUploadedFile
from catalogo.importador import importar_csv, importar_excel, importar_desde_filas
from catalogo.sat import asegurar_catalogo_sat


@override_settings(DEBUG=True, SECURE_SSL_REDIRECT=False)
class ImportacionSugeridaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='catalogo-test', password='secret')
        self.tenant = Tenant.objects.create(nombre='Importación', propietario=self.user)
        MembresiaTenant.objects.create(tenant=self.tenant, usuario=self.user, rol='propietario')
        self.client.force_login(self.user)
        session = self.client.session
        session['tenant_id'] = self.tenant.pk
        session.save()

    def test_sat_se_carga_automaticamente_sin_duplicados(self):
        asegurar_catalogo_sat()
        total = CodigoAgrupador.objects.count()
        asegurar_catalogo_sat()
        self.assertEqual(CodigoAgrupador.objects.count(), total)
        self.assertGreater(total, 1000)
        self.assertEqual(CodigoAgrupador.objects.get(codigoagrupador='102.01').nombre, 'Bancos nacionales')

    def test_csv_sugiere_y_omite_cuentas_mas_profundas(self):
        archivo = io.BytesIO('cuenta,descripcion,nivel\nA,Bancos nacionales,1\nA.1,Caja,2\nA.1.1,Desconocida,3'.encode())
        resultado = importar_csv(archivo, self.tenant, nivel_maximo=2)
        self.assertEqual((resultado.creadas, resultado.sugeridas, resultado.omitidas), (2, 2, 1))
        cuenta = self.tenant.cuentas.get(cuenta='A')
        self.assertEqual(cuenta.codigoagrupador.codigoagrupador, '102.01')
        self.assertTrue(cuenta.relacion_sugerida)
        self.assertEqual(self.tenant.cuentas.get(cuenta='A.1').nivel, 2)

    def test_sin_coincidencia_se_guarda_pendiente(self):
        resultado = importar_csv(io.BytesIO(b'cuenta,descripcion\nX,zzzzzz'), self.tenant)
        self.assertEqual(resultado.pendientes, 1)
        self.assertIsNone(self.tenant.cuentas.get().codigoagrupador)

    def test_no_usa_numero_propio_como_codigo_sat(self):
        importar_csv(io.BytesIO(b'cuenta,descripcion\n102.01,Caja'), self.tenant)
        self.assertEqual(self.tenant.cuentas.get().codigoagrupador.codigoagrupador, '101')

    def test_codigo_invalido_no_se_sustituye_silenciosamente(self):
        resultado = importar_csv(io.BytesIO(b'cuenta,descripcion,codigoagrupador\nA,Caja,9999'), self.tenant)
        self.assertEqual(len(resultado.errores), 1)
        self.assertFalse(self.tenant.cuentas.exists())

    def test_headers_y_nivel_invalido_no_escriben(self):
        for archivo, nivel in [(b'cuenta\nA', None), (b'cuenta,descripcion\nA,Caja', 'invalido')]:
            resultado = importar_csv(io.BytesIO(archivo), self.tenant, nivel_maximo=nivel)
            self.assertTrue(resultado.errores)
        self.assertFalse(self.tenant.cuentas.exists())

    def test_excel_se_lee_y_respeta_niveles_y_codigos_explicitos(self):
        import openpyxl
        wb = openpyxl.Workbook()
        wb.active.append(['cuenta', 'descripcion', 'codigoagrupador', 'nivel'])
        wb.active.append(['001', 'Caja', '101', 1])
        wb.active.append(['001.01', 'Caja sucursal', '101', 2])
        archivo = io.BytesIO()
        wb.save(archivo)
        archivo.seek(0)
        resultado = importar_excel(archivo, self.tenant, nivel_maximo=1)
        self.assertEqual((resultado.creadas, resultado.omitidas), (1, 1))
        self.assertFalse(self.tenant.cuentas.get().relacion_sugerida)
        self.assertEqual(self.tenant.cuentas.get().cuenta, '001')

    def test_inferir_nivel_con_cero_y_segmentos(self):
        resultado = importar_desde_filas(self.tenant, [
            {'cuenta': 'A', 'descripcion': 'Caja', 'nivel1': '1', 'nivel2': '0'},
            {'cuenta': 'B.1.2', 'descripcion': 'Caja'},
        ], ['cuenta', 'descripcion'], nivel_maximo=1)
        self.assertEqual(resultado.omitidas, 2)

    def test_importacion_http_y_confirmacion(self):
        archivo = SimpleUploadedFile('catalogo.csv', b'cuenta,descripcion\nA,Bancos nacionales')
        response = self.client.post(reverse('agregar_cuenta'), {'accion': 'importar_catalogo', 'archivo': archivo})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '1 relaciones sugeridas')
        cuenta = self.tenant.cuentas.get()
        response = self.client.post(reverse('catalogo_cuentas'), {'cuenta_id': cuenta.pk, 'codigoagrupador': '102.01'})
        self.assertEqual(response.status_code, 302)
        cuenta.refresh_from_db()
        self.assertFalse(cuenta.relacion_sugerida)

    def test_no_puede_confirmar_relacion_de_otro_tenant(self):
        otro = Tenant.objects.create(nombre='Ajeno', propietario=self.user)
        importar_csv(io.BytesIO(b'cuenta,descripcion\nA,Caja'), otro)
        response = self.client.post(reverse('catalogo_cuentas'), {'cuenta_id': otro.cuentas.get().pk, 'codigoagrupador': '101'})
        self.assertEqual(response.status_code, 404)

    def test_sat_permite_manual_sin_catalogo_propio(self):
        response = self.client.get(reverse('generar_manual'))
        self.assertContains(response, 'Estás usando el catálogo oficial SAT')
        codigo = CodigoAgrupador.objects.get(codigoagrupador='101')
        with patch('catalogo.views.generar_contenido_manual', return_value='Manual de caja'):
            response = self.client.post(reverse('generar_manual'), {'cuentas': [f'sat:{codigo.pk}']})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.tenant.manuales.get().contenido, 'Manual de caja')
        self.assertFalse(self.tenant.cuentas.exists())

    def test_manual_requiere_confirmar_sugerencias(self):
        importar_csv(io.BytesIO(b'cuenta,descripcion\nA,Caja'), self.tenant)
        with patch('catalogo.views.generar_contenido_manual') as generar:
            response = self.client.post(reverse('generar_manual'), {'cuentas': [self.tenant.cuentas.get().pk]})
        self.assertRedirects(response, reverse('catalogo_cuentas'))
        generar.assert_not_called()


@override_settings(DEBUG=True, SECURE_SSL_REDIRECT=False)
class VistaVinculacionesManualTests(TestCase):
    setUp = ImportacionSugeridaTests.setUp

    def crear_cuenta(self, numero, codigo=None, sugerida=False, tenant=None):
        return CatalogoCuentas.objects.create(
            tenant=tenant or self.tenant, cuenta=numero, descripcion=f'Cuenta {numero}',
            codigoagrupador=codigo, relacion_sugerida=sugerida)

    def test_catalogo_propio_muestra_codigo_y_estados_de_vinculacion(self):
        asegurar_catalogo_sat()
        codigo = CodigoAgrupador.objects.get(codigoagrupador='102.01')
        self.crear_cuenta('A', codigo)
        self.crear_cuenta('B', codigo, sugerida=True)
        self.crear_cuenta('C')
        response = self.client.get(reverse('generar_manual'))
        self.assertContains(response, 'SAT: <strong>102.01</strong>', html=False)
        self.assertContains(response, 'Vinculación confirmada')
        self.assertContains(response, 'Vinculación sugerida · pendiente de confirmar')
        self.assertContains(response, 'Falta vinculación SAT')
        self.assertContains(response, 'SAT → Cuentas propias')
        self.assertContains(response, 'data-unlinked-count>1</span>')
        self.assertFalse(response.context['usar_sat'])
        # Ambos paneles reflejan la misma cuenta; la pendiente sigue sin ser seleccionable.
        from html.parser import HTMLParser
        class Inputs(HTMLParser):
            def __init__(self):
                super().__init__()
                self.inputs = []
            def handle_starttag(self, tag, attrs):
                if tag == 'input':
                    self.inputs.append(dict(attrs))
        parser = Inputs()
        parser.feed(response.content.decode())
        for cuenta in self.tenant.cuentas.all():
            inputs = [i for i in parser.inputs if i.get('data-account-id') == str(cuenta.pk)]
            self.assertEqual(len(inputs), 2)
            for item in inputs:
                self.assertEqual('disabled' in item, cuenta.codigoagrupador is None or cuenta.relacion_sugerida)

    def test_vista_sat_agrupa_varias_cuentas_y_aisla_organizaciones(self):
        asegurar_catalogo_sat()
        codigo = CodigoAgrupador.objects.get(codigoagrupador='101')
        propia1 = self.crear_cuenta('A', codigo)
        propia2 = self.crear_cuenta('B', codigo)
        pendiente = self.crear_cuenta('C')
        otro = Tenant.objects.create(nombre='Otra organización', propietario=self.user)
        ajena = self.crear_cuenta('PRIVADA', codigo, tenant=otro)
        response = self.client.get(reverse('generar_manual'))
        grupo = next(g for g in response.context['grupos_sat'] if g['codigo'].pk == codigo.pk)
        self.assertEqual([c.pk for c in grupo['cuentas']], [propia1.pk, propia2.pk])
        self.assertEqual(response.context['cuentas_sin_vinculo'], [pendiente])
        self.assertNotContains(response, ajena.descripcion)
        sin_vinculo = next(g for g in response.context['grupos_sat'] if g['codigo'].codigoagrupador == '102.01')
        self.assertEqual(sin_vinculo['cuentas'], [])

    def test_generacion_desde_vista_invertida_usa_las_cuentas_propias(self):
        asegurar_catalogo_sat()
        codigo = CodigoAgrupador.objects.get(codigoagrupador='101')
        cuenta = self.crear_cuenta('A', codigo)
        with patch('catalogo.views.generar_contenido_manual', return_value='Manual propio') as generar:
            response = self.client.post(reverse('generar_manual'), {'cuentas': [str(cuenta.pk)]})
        self.assertEqual(response.status_code, 302)
        self.assertEqual([c.pk for c in generar.call_args.args[0]], [cuenta.pk])
        self.assertEqual(list(self.tenant.manuales.get().cuentas.all()), [cuenta])

    def test_no_se_puede_generar_con_cuenta_de_otra_organizacion(self):
        asegurar_catalogo_sat()
        codigo = CodigoAgrupador.objects.get(codigoagrupador='101')
        self.crear_cuenta('A', codigo)
        otro = Tenant.objects.create(nombre='Ajeno', propietario=self.user)
        ajena = self.crear_cuenta('B', codigo, tenant=otro)
        with patch('catalogo.views.generar_contenido_manual') as generar:
            response = self.client.post(reverse('generar_manual'), {'cuentas': [str(ajena.pk)]})
        self.assertEqual(response.status_code, 302)
        generar.assert_not_called()


@override_settings(DEBUG=True, SECURE_SSL_REDIRECT=False)
class ConfirmarRelacionAjaxTests(TestCase):
    setUp = ImportacionSugeridaTests.setUp

    def preparar(self):
        codigo = CodigoAgrupador.objects.create(nivel=1, codigoagrupador='101', nombre='Caja')
        destino = CodigoAgrupador.objects.create(nivel=2, codigoagrupador='102.01', nombre='Bancos nacionales')
        cuenta = CatalogoCuentas.objects.create(tenant=self.tenant, cuenta='A', descripcion='Cuenta A',
            codigoagrupador=codigo, relacion_sugerida=True, confianza_relacion=85)
        return cuenta, destino

    def post_ajax(self, cuenta, codigo):
        return self.client.post(reverse('confirmar_relacion', args=[cuenta.pk]),
            {'codigoagrupador': codigo}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def test_confirmar_solo_actualiza_una_cuenta_y_no_carga_catalogos(self):
        cuenta, codigo = self.preparar()
        otra = CatalogoCuentas.objects.create(tenant=self.tenant, cuenta='B', descripcion='Otra cuenta',
            codigoagrupador=cuenta.codigoagrupador, relacion_sugerida=True, confianza_relacion=70)
        with patch('catalogo.views.asegurar_catalogo_sat') as asegurar, patch('catalogo.views.render') as render:
            response = self.post_ajax(cuenta, codigo.codigoagrupador)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['cuenta'], {'id': cuenta.pk, 'codigoagrupador': '102.01', 'nombre_sat': 'Bancos nacionales'})
        asegurar.assert_not_called()
        render.assert_not_called()
        cuenta.refresh_from_db()
        otra.refresh_from_db()
        self.assertFalse(cuenta.relacion_sugerida)
        self.assertIsNone(cuenta.confianza_relacion)
        self.assertEqual(cuenta.codigoagrupador, codigo)
        self.assertTrue(otra.relacion_sugerida)
        self.assertEqual(otra.confianza_relacion, 70)
        self.assertNotEqual(otra.codigoagrupador, codigo)
        self.assertFalse(list(get_messages(response.wsgi_request)))

    def test_codigo_invalido_o_vacio_devuelve_json_sin_modificar(self):
        cuenta, _ = self.preparar()
        for codigo in ['', 'inexistente']:
            with self.subTest(codigo=codigo):
                response = self.post_ajax(cuenta, codigo)
                self.assertEqual(response.status_code, 400)
                self.assertFalse(response.json()['ok'])
                cuenta.refresh_from_db()
                self.assertTrue(cuenta.relacion_sugerida)

    def test_cuenta_ajena_no_se_modifica(self):
        cuenta, codigo = self.preparar()
        otro = Tenant.objects.create(nombre='Otro tenant', propietario=self.user)
        cuenta.tenant = otro
        cuenta.save()
        response = self.post_ajax(cuenta, codigo.codigoagrupador)
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json()['ok'])
        cuenta.refresh_from_db()
        self.assertTrue(cuenta.relacion_sugerida)

    def test_solo_acepta_post(self):
        cuenta, _ = self.preparar()
        self.assertEqual(self.client.get(reverse('confirmar_relacion', args=[cuenta.pk])).status_code, 405)

    def test_conserva_proteccion_csrf(self):
        from django.test import Client
        cuenta, codigo = self.preparar()
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        session = client.session
        session['tenant_id'] = self.tenant.pk
        session.save()
        response = client.post(reverse('confirmar_relacion', args=[cuenta.pk]),
            {'codigoagrupador': codigo.codigoagrupador}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)
        cuenta.refresh_from_db()
        self.assertTrue(cuenta.relacion_sugerida)


@override_settings(DEBUG=True, SECURE_SSL_REDIRECT=False)
class RendimientoCatalogoTests(TestCase):
    setUp = ImportacionSugeridaTests.setUp

    def test_pagina_25_cuentas_y_renderiza_una_sola_lista_sat(self):
        asegurar_catalogo_sat()
        CatalogoCuentas.objects.bulk_create([
            CatalogoCuentas(tenant=self.tenant, cuenta=f'{i:04d}', descripcion=f'Cuenta {i}')
            for i in range(70)
        ])
        response = self.client.get(reverse('catalogo_cuentas'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 70)
        self.assertEqual(len(response.context['cuentas']), 25)
        html = response.content.decode()
        self.assertEqual(html.count('<datalist '), 1)
        self.assertEqual(html.count('<option '), CodigoAgrupador.objects.count())
        self.assertEqual(html.count('data-confirmar-relacion'), 25)
        self.assertNotIn('<select name="codigoagrupador"', html)
        self.assertLess(len(response.content), 300000)
        self.assertContains(response, 'Primero selecciona un código SAT')
        self.assertContains(response, 'type="submit" disabled')
        response = self.client.get(reverse('catalogo_cuentas'), {'page': 3})
        self.assertEqual(len(response.context['cuentas']), 20)
        self.assertEqual(response.context['cuentas'].number, 3)

    def test_busqueda_y_pagina_no_muestran_cuentas_ajenas(self):
        otro = Tenant.objects.create(nombre='Otro tenant', propietario=self.user)
        CatalogoCuentas.objects.create(tenant=otro, cuenta='PRIVADA', descripcion='Cuenta ajena')
        CatalogoCuentas.objects.create(tenant=self.tenant, cuenta='A', descripcion='Banco propio')
        response = self.client.get(reverse('catalogo_cuentas'), {'q': 'Banco', 'page': 1})
        self.assertEqual(response.context['total'], 1)
        self.assertContains(response, 'Banco propio')
        self.assertNotContains(response, 'Cuenta ajena')


@override_settings(DEBUG=True, SECURE_SSL_REDIRECT=False)
class ConfirmarSugerenciaManualTests(TestCase):
    setUp = ImportacionSugeridaTests.setUp
    preparar = ConfirmarRelacionAjaxTests.preparar

    def test_boton_solo_para_cuentas_con_sugerencia_y_en_ambas_vistas(self):
        cuenta, codigo = self.preparar()
        CatalogoCuentas.objects.create(tenant=self.tenant, cuenta='B', descripcion='Sin relación')
        response = self.client.get(reverse('generar_manual'))
        self.assertContains(response, 'data-confirmar-sugerencia', count=2)
        self.assertContains(response, f'data-url="{reverse("confirmar_relacion", args=[cuenta.pk])}"', count=2)
        self.assertContains(response, 'type="button" data-confirmar-sugerencia', count=2)

    def test_confirmar_desde_manual_permite_generar_sin_visitar_catalogo(self):
        cuenta, codigo = self.preparar()
        response = self.client.post(reverse('confirmar_relacion', args=[cuenta.pk]),
            {'codigoagrupador': cuenta.codigoagrupador.codigoagrupador},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        with patch('catalogo.views.generar_contenido_manual', return_value='Manual confirmado') as generar:
            response = self.client.post(reverse('generar_manual'), {'cuentas': [str(cuenta.pk)]})
        self.assertEqual(response.status_code, 302)
        generar.assert_called_once()
        self.assertEqual(list(self.tenant.manuales.get().cuentas.all()), [cuenta])


@override_settings(DEBUG=True, SECURE_SSL_REDIRECT=False)
class ModalVinculacionManualTests(TestCase):
    setUp = ImportacionSugeridaTests.setUp

    def test_cuenta_sin_relacion_tiene_boton_en_ambas_vistas_y_modal_unico(self):
        cuenta = CatalogoCuentas.objects.create(tenant=self.tenant, cuenta='A', descripcion='Caja chica')
        response = self.client.get(reverse('generar_manual'))
        self.assertContains(response, 'type="button" data-vincular-sat', count=2)
        self.assertContains(response, 'id="modal-vincular-sat"', count=1)
        self.assertContains(response, f'data-url="{reverse("confirmar_relacion", args=[cuenta.pk])}"', count=2)
        self.assertContains(response, 'Buscar por código o nombre')
        self.assertGreater(len(response.context['opciones_sat_modal']), 1000)

    def test_vincular_cuenta_sin_codigo_desde_modal_y_generar_manual(self):
        cuenta = CatalogoCuentas.objects.create(tenant=self.tenant, cuenta='A', descripcion='Caja chica')
        asegurar_catalogo_sat()
        response = self.client.post(reverse('confirmar_relacion', args=[cuenta.pk]),
            {'codigoagrupador': '101.01'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        cuenta.refresh_from_db()
        self.assertEqual(cuenta.codigoagrupador.codigoagrupador, '101.01')
        self.assertFalse(cuenta.relacion_sugerida)
        response = self.client.get(reverse('generar_manual'))
        grupo = next(g for g in response.context['grupos_sat'] if g['codigo'].codigoagrupador == '101.01')
        self.assertEqual(grupo['cuentas'], [cuenta])
        self.assertEqual(response.context['cuentas_sin_vinculo'], [])
        self.assertNotContains(response, 'data-vincular-sat')
        with patch('catalogo.views.generar_contenido_manual', return_value='Manual vinculado'):
            response = self.client.post(reverse('generar_manual'), {'cuentas': [cuenta.pk]})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.tenant.manuales.get().contenido, 'Manual vinculado')
