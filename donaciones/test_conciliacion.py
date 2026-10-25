"""Escenarios financieros y carreras reales de PostgreSQL; proveedor siempre simulado."""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch
from uuid import uuid4

from django.core import signing
from django.db import close_old_connections, connection
from django.test import Client, TestCase, TransactionTestCase, override_settings

from .mercadopago_service import conciliar
from .models import Donativo, PagoMercadoPago

CONFIG = dict(DEBUG=False, SECURE_SSL_REDIRECT=False,
              MERCADOPAGO_ACCESS_TOKEN='APP_USR-simulacion',
              MERCADOPAGO_WEBHOOK_SECRET='secreto-local', MERCADOPAGO_SANDBOX=False,
              MERCADOPAGO_COLLECTOR_ID='')


@override_settings(**CONFIG)
class ConciliacionFinancieraTests(TestCase):
    def setUp(self):
        self.obj = Donativo.objects.create(monto=100, preference_id='pref-local', collector_mp='88')
        self.payment = dict(id=123, external_reference=str(self.obj.pk), status='approved',
                            transaction_amount=100, transaction_amount_refunded=0, currency_id='MXN',
                            collector_id=88, live_mode=True, date_last_updated='2026-10-25T10:00:00Z')
        patcher = patch('mercadopago.SDK'); self.sdk = patcher.start().return_value
        self.addCleanup(patcher.stop)
        self.sdk.payment.return_value.get.side_effect = lambda *a, **k: {'status': 200, 'response': dict(self.payment)}

    def reconcile(self, **changes):
        self.payment.update(changes)
        conciliar(str(self.payment['id']))
        self.obj.refresh_from_db()

    def test_parcial_confirma_solo_neto_y_devolucion_total_lo_lleva_a_cero(self):
        self.reconcile(transaction_amount_refunded=30)
        self.assertEqual((self.obj.estado, self.obj.monto_confirmado, self.obj.monto_reembolsado),
                         ('parcial', Decimal('70'), Decimal('30')))
        self.reconcile(status='refunded', transaction_amount_refunded=100, date_last_updated='2026-10-25T11:00:00Z')
        self.assertEqual((self.obj.estado, self.obj.monto_confirmado), ('reembolsado', Decimal('0')))

    def test_dos_pagos_reales_en_misma_preferencia_se_suman(self):
        self.reconcile()
        self.reconcile(id=124, date_last_updated='2026-10-25T11:00:00Z')
        self.assertEqual(self.obj.monto_confirmado, Decimal('200'))
        self.reconcile(status='refunded', transaction_amount_refunded=100, date_last_updated='2026-10-25T12:00:00Z')
        self.assertEqual((self.obj.estado, self.obj.monto_confirmado), ('parcial', Decimal('100')))
        self.assertEqual(PagoMercadoPago.objects.count(), 2)

    def test_contracargo_no_cuenta_como_donativo_confirmado(self):
        self.reconcile()
        self.reconcile(status='charged_back', date_last_updated='2026-10-25T12:00:00Z')
        self.assertEqual((self.obj.estado, self.obj.monto_confirmado), ('contracargo', Decimal('0')))

    def test_otro_intento_rechazado_no_borra_neto_confirmado(self):
        self.reconcile()
        self.reconcile(id=124, status='rejected', date_last_updated='2026-10-25T12:00:00Z')
        self.assertEqual((self.obj.estado, self.obj.monto_confirmado, self.obj.referencia_mp),
                         ('aprobado', Decimal('100'), '123'))

    def test_version_antigua_no_revierte_reembolso(self):
        self.reconcile(status='refunded', transaction_amount_refunded=100, date_last_updated='2026-10-25T12:00:00Z')
        self.reconcile(status='approved', transaction_amount_refunded=0)
        self.assertEqual((self.obj.estado, self.obj.monto_confirmado), ('reembolsado', Decimal('0')))

    def test_resumen_no_persiste_tarjeta_documentos_ni_payer(self):
        self.reconcile(card={'last_four_digits': '1234'}, payer={'email': 'nuevo@example.com', 'identification': {'number': 'privado'}})
        self.assertNotIn('card', self.obj.datos_webhook)
        self.assertNotIn('payer', PagoMercadoPago.objects.get().resumen)
        self.assertEqual(self.obj.email_donante, 'nuevo@example.com')

    def test_retorno_firmado_depende_del_estado_en_base(self):
        token = signing.dumps({'id': self.obj.pk}, salt='mp-retorno')
        url = f'/donar/exito/?donativo_id={self.obj.pk}&token={token}&status=approved'
        self.assertNotContains(self.client.get(url), '¡Muchas gracias!')
        self.reconcile()
        self.assertContains(self.client.get(url), '¡Muchas gracias!')
        self.reconcile(status='refunded', transaction_amount_refunded=100, date_last_updated='2026-10-25T12:00:00Z')
        response = self.client.get(url)
        self.assertContains(response, 'Donativo reembolsado')
        self.assertNotContains(response, '¡Muchas gracias!')

    def test_token_de_otro_donativo_no_muestra_estado(self):
        self.reconcile()
        token = signing.dumps({'id': self.obj.pk + 1}, salt='mp-retorno')
        self.assertNotContains(self.client.get(f'/donar/exito/?donativo_id={self.obj.pk}&token={token}'), '¡Muchas gracias!')

    def test_no_se_reconcilian_otros_registros_al_notificar(self):
        old = Donativo.objects.create(monto=200, estado='aprobado', referencia_mp='900', preference_id='hist')
        self.reconcile()
        old.refresh_from_db()
        self.assertEqual((old.estado, old.monto_confirmado, old.referencia_mp), ('aprobado', None, '900'))
        self.assertFalse(old.pagos_mp.exists())


@override_settings(**CONFIG)
class ProteccionCheckoutTests(TestCase):
    def setUp(self):
        patcher = patch('mercadopago.SDK'); self.sdk = patcher.start().return_value
        self.addCleanup(patcher.stop)
        self.sdk.preference.return_value.create.return_value = {'status': 201, 'response': {
            'id': 'pref', 'collector_id': 88, 'init_point': 'https://www.mercadopago.com.mx/checkout',
            'sandbox_init_point': 'https://sandbox.mercadopago.com.mx/checkout'}}
        self.token = self.client.get('/donar/').context['checkout_token']

    def test_formulario_de_otra_sesion_no_crea_preferencia(self):
        Client().post('/donar/', {'monto': '100', 'checkout_token': self.token})
        self.sdk.preference.return_value.create.assert_not_called()
        self.assertEqual(Donativo.objects.count(), 0)

    def test_token_alterado_no_crea_preferencia(self):
        self.client.post('/donar/', {'monto': '100', 'checkout_token': self.token + 'x'})
        self.sdk.preference.return_value.create.assert_not_called()

    def test_reenvio_con_monto_distinto_no_cambia_solicitud(self):
        self.client.post('/donar/', {'monto': '100', 'checkout_token': self.token})
        self.client.post('/donar/', {'monto': '200', 'checkout_token': self.token})
        self.assertEqual(self.sdk.preference.return_value.create.call_count, 1)
        self.assertEqual(Donativo.objects.get().monto, Decimal('100'))

    @override_settings(MERCADOPAGO_SANDBOX=True)
    def test_sandbox_usa_su_propio_checkout(self):
        response = self.client.post('/donar/', {'monto': '100', 'checkout_token': self.token})
        self.assertEqual(response.url, 'https://sandbox.mercadopago.com.mx/checkout')

    def test_reintento_incierto_conserva_clave_y_referencia(self):
        self.sdk.preference.return_value.create.side_effect = [TimeoutError(), self.sdk.preference.return_value.create.return_value]
        data = {'monto': '100', 'checkout_token': self.token}
        self.client.post('/donar/', data); self.client.post('/donar/', data)
        calls = self.sdk.preference.return_value.create.call_args_list
        self.assertEqual(calls[0].args[0]['external_reference'], calls[1].args[0]['external_reference'])
        self.assertEqual(calls[0].kwargs['request_options'].custom_headers,
                         calls[1].kwargs['request_options'].custom_headers)
        self.assertEqual(Donativo.objects.count(), 1)


@skipUnless(connection.vendor == 'postgresql', 'Bloqueos transaccionales requieren PostgreSQL')
@override_settings(**CONFIG)
class ConcurrenciaMercadoPagoTests(TransactionTestCase):
    def run_parallel(self, task):
        barrier = Barrier(2)
        def worker():
            close_old_connections()
            try:
                barrier.wait(timeout=5)
                return task()
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(worker) for _ in range(2)]
            return [future.result(timeout=15) for future in futures]

    @patch('mercadopago.SDK')
    def test_dos_webhooks_simultaneos_registran_un_solo_pago(self, factory):
        obj = Donativo.objects.create(monto=100, preference_id='pref', collector_mp='88')
        factory.return_value.payment.return_value.get.return_value = {'status': 200, 'response': {
            'id': 123, 'external_reference': str(obj.pk), 'status': 'approved', 'transaction_amount': 100,
            'transaction_amount_refunded': 0, 'currency_id': 'MXN', 'collector_id': 88,
            'live_mode': True, 'date_last_updated': '2026-10-25T10:00:00Z'}}
        self.assertCountEqual(self.run_parallel(lambda: conciliar('123')), ['actualizado', 'duplicado_o_anterior'])
        obj.refresh_from_db()
        self.assertEqual(PagoMercadoPago.objects.count(), 1)
        self.assertEqual(obj.monto_confirmado, Decimal('100'))

    @patch('mercadopago.SDK')
    def test_dos_envios_simultaneos_crean_una_sola_preferencia(self, factory):
        factory.return_value.preference.return_value.create.return_value = {'status': 201, 'response': {
            'id': 'pref', 'collector_id': 88, 'init_point': 'https://www.mercadopago.com.mx/checkout'}}
        # Cookie firmada compartida por dos solicitudes del mismo navegador.
        from django.contrib.sessions.backends.signed_cookies import SessionStore
        from django.conf import settings
        session = SessionStore(); session['donation_checkout_nonce'] = 'nonce'; session.save()
        token = signing.dumps({'nonce': 'nonce', 'clave': str(uuid4())}, salt='mp-checkout')
        def submit():
            client = Client(); client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
            return client.post('/donar/', {'monto': '100', 'checkout_token': token}).status_code
        with override_settings(SESSION_ENGINE='django.contrib.sessions.backends.signed_cookies'):
            self.assertEqual(self.run_parallel(submit), [302, 302])
        self.assertEqual(Donativo.objects.count(), 1)
        self.assertEqual(factory.return_value.preference.return_value.create.call_count, 1)
