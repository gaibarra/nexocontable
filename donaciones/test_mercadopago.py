"""Pruebas de integración local: todo acceso al SDK queda simulado."""
import hashlib
import hmac
import json
import time
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from .models import Donativo


@override_settings(DEBUG=False, SECURE_SSL_REDIRECT=False, MERCADOPAGO_ACCESS_TOKEN='APP_USR-test-local',
                   MERCADOPAGO_WEBHOOK_SECRET='secreto-webhook-local', MERCADOPAGO_SANDBOX=False)
class MercadoPagoRobustezTests(TestCase):
    def setUp(self):
        self.donativo = Donativo.objects.create(monto='100', estado='pendiente', preference_id='pref-local')
        self.sdk_patch = patch('mercadopago.SDK')
        self.factory = self.sdk_patch.start(); self.addCleanup(self.sdk_patch.stop)
        self.sdk = self.factory.return_value
        self.payment = {'id': 123456, 'status': 'approved', 'external_reference': str(self.donativo.pk),
                        'transaction_amount': 100, 'currency_id': 'MXN', 'collector_id': 88,
                        'live_mode': True, 'date_last_updated': '2026-10-25T10:00:00.000-06:00',
                        'transaction_amount_refunded': 0, 'payer': {'email': 'donante@example.com'}}
        self.sdk.payment.return_value.get.side_effect = lambda *a, **k: {'status': 200, 'response': self.payment.copy()}
        self.sdk.preference.return_value.get.return_value = {'status': 200, 'response': {'id': 'pref-local', 'collector_id': 88, 'external_reference': str(self.donativo.pk)}}

    def notificar(self, client=None, payment_id='123456', firma=True, **kwargs):
        ts = str(int(time.time()))
        manifest = f'id:{payment_id};request-id:req-local;ts:{ts};'
        digest = hmac.new(b'secreto-webhook-local', manifest.encode(), hashlib.sha256).hexdigest()
        headers = {'HTTP_X_REQUEST_ID': 'req-local', 'HTTP_X_SIGNATURE': f'ts={ts},v1={digest}'} if firma else {}
        headers.update(kwargs)
        return (client or self.client).post(reverse('webhook_mercadopago') + '?data.id=' + payment_id + '&type=payment',
            data=json.dumps({'type': 'payment', 'data': {'id': payment_id}}), content_type='application/json', **headers)

    def test_webhook_firmado_no_necesita_cookie_csrf(self):
        response = self.notificar(client=Client(enforce_csrf_checks=True))
        self.assertEqual(response.status_code, 200)
        self.donativo.refresh_from_db(); self.assertEqual(self.donativo.estado, 'aprobado')

    def test_reembolso_posterior_a_aprobacion_no_se_ignora(self):
        self.donativo.estado = 'aprobado'; self.donativo.referencia_mp = '123456'; self.donativo.save()
        self.payment['status'] = 'refunded'; self.payment['transaction_amount_refunded'] = 100
        self.notificar()
        self.donativo.refresh_from_db(); self.assertEqual(self.donativo.estado, 'reembolsado')

    def test_monto_incorrecto_no_aprueba(self):
        self.payment['transaction_amount'] = 99
        self.notificar()
        self.donativo.refresh_from_db(); self.assertEqual(self.donativo.estado, 'pendiente')

    def test_error_del_proveedor_devuelve_error_reintentable(self):
        self.sdk.payment.return_value.get.side_effect = None
        self.sdk.payment.return_value.get.return_value = {'status': 500, 'response': {'message': 'Error simulado'}}
        self.assertEqual(self.notificar().status_code, 503)
        self.donativo.refresh_from_db(); self.assertEqual(self.donativo.estado, 'pendiente')

    @override_settings(DEBUG=True, MERCADOPAGO_WEBHOOK_SECRET='')
    def test_no_se_acepta_webhook_sin_secreto_ni_en_debug(self):
        self.assertEqual(self.notificar(firma=False).status_code, 503)
        self.factory.assert_not_called()

    def test_retorno_manipulado_no_afirma_un_pago_aprobado(self):
        response = self.client.get(reverse('donativo_exito') + f'?donativo_id={self.donativo.pk}&status=approved')
        self.assertNotContains(response, '¡Muchas gracias!')
        self.donativo.refresh_from_db(); self.assertEqual(self.donativo.estado, 'pendiente')

    def test_monto_con_fraccion_de_centavo_no_inicia_checkout(self):
        self.client.post(reverse('donar'), {'monto_custom': '100.001'})
        self.factory.assert_not_called()

    def test_anonimos_distintos_no_se_colapsan_en_un_solo_colaborador(self):
        self.donativo.estado='aprobado'; self.donativo.referencia_mp='123456'; self.donativo.save()
        Donativo.objects.create(monto=100, estado='aprobado', referencia_mp='otro-pago')
        response=self.client.get(reverse('donar'))
        self.assertEqual(response.context['total_donantes'], 2)

    def test_firma_incorrecta_no_consulta_api(self):
        response=self.notificar(HTTP_X_SIGNATURE='ts=1,v1='+'0'*64)
        self.assertEqual(response.status_code,401);self.factory.assert_not_called()

    def test_firma_ausente_no_consulta_api(self):
        self.assertEqual(self.notificar(firma=False).status_code,401);self.factory.assert_not_called()

    def test_webhook_solo_admite_post(self):
        self.assertEqual(self.client.get(reverse('webhook_mercadopago')).status_code,405)
        self.factory.assert_not_called()

    def test_json_invalido_se_rechaza(self):
        response=self.client.post(reverse('webhook_mercadopago'),data='{',content_type='application/json')
        self.assertEqual(response.status_code,400);self.factory.assert_not_called()

    def test_json_array_se_rechaza(self):
        response=self.client.post(reverse('webhook_mercadopago'),data='[]',content_type='application/json')
        self.assertEqual(response.status_code,400);self.factory.assert_not_called()

    def test_data_de_tipo_incorrecto_se_rechaza(self):
        response=self.client.post(reverse('webhook_mercadopago'),data=json.dumps({'type':'payment','data':[]}),content_type='application/json')
        self.assertEqual(response.status_code,400);self.factory.assert_not_called()

    def test_otro_tipo_de_evento_no_modifica_donativos(self):
        response=self.client.post(reverse('webhook_mercadopago'),data=json.dumps({'type':'merchant_order','data':{'id':'123'}}),content_type='application/json')
        self.assertEqual(response.status_code,200);self.factory.assert_not_called()

    def test_id_diferente_en_query_y_cuerpo_no_se_procesa(self):
        ts=str(int(time.time()));manifest=f'id:123456;request-id:req-local;ts:{ts};'
        digest=hmac.new(b'secreto-webhook-local',manifest.encode(),hashlib.sha256).hexdigest()
        response=self.client.post(reverse('webhook_mercadopago')+'?data.id=999',data=json.dumps({'type':'payment','data':{'id':'123456'}}),content_type='application/json',HTTP_X_REQUEST_ID='req-local',HTTP_X_SIGNATURE=f'ts={ts},v1={digest}')
        self.assertEqual(response.status_code,400);self.factory.assert_not_called()

    def test_moneda_incorrecta_no_aprueba(self):
        self.payment['currency_id']='USD';self.notificar();self.donativo.refresh_from_db()
        self.assertEqual(self.donativo.estado,'pendiente')

    @override_settings(MERCADOPAGO_COLLECTOR_ID='88')
    def test_receptor_incorrecto_no_aprueba(self):
        self.payment['collector_id']=99;self.notificar();self.donativo.refresh_from_db()
        self.assertEqual(self.donativo.estado,'pendiente')

    def test_pago_de_prueba_no_cuenta_como_produccion(self):
        self.payment['live_mode']=False;self.notificar();self.donativo.refresh_from_db()
        self.assertEqual(self.donativo.estado,'pendiente')

    def test_id_de_api_diferente_no_aprueba(self):
        self.payment['id']=999;self.notificar();self.donativo.refresh_from_db()
        self.assertEqual(self.donativo.estado,'pendiente')

    def test_referencia_de_otro_donativo_no_existe_se_ignora(self):
        self.payment['external_reference']='99999999'
        self.assertEqual(self.notificar().status_code,200)
        self.donativo.refresh_from_db();self.assertEqual(self.donativo.estado,'pendiente')

    def test_api_sin_referencia_no_aprueba(self):
        self.payment.pop('external_reference')
        self.notificar();self.donativo.refresh_from_db();self.assertEqual(self.donativo.estado,'pendiente')

    def test_api_sin_estado_no_aprueba_ni_asigna_pago(self):
        self.payment.pop('status');self.notificar();self.donativo.refresh_from_db()
        self.assertEqual(self.donativo.estado,'pendiente');self.assertIsNone(self.donativo.referencia_mp)

    def test_timeout_del_proveedor_permite_reintento(self):
        self.sdk.payment.return_value.get.side_effect=TimeoutError('Fallo local simulado')
        self.assertEqual(self.notificar().status_code,503)

    def test_rechazo_se_registra(self):
        self.payment['status']='rejected';self.notificar();self.donativo.refresh_from_db()
        self.assertEqual(self.donativo.estado,'rechazado')

    def test_cancelacion_se_registra(self):
        self.payment['status']='cancelled';self.notificar();self.donativo.refresh_from_db()
        self.assertEqual(self.donativo.estado,'cancelado')

    def test_contracargo_reemplaza_aprobacion(self):
        self.donativo.estado='aprobado';self.donativo.referencia_mp='123456';self.donativo.save()
        self.payment['status']='charged_back';self.notificar();self.donativo.refresh_from_db()
        self.assertEqual(self.donativo.estado,'contracargo')

    def test_parcial_no_reporta_total_integro_como_confirmado(self):
        self.payment['transaction_amount_refunded']=30;self.notificar();self.donativo.refresh_from_db()
        # No basta con conservar un "aprobado" de 100 cuando se devolvieron 30.
        self.assertNotEqual(self.donativo.estado,'aprobado')

    def test_notificaciones_duplicadas_no_crean_otro_donativo(self):
        initial=Donativo.objects.count();self.notificar();self.notificar()
        self.assertEqual(Donativo.objects.count(),initial)
        self.donativo.refresh_from_db();self.assertEqual(self.donativo.estado,'aprobado')

    def test_estado_antiguo_no_reemplaza_un_estado_mas_reciente(self):
        self.payment['status']='rejected';self.payment['date_last_updated']='2026-10-25T11:00:00-06:00';self.notificar()
        self.payment['status']='approved';self.payment['date_last_updated']='2026-10-25T10:00:00-06:00';self.notificar()
        self.donativo.refresh_from_db();self.assertEqual(self.donativo.estado,'rechazado')

    def test_otros_intentos_rechazados_no_quitan_aprobacion_confirmada(self):
        self.donativo.estado='aprobado';self.donativo.referencia_mp='pago-confirmado';self.donativo.save()
        self.payment['status']='rejected';self.notificar();self.donativo.refresh_from_db()
        self.assertEqual(self.donativo.estado,'aprobado');self.assertEqual(self.donativo.referencia_mp,'pago-confirmado')

    def test_no_se_registra_el_cuerpo_privado_del_webhook_en_logs(self):
        ts=str(int(time.time()));manifest=f'id:123456;request-id:req-local;ts:{ts};'
        digest=hmac.new(b'secreto-webhook-local',manifest.encode(),hashlib.sha256).hexdigest()
        with self.assertLogs('donaciones.views',level='INFO') as logs:
            self.client.post(reverse('webhook_mercadopago')+'?data.id=123456',data=json.dumps({'type':'payment','data':{'id':'123456'},'dato_privado':'MARCADOR_PRIVADO_DE_PRUEBA'}),content_type='application/json',HTTP_X_REQUEST_ID='req-local',HTTP_X_SIGNATURE=f'ts={ts},v1={digest}')
        self.assertNotIn('MARCADOR_PRIVADO_DE_PRUEBA',' '.join(logs.output))

    def test_pendiente_no_promete_un_correo_que_no_se_envia(self):
        response=self.client.get(reverse('donativo_pendiente'))
        self.assertNotContains(response,'Te llegará confirmación por email')

    def test_usuario_ajeno_no_ve_un_exito_solo_por_id_en_la_url(self):
        self.donativo.estado='aprobado';self.donativo.save()
        response=self.client.get(reverse('donativo_exito')+f'?donativo_id={self.donativo.pk}')
        self.assertNotContains(response,'¡Muchas gracias!')

    def test_donativos_rechazados_y_reembolsados_no_incrementan_colaboradores(self):
        for status in ['pendiente','rechazado','reembolsado']:
            Donativo.objects.create(monto=100,estado=status,email_donante=status+'@example.com')
        response=self.client.get(reverse('donar'))
        self.assertEqual(response.context['total_colaboradores'],40)

    def test_correos_repetidos_con_distinta_capitalizacion_son_un_colaborador(self):
        Donativo.objects.create(monto=100,estado='aprobado',email_donante='Persona@example.com')
        Donativo.objects.create(monto=100,estado='aprobado',email_donante='persona@example.com')
        self.assertEqual(self.client.get(reverse('donar')).context['total_donantes'],1)


@override_settings(DEBUG=False, SECURE_SSL_REDIRECT=False, MERCADOPAGO_ACCESS_TOKEN='APP_USR-local', MERCADOPAGO_WEBHOOK_SECRET='local-secret')
class MercadoPagoCheckoutTests(TestCase):
    def setUp(self):
        self.sdk_patch=patch('mercadopago.SDK');self.factory=self.sdk_patch.start();self.addCleanup(self.sdk_patch.stop)
        self.sdk=self.factory.return_value
        self.checkout='https://www.mercadopago.com.mx/checkout/v1/redirect?pref_id=pref-prueba'
        self.sdk.preference.return_value.create.return_value={'status':201,'response':{
            'id':'pref-prueba','init_point':self.checkout,
            'sandbox_init_point':'https://sandbox.mercadopago.com.mx/checkout/v1/redirect?pref_id=pref-prueba','collector_id':88}}

    def post(self, data=None, client=None):
        client=client or self.client
        response=client.get(reverse('donar'))
        token=response.context.get('checkout_token','')
        return client.post(reverse('donar'),{'monto':'500','checkout_token':token}|(data or {}))

    def test_checkout_anonimo_crea_pendiente_y_referencia(self):
        response=self.post();self.assertEqual(response.status_code,302);self.assertEqual(response.url,self.checkout)
        obj=Donativo.objects.get();self.assertEqual(obj.estado,'pendiente');self.assertIsNone(obj.usuario)
        payload=self.sdk.preference.return_value.create.call_args.args[0]
        self.assertEqual(payload['external_reference'],str(obj.pk));self.assertEqual(payload['items'][0]['currency_id'],'MXN')

    def test_monto_personalizado_tiene_prioridad(self):
        self.post({'monto':'500','monto_custom':'250.50'})
        self.assertEqual(self.sdk.preference.return_value.create.call_args.args[0]['items'][0]['unit_price'],250.5)

    def test_limites_10_y_100000_son_aceptados(self):
        for amount in ['10','100000']:
            with self.subTest(amount=amount):
                self.assertEqual(self.post({'monto_custom':amount}).url,self.checkout)

    def test_montos_invalidos_no_llaman_al_proveedor(self):
        for amount in ['0','-1','9.99','100000.01','NaN','Infinity','-Infinity','texto','']:
            with self.subTest(amount=amount):
                self.factory.reset_mock()
                self.post({'monto':amount})
                self.factory.assert_not_called()

    def test_montos_de_mas_de_dos_decimales_se_rechazan(self):
        self.post({'monto_custom':'10.001'});self.factory.assert_not_called()

    def test_csrf_sigue_obligatorio_para_crear_checkout(self):
        response=Client(enforce_csrf_checks=True).post(reverse('donar'),{'monto':'500'})
        self.assertEqual(response.status_code,403);self.factory.assert_not_called()

    def test_error_api_no_redirige_a_checkout_ni_confirma_pago(self):
        self.sdk.preference.return_value.create.return_value={'status':401,'response':{'message':'token inválido simulado'}}
        self.assertEqual(self.post().url,reverse('donar'))
        self.assertFalse(Donativo.objects.filter(estado='aprobado').exists())

    def test_timeout_no_confirma_pago(self):
        self.sdk.preference.return_value.create.side_effect=TimeoutError('Error local simulado')
        self.assertEqual(self.post().url,reverse('donar'))
        self.assertFalse(Donativo.objects.filter(estado='aprobado').exists())

    def test_respuesta_sin_url_no_confirma_pago(self):
        self.sdk.preference.return_value.create.return_value={'status':201,'response':{'id':'pref-prueba'}}
        self.assertEqual(self.post().url,reverse('donar'))
        self.assertFalse(Donativo.objects.filter(estado='aprobado').exists())

    def test_url_de_salida_no_puede_apuntar_a_un_sitio_ajeno(self):
        self.sdk.preference.return_value.create.return_value={'status':201,'response':{'id':'pref-prueba','init_point':'https://example.com/pago'}}
        self.assertEqual(self.post().url,reverse('donar'))

    def test_url_de_salida_no_admite_http(self):
        self.sdk.preference.return_value.create.return_value={'status':201,'response':{'id':'pref-prueba','init_point':'http://www.mercadopago.com.mx/checkout'}}
        self.assertEqual(self.post().url,reverse('donar'))

    def test_respuesta_nula_del_sdk_muestra_error_controlado(self):
        self.sdk.preference.return_value.create.return_value=None
        self.assertEqual(self.post().url,reverse('donar'))
        self.assertFalse(Donativo.objects.filter(estado='aprobado').exists())

    def test_reenvio_del_mismo_formulario_no_crea_dos_checkouts(self):
        response=self.client.get(reverse('donar'));token=response.context.get('checkout_token','')
        payload={'monto':'500','checkout_token':token}
        self.client.post(reverse('donar'),payload);self.client.post(reverse('donar'),payload)
        self.assertEqual(self.sdk.preference.return_value.create.call_count,1)

    def test_urls_de_retorno_y_webhook_son_https_canonicas(self):
        response=self.client.get(reverse('donar'),secure=True,HTTP_HOST='manualcontable.online')
        self.client.post(reverse('donar'),{'monto':'500','checkout_token':response.context['checkout_token']},secure=True,HTTP_HOST='manualcontable.online')
        payload=self.sdk.preference.return_value.create.call_args.args[0]
        self.assertTrue(payload['notification_url'].startswith('https://manualcontable.online/'))
        for value in payload['back_urls'].values():
            self.assertTrue(value.startswith('https://manualcontable.online/'))

    @override_settings(MERCADOPAGO_ACCESS_TOKEN='')
    def test_sin_token_no_inicia_checkout(self):
        self.post();self.factory.assert_not_called()

    def test_checkout_fallido_no_se_confunde_con_pago_pendiente(self):
        self.sdk.preference.return_value.create.return_value={'status':401,'response':{'message':'Error simulado'}}
        self.post()
        self.assertFalse(Donativo.objects.filter(estado='pendiente',preference_id__isnull=True).exists())

    @override_settings(MERCADOPAGO_WEBHOOK_SECRET='')
    def test_sin_secreto_de_confirmacion_no_se_inicia_checkout(self):
        self.post();self.factory.assert_not_called()

    def test_sdk_tiene_timeout_acotado_y_reintentos_controlados(self):
        self.post()
        options=self.factory.call_args.kwargs.get('request_options')
        self.assertIsNotNone(options,'Se están usando timeout y reintentos predeterminados del SDK')
        self.assertLessEqual(options.connection_timeout,10)
        self.assertLessEqual(options.max_retries,1)
