import time
from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from cuentas.models import Tenant
from catalogo.models import ManualContable
from .controls import reservar_generacion
from .models import AccesoPanel, Contacto, ControlPlataforma, CupoDiario, Evento, Nota, Tarea
from .security import codigo, secreto, validar_totp
from .services import sincronizar_usuario

User = get_user_model()


class PanelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user('creador', email='creador@example.com', password='Test-password-99')
        cls.access = AccesoPanel.objects.create(usuario=cls.owner, rol='propietario')
        cls.normal = User.objects.create_user('contador', email='contador@example.com', password='Test-password-99')
        cls.contact = Contacto.objects.create(nombre='Prospecto', email='prospecto@example.com')

    def entrar(self, user=None):
        user = user or self.owner
        self.client.force_login(user)
        session = self.client.session
        session['panel_2fa'] = user.pk
        session.save()

    def test_anonimo_no_ve_datos(self):
        for name in ['inicio', 'crm', 'actividad', 'usuarios', 'organizaciones', 'inteligencia', 'donativos', 'oportunidades', 'controles', 'salud']:
            self.assertRedirects(self.client.get(reverse('panel:' + name)), reverse('panel:login'), fetch_redirect_response=False)

    def test_usuario_regular_y_superusuario_sin_autorizacion_no_entran(self):
        self.normal.is_superuser = True
        self.normal.save()
        self.client.force_login(self.normal)
        self.assertEqual(self.client.get(reverse('panel:inicio')).status_code, 403)
        self.client.logout()
        response = self.client.post(reverse('panel:login'), {'username': 'contador', 'password': 'Test-password-99'})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_password_requiere_segundo_factor(self):
        response = self.client.post(reverse('panel:login'), {'username': 'creador', 'password': 'Test-password-99'})
        self.assertRedirects(response, reverse('panel:verificar'), fetch_redirect_response=False)
        self.assertRedirects(self.client.get(reverse('panel:inicio')), reverse('panel:verificar'), fetch_redirect_response=False)
        response = self.client.get(reverse('panel:verificar'))
        self.assertContains(response, 'Protege tu centro de mando')
        secret = self.client.session['panel_enrolamiento']
        value = codigo(secret, int(time.time()) // 30)
        self.assertRedirects(self.client.post(reverse('panel:verificar'), {'codigo': value}), reverse('panel:inicio'), fetch_redirect_response=False)
        self.access.refresh_from_db()
        self.assertEqual(self.access.secreto_totp, secret)
        self.assertIsNone(validar_totp(secret, value, self.access.ultimo_paso))
        self.assertEqual(self.client.session['panel_2fa'], self.owner.pk)

    def test_verificacion_caduca(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('panel:verificar'))
        self.assertRedirects(response, reverse('panel:login'), fetch_redirect_response=False)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_totp_vector_estandar_y_rechazo(self):
        # RFC 6238: a los 59 segundos, SHA1 da 94287082, truncado a seis cifras.
        secret = 'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ'
        self.assertEqual(codigo(secret, 1), '287082')
        self.assertIsNone(validar_totp(secret, 'abcdef'))
        self.assertIsNone(validar_totp(secret, '１２３４５６'))

    def test_limite_password_compartido(self):
        for _ in range(10):
            self.client.post(reverse('panel:login'), {'username': 'creador', 'password': 'incorrecta'})
        response = self.client.post(reverse('panel:login'), {'username': 'creador', 'password': 'Test-password-99'})
        self.assertContains(response, 'Demasiados intentos')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_todas_las_paginas_con_datos_reales(self):
        self.entrar()
        Tenant.objects.create(nombre='Empresa real', propietario=self.normal)
        for name in ['inicio', 'crm', 'actividad', 'usuarios', 'organizaciones', 'inteligencia', 'donativos', 'oportunidades', 'controles', 'salud', 'contacto_nuevo']:
            with self.subTest(name=name):
                response = self.client.get(reverse('panel:' + name))
                self.assertEqual(response.status_code, 200)
                self.assertIn('no-store', response['Cache-Control'])
        self.assertEqual(self.client.get(reverse('panel:contacto', args=[self.contact.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('panel:usuario', args=[self.normal.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('panel:contacto_editar', args=[self.contact.pk])).status_code, 200)

    def test_consulta_no_puede_mutar(self):
        self.access.rol = 'consulta'; self.access.save()
        self.entrar()
        for name, args in [('sincronizar', []), ('nota', [self.contact.pk]), ('tarea', [self.contact.pk]), ('estado_usuario', [self.normal.pk]), ('estado_organizacion', [999]), ('contacto_editar', [self.contact.pk]), ('controles', [])]:
            self.assertEqual(self.client.post(reverse('panel:' + name, args=args)).status_code, 403)

    def test_revocar_acceso_invalida_sesion(self):
        self.entrar()
        self.access.activo = False; self.access.save()
        self.assertEqual(self.client.get(reverse('panel:crm')).status_code, 403)

    def test_crm_crear_nota_tarea_y_completar(self):
        self.entrar()
        response = self.client.post(reverse('panel:contacto_nuevo'), {'nombre': 'Nuevo', 'email': 'NUEVO@EXAMPLE.COM', 'etapa': 'prospecto', 'origen': 'Congreso'})
        obj = Contacto.objects.get(email='nuevo@example.com')
        self.assertRedirects(response, reverse('panel:contacto', args=[obj.pk]), fetch_redirect_response=False)
        self.client.post(reverse('panel:nota', args=[obj.pk]), {'texto': '<script>privado</script>'})
        self.assertContains(self.client.get(reverse('panel:contacto', args=[obj.pk])), '&lt;script&gt;privado&lt;/script&gt;')
        self.client.post(reverse('panel:tarea', args=[obj.pk]), {'titulo': 'Llamar', 'vence': '2026-11-01'})
        task = Tarea.objects.get(contacto=obj)
        self.client.post(reverse('panel:completar_tarea', args=[task.pk]))
        task.refresh_from_db(); self.assertTrue(task.completada)
        self.assertTrue(Evento.objects.filter(accion='tarea.completada', actor=self.owner).exists())

    def test_crm_correo_insensible_mayusculas(self):
        self.entrar()
        response = self.client.post(reverse('panel:contacto_nuevo'), {'nombre': 'Duplicado', 'email': 'PROSPECTO@example.com', 'etapa': 'prospecto', 'origen': 'Manual'})
        self.assertContains(response, 'Ya existe un contacto')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Contacto.objects.create(nombre='Duplicado', email='PROSPECTO@example.com')

    def test_sincronizar_idempotente_conserva_contexto(self):
        self.contact.email = self.normal.email; self.contact.etapa = 'perdido'; self.contact.save()
        Nota.objects.create(contacto=self.contact, autor=self.owner, texto='No perder')
        sincronizar_usuario(self.normal); sincronizar_usuario(self.normal)
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.usuario, self.normal)
        self.assertEqual(self.contact.etapa, 'perdido')
        self.assertEqual(self.contact.notas.count(), 1)
        self.assertEqual(Contacto.objects.filter(usuario=self.normal).count(), 1)

    def test_etapa_avanza_segun_uso(self):
        obj = sincronizar_usuario(self.normal)
        self.assertEqual(obj.etapa, 'registrado')
        org = Tenant.objects.create(nombre='Cliente', propietario=self.normal)
        obj = sincronizar_usuario(self.normal); self.assertEqual(obj.etapa, 'organizacion')
        ManualContable.objects.create(tenant=org, creado_por=self.normal, titulo='Manual', contenido='Texto')
        obj = sincronizar_usuario(self.normal); self.assertEqual(obj.etapa, 'manual')
        ManualContable.objects.create(tenant=org, creado_por=self.normal, titulo='Otro', contenido='Texto')
        obj = sincronizar_usuario(self.normal); self.assertEqual(obj.etapa, 'recurrente')

    def test_suspender_exige_motivo_y_no_autosuspension(self):
        self.entrar()
        self.client.post(reverse('panel:estado_usuario', args=[self.normal.pk]))
        self.normal.refresh_from_db(); self.assertTrue(self.normal.is_active)
        self.client.post(reverse('panel:estado_usuario', args=[self.normal.pk]), {'motivo': 'Solicitud del titular'})
        self.normal.refresh_from_db(); self.assertFalse(self.normal.is_active)
        self.assertEqual(self.client.post(reverse('panel:estado_usuario', args=[self.owner.pk]), {'motivo': 'Prueba'}).status_code, 403)
        self.assertTrue(Evento.objects.filter(accion='usuario.suspendido', detalle='Solicitud del titular').exists())

    def test_mutaciones_no_aceptan_get(self):
        self.entrar()
        for name, args in [('logout', []), ('sincronizar', []), ('nota', [self.contact.pk]), ('tarea', [self.contact.pk]), ('estado_usuario', [self.normal.pk])]:
            self.assertEqual(self.client.get(reverse('panel:' + name, args=args)).status_code, 405)

    def test_csrf_requerido(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse('panel:login'), {'username': 'creador', 'password': 'Test-password-99'}).status_code, 403)
        self.client = client
        self.entrar()
        self.assertEqual(client.post(reverse('panel:nota', args=[self.contact.pk]), {'texto': 'Sin token'}).status_code, 403)

    def test_evento_http_no_guarda_credenciales_ni_queries(self):
        self.entrar()
        self.client.post(reverse('panel:nota', args=[self.contact.pk]) + '?secreto=VALOR_PRIVADO', {'texto': 'CUERPO_PRIVADO'})
        eventos = ' '.join(Evento.objects.values_list('detalle', flat=True))
        self.assertNotIn('VALOR_PRIVADO', eventos)
        self.assertNotIn('CUERPO_PRIVADO', eventos)
        self.assertTrue(Evento.objects.filter(accion='panel:nota', detalle='POST').exists())

    def test_auditoria_solo_despues_de_commit(self):
        with self.captureOnCommitCallbacks(execute=True):
            org = Tenant.objects.create(nombre='Auditada', propietario=self.normal)
        self.assertTrue(Evento.objects.filter(accion='cuentas.tenant.creado', organizacion_id=org.pk).exists())

    def test_limites_ia_cuentan_solicitudes_y_cambian_por_dia(self):
        ControlPlataforma.objects.create(pk=1, limite_diario_usuario=2)
        self.assertEqual(reservar_generacion(self.normal), '')
        self.assertEqual(reservar_generacion(self.normal), '')
        self.assertIn('límite diario', reservar_generacion(self.normal))
        self.assertEqual(CupoDiario.objects.get(usuario=self.normal).solicitudes, 2)
        with patch('panel.controls.timezone.localdate', return_value=timezone.localdate()+timedelta(days=1)):
            self.assertEqual(reservar_generacion(self.normal), '')

    def test_pausa_ia_no_reserva(self):
        ControlPlataforma.objects.create(pk=1, generacion_habilitada=False)
        self.assertIn('pausada', reservar_generacion(self.normal))
        self.assertFalse(CupoDiario.objects.exists())

    def test_controles_guardan_y_exigen_motivo(self):
        self.entrar()
        response = self.client.post(reverse('panel:controles'), {'aviso': 'Mantenimiento', 'aviso_activo': 'on', 'limite_diario_usuario': '3'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ControlPlataforma.objects.get(pk=1).generacion_habilitada)
        self.client.post(reverse('panel:controles'), {'aviso': 'Mantenimiento', 'aviso_activo': 'on', 'limite_diario_usuario': '3', 'motivo': 'Ajuste operativo'})
        self.assertFalse(ControlPlataforma.objects.get(pk=1).generacion_habilitada)
        self.assertTrue(Evento.objects.filter(accion='controles.actualizados').exists())

    def test_filtros_invalidos_no_rompen_actividad(self):
        self.entrar()
        for query in ['?desde=no-fecha', '?desde=2026-99-99', '?usuario=abc&page=0', '?q=foo&categoria=http&organizacion=-3']:
            self.assertEqual(self.client.get(reverse('panel:actividad')+query).status_code, 200)

    @override_settings(ROOT_URLCONF='manual_contable_ai.urls')
    def test_aplicacion_publica_usa_puerta_sin_tenant(self):
        self.client.force_login(self.normal)
        with patch('panel.gateway.ConexionPanel') as conn:
            upstream = conn.return_value.getresponse.return_value
            upstream.status = 200; upstream.read.return_value = b'PANEL AISLADO'; upstream.getheaders.return_value = [('Set-Cookie', 'panel_sessionid=privada; Path=/panel/; HttpOnly'), ('Set-Cookie', 'panel_csrftoken=token; Path=/panel/')]
            response = self.client.get('/panel/')
        self.assertContains(response, 'PANEL AISLADO')
        self.assertIn('panel_sessionid', response.cookies)
        self.assertIn('panel_csrftoken', response.cookies)
        headers = conn.return_value.request.call_args.kwargs['headers']
        from http.cookies import SimpleCookie
        self.assertNotIn('sessionid', SimpleCookie(headers['Cookie']))

    @override_settings(ROOT_URLCONF='manual_contable_ai.urls')
    def test_pausa_conectada_a_generacion_no_llama_ia(self):
        from django.test import RequestFactory
        from django.contrib.messages.storage.fallback import FallbackStorage
        from catalogo.views import generar_manual
        from catalogo.models import CodigoAgrupador, CatalogoCuentas
        org = Tenant.objects.create(nombre='Empresa', propietario=self.normal)
        sat = CodigoAgrupador.objects.create(nivel=1, codigoagrupador='101', nombre='Caja')
        cuenta = CatalogoCuentas.objects.create(tenant=org, cuenta='1', descripcion='Caja', codigoagrupador=sat)
        ControlPlataforma.objects.create(pk=1, generacion_habilitada=False)
        request = RequestFactory().post('/catalogo/generar-manual/', {'cuentas': [str(cuenta.pk)]})
        request.user, request.tenant, request.session = self.normal, org, {}
        request._messages = FallbackStorage(request)
        with patch('catalogo.views.asegurar_catalogo_sat'), patch('catalogo.views.generar_contenido_manual') as proveedor:
            response = generar_manual(request)
        self.assertEqual(response.status_code, 302)
        proveedor.assert_not_called()
        self.assertFalse(CupoDiario.objects.exists())

    def test_aviso_escapa_html(self):
        from panel.controls import aviso_plataforma
        from django.test import RequestFactory
        from django.template import Template, Context
        ControlPlataforma.objects.create(pk=1, aviso='<script>AVISO</script>', aviso_activo=True)
        request = RequestFactory().get('/')
        request.user = self.normal
        data = aviso_plataforma(request)
        self.assertEqual(data['aviso_plataforma'], '<script>AVISO</script>')
        self.assertIn('&lt;script&gt;', Template('{{ aviso_plataforma }}').render(Context(data)))

    def test_consumo_con_proveedor_real_y_registros_incompletos(self):
        from catalogo.models import UsoIA
        self.entrar()
        UsoIA.objects.create(usuario=self.normal, intentos=[
            {'proveedor': 'deepseek', 'modelo': 'deepseek-flash', 'total': 8647},
            {'provider': 'openai', 'total': None},
            {},
        ])
        response = self.client.get(reverse('panel:inteligencia'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'deepseek')
        self.assertContains(response, 'openai')
        self.assertContains(response, 'Sin proveedor registrado')
