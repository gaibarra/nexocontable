from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from .models import Tenant, MembresiaTenant, InvitacionAcceso


@override_settings(
	DEBUG=True,
	SECURE_SSL_REDIRECT=False,
	EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class RegistrarColegaTests(TestCase):
	def setUp(self):
		self.owner = User.objects.create_user(
			username='owner@example.com',
			email='owner@example.com',
			password='StrongPass123!',
		)
		self.tenant = Tenant.objects.create(nombre='Org Demo', propietario=self.owner)
		MembresiaTenant.objects.create(tenant=self.tenant, usuario=self.owner, rol='propietario')

		self.client.login(username='owner@example.com', password='StrongPass123!')

	def test_registro_colega_crea_invitacion_segura(self):
		response = self.client.post(
			reverse('registrar_usuario', args=[self.tenant.pk]),
			{
				'nombre': 'Colega Nuevo',
				'email': 'colega@example.com',
				'rol': 'auxiliar',
			},
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Se envió un enlace de acceso seguro')

		user = User.objects.get(email='colega@example.com')
		self.assertFalse(user.has_usable_password())

		invitacion = InvitacionAcceso.objects.filter(usuario=user, tenant=self.tenant).first()
		self.assertIsNotNone(invitacion)
		self.assertIsNone(invitacion.usado_en)
		self.assertGreater(invitacion.expira_en, timezone.now())

	def test_establecer_password_invitacion_usa_token_una_vez(self):
		user = User.objects.create_user(username='colega@example.com', email='colega@example.com')
		user.set_unusable_password()
		user.save()

		invitacion = InvitacionAcceso.objects.create(
			token='token-seguro-123',
			usuario=user,
			tenant=self.tenant,
			rol='auxiliar',
			creado_por=self.owner,
			expira_en=timezone.now() + timedelta(hours=24),
		)

		url = reverse('establecer_password_invitacion', args=[invitacion.token])
		response = self.client.post(
			url,
			{
				'new_password1': 'NuevaClaveSegura#2026',
				'new_password2': 'NuevaClaveSegura#2026',
			},
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		user.refresh_from_db()
		invitacion.refresh_from_db()
		self.assertTrue(user.check_password('NuevaClaveSegura#2026'))
		self.assertIsNotNone(invitacion.usado_en)

		second = self.client.get(url, follow=True)
		self.assertEqual(second.status_code, 200)
		self.assertContains(second, 'expiró o ya fue utilizado')

	def test_establecer_password_invitacion_expirada(self):
		user = User.objects.create_user(username='expira@example.com', email='expira@example.com')
		invitacion = InvitacionAcceso.objects.create(
			token='token-expirado-123',
			usuario=user,
			tenant=self.tenant,
			rol='auxiliar',
			creado_por=self.owner,
			expira_en=timezone.now() - timedelta(minutes=1),
		)

		response = self.client.get(
			reverse('establecer_password_invitacion', args=[invitacion.token]),
			follow=True,
		)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'expiró o ya fue utilizado')

	def test_editar_tenant_renderiza_correctamente(self):
		response = self.client.get(reverse('editar_tenant', args=[self.tenant.pk]))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Editar —')


@override_settings(
    DEBUG=False,
    SECURE_SSL_REDIRECT=False,
    AUTHENTICATION_BACKENDS=[
        'cuentas.backends.EmailOrUsernameBackend',
        'django.contrib.auth.backends.ModelBackend',
    ],
)
class RegistroTests(TestCase):
    def setUp(self):
        self.data = {
            'email': 'registro@example.com',
            'version_aviso': '2026-10-25',
            'password': 'PruebaSegura#2026',
            'password_confirm': 'PruebaSegura#2026',
            'nombre_completo': 'Persona de Prueba',
            'especialidad': 'contabilidad_general',
            'ciudad': 'Mexicali', 'estado': 'BC', 'acepta_terminos': 'on',
        }

    def test_registro_con_dos_backends_inicia_sesion(self):
        from .models import PerfilCPC
        response = self.client.post(reverse('registro'), self.data)
        self.assertRedirects(response, reverse('crear_tenant'), fetch_redirect_response=False)
        user = User.objects.get(email=self.data['email'])
        self.assertTrue(PerfilCPC.objects.filter(usuario=user).exists())
        self.assertEqual(self.client.session['_auth_user_id'], str(user.pk))
        self.assertEqual(self.client.session['_auth_user_backend'], 'cuentas.backends.EmailOrUsernameBackend')
        page = self.client.get(reverse('crear_tenant'))
        self.assertContains(page, 'app-notifications')
        self.assertContains(page, '¡Bienvenido!')

    def test_fallo_de_login_revierte_usuario_y_perfil(self):
        from unittest.mock import patch
        from .models import PerfilCPC
        initial = PerfilCPC.objects.count()
        with patch('cuentas.views.login', side_effect=RuntimeError('Fallo simulado')):
            with self.assertRaises(RuntimeError):
                self.client.post(reverse('registro'), self.data)
        self.assertFalse(User.objects.filter(email=self.data['email']).exists())
        self.assertEqual(PerfilCPC.objects.count(), initial)

    def test_formulario_invalido_muestra_notificacion_sin_crear_usuario(self):
        self.data['password_confirm'] = 'Diferente#2026'
        response = self.client.post(reverse('registro'), self.data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'app-notifications')
        self.assertContains(response, 'Las contraseñas no coinciden.')
        self.assertNotContains(response, self.data['password'])
        self.assertFalse(User.objects.filter(email=self.data['email']).exists())


class NotificationTests(TestCase):
    def test_mensajes_se_serializan_sin_inyectar_html(self):
        from django.contrib.messages.storage.base import Message
        from django.template import Context, Template
        text = '</script><img src=x onerror=alert(1)>'
        rendered = Template('{% load notifications %}{% app_notifications %}').render(
            Context({'messages': [Message(40, text), Message(25, 'Guardado')]}))
        self.assertNotIn(text, rendered)
        self.assertIn('\\u003C/script\\u003E', rendered)
        self.assertIn('"icon": "error"', rendered)
        self.assertIn('"icon": "success"', rendered)
