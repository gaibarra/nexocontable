import hashlib
import hmac
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Donativo


@override_settings(MERCADOPAGO_ACCESS_TOKEN='APP_USR-prueba-local', MERCADOPAGO_SANDBOX=False)
class DonacionesWebhookTests(TestCase):
	def _build_signature(self, secret, payment_id, request_id, ts):
		manifest = f'id:{payment_id};request-id:{request_id};ts:{ts};'
		digest = hmac.new(
			secret.encode('utf-8'),
			msg=manifest.encode('utf-8'),
			digestmod=hashlib.sha256,
		).hexdigest()
		return f'ts={ts},v1={digest}'

	@override_settings(DEBUG=True, SECURE_SSL_REDIRECT=False, MERCADOPAGO_WEBHOOK_SECRET='super-secret-webhook-key')
	def test_webhook_rechaza_firma_invalida(self):
		payload = {'type': 'payment', 'data': {'id': '778899'}}
		response = self.client.post(
			reverse('webhook_mercadopago'),
			data=payload,
			content_type='application/json',
			HTTP_X_REQUEST_ID='req-invalid',
			HTTP_X_SIGNATURE='ts=1700000000,v1=firma-invalida',
		)

		self.assertEqual(response.status_code, 401)

	@override_settings(DEBUG=True, SECURE_SSL_REDIRECT=False, MERCADOPAGO_WEBHOOK_SECRET='super-secret-webhook-key')
	def test_webhook_aprueba_donativo_con_firma_valida(self):
		user = User.objects.create_user(username='donante@example.com', email='donante@example.com', password='StrongPass123!')
		donativo = Donativo.objects.create(
			usuario=user,
			nombre_donante='Donante Demo',
			email_donante='donante@example.com',
			monto='100.00',
			estado='pendiente',
			preference_id='pref-local', collector_mp='88',
		)

		payment_id = '123456'
		request_id = 'req-valid'
		ts = '1700000000'
		signature = self._build_signature('super-secret-webhook-key', payment_id, request_id, ts)
		payload = {'type': 'payment', 'data': {'id': payment_id}}

		class FakePaymentClient:
			def get(self, _payment_id):
				return {
					'status': 200,
					'response': {
						'id': 123456, 'transaction_amount': 100, 'currency_id': 'MXN',
						'collector_id': 88, 'live_mode': True, 'transaction_amount_refunded': 0,
						'date_last_updated': '2026-10-25T11:00:00-06:00',
						'external_reference': str(donativo.id),
						'status': 'approved',
					}
				}

		class FakeSDK:
			def __init__(self, _token, **kwargs):
				pass

			def payment(self):
				return FakePaymentClient()

		fake_mp_module = SimpleNamespace(SDK=FakeSDK)

		with patch.dict('sys.modules', {'mercadopago': fake_mp_module}):
			response = self.client.post(
				reverse('webhook_mercadopago'),
				data=payload,
				content_type='application/json',
				HTTP_X_REQUEST_ID=request_id,
				HTTP_X_SIGNATURE=signature,
			)

		donativo.refresh_from_db()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(donativo.estado, 'aprobado')
		self.assertEqual(donativo.referencia_mp, payment_id)


@override_settings(DEBUG=True, SECURE_SSL_REDIRECT=False)
class DonacionesPublicasTests(TestCase):
    def test_colaboradores_incluye_base_sin_donativos(self):
        response = self.client.get(reverse('donar'))
        self.assertEqual(response.context['total_colaboradores'], 40)
        self.assertContains(response, 'aboradores con donativo confirmado.')
        self.assertNotContains(response, 'Recaudado')
        self.assertNotIn('total_recaudado', response.context)

    def test_base_se_suma_a_colaboradores_confirmados_sin_duplicar_correo(self):
        for email, estado in [('uno@example.com', 'aprobado'), ('uno@example.com', 'aprobado'),
                              ('dos@example.com', 'aprobado'), ('pendiente@example.com', 'pendiente')]:
            Donativo.objects.create(email_donante=email, estado=estado, monto=12345)
        response = self.client.get(reverse('donar'))
        self.assertEqual(response.context['total_colaboradores'], 42)
        self.assertNotContains(response, '12345')
        self.assertNotContains(response, 'Recaudado')

    def test_privacidad_disponible_y_plegada_al_abrir(self):
        from bs4 import BeautifulSoup
        response = self.client.get(reverse('donar'))
        html = BeautifulSoup(response.content, 'html.parser')
        details = html.select_one('[data-donation-privacy]')
        self.assertIsNotNone(details)
        self.assertFalse(details.has_attr('open'))
        self.assertIn('Ver privacidad y uso de tus datos', details.summary.get_text())
        self.assertIn('proyectog40@gmail.com', details.get_text())
        self.assertTrue(html.select('a[href="/aviso-de-privacidad/"]'))
