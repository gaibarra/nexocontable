import re
from datetime import timedelta
from smtplib import SMTPException
from unittest.mock import patch
from urllib.parse import urlparse
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


@override_settings(DEBUG=True, SECURE_SSL_REDIRECT=False,
                   EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                   PASSWORD_RESET_DOMAIN='manualcontable.online', PASSWORD_RESET_TIMEOUT=3600)
class RecuperacionPasswordTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='contadora', email='contadora@example.com', password='Anterior#Segura2026')

    def solicitar(self, correo=None, **kwargs):
        return self.client.post(reverse('password_reset'), {'email': correo or self.user.email}, **kwargs)

    def enlace(self):
        return urlparse(re.search(r'https://[^\s]+/restablecer/[^\s]+/', mail.outbox[-1].body).group()).path

    def formulario_nueva(self):
        self.solicitar()
        enlace = self.enlace()
        response = self.client.get(enlace)
        self.assertEqual(response.status_code, 302)
        self.assertIn('set-password', response.url)
        return enlace, response.url

    def test_envia_enlace_https_y_correo_html_en_espanol(self):
        response = self.solicitar()
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        mensaje = mail.outbox[0]
        self.assertEqual(mensaje.to, [self.user.email])
        self.assertIn('NexoContable', mensaje.subject)
        self.assertIn('vence en una hora', mensaje.body)
        self.assertIn('https://manualcontable.online/restablecer/', mensaje.body)
        self.assertEqual(mensaje.alternatives[0][1], 'text/html')
        self.assertNotIn('Anterior#Segura2026', mensaje.body)

    def test_respuesta_no_revela_correos_inexistentes_inactivos_o_sin_acceso(self):
        User.objects.create_user(username='inactivo', email='inactivo@example.com', password='Anterior#Segura2026', is_active=False)
        invitado = User.objects.create_user(username='invitado', email='invitado@example.com')
        self.assertFalse(invitado.has_usable_password())
        for correo in ['ausente@example.com', 'inactivo@example.com', 'invitado@example.com']:
            response = self.solicitar(correo)
            self.assertRedirects(response, reverse('password_reset_done'))
            self.assertEqual(len(mail.outbox), 0)
        self.assertContains(self.client.get(reverse('password_reset_done')), 'Si el correo corresponde')

    def test_correo_invalido_se_puede_corregir(self):
        response = self.solicitar('sin-correo')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors.get('email'))
        self.assertEqual(len(mail.outbox), 0)

    def test_cambio_completo_invalida_enlace_y_permite_acceso_con_nueva_password(self):
        enlace, formulario = self.formulario_nueva()
        self.assertTrue(self.client.get(formulario).context['validlink'])
        response = self.client.post(formulario, {'new_password1': 'Nueva#Acceso2026', 'new_password2': 'Nueva#Acceso2026'})
        self.assertRedirects(response, reverse('password_reset_complete'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Nueva#Acceso2026'))
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertFalse(self.client.get(enlace).context['validlink'])
        self.assertFalse(self.client.get(formulario).context['validlink'])
        response = self.client.post(reverse('login'), {'username': self.user.email, 'password': 'Anterior#Segura2026'})
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('login'), {'username': self.user.email, 'password': 'Nueva#Acceso2026'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_contrasenas_no_coincidentes_o_debiles_no_se_guardan(self):
        _, formulario = self.formulario_nueva()
        for primera, segunda in [('Nueva#Acceso2026', 'Otra#Acceso2026'), ('12345678', '12345678')]:
            response = self.client.post(formulario, {'new_password1': primera, 'new_password2': segunda})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['form'].errors)
            self.assertNotContains(response, f'value="{primera}"')
            self.user.refresh_from_db()
            self.assertTrue(self.user.check_password('Anterior#Segura2026'))

    def test_enlace_vence_despues_de_una_hora(self):
        self.solicitar()
        enlace = self.enlace()
        futuro = default_token_generator._now() + timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT + 1)
        with patch.object(default_token_generator, '_now', return_value=futuro):
            response = self.client.get(enlace)
        self.assertFalse(response.context['validlink'])
        self.assertContains(response, 'Solicitar un nuevo enlace')

    def test_token_modificado_o_de_otro_usuario_no_funciona(self):
        otro = User.objects.create_user(username='otra', password='Otra#Acceso2026')
        token = default_token_generator.make_token(self.user)
        for uid, clave in [('invalido', 'invalido'), (urlsafe_base64_encode(force_bytes(self.user.pk)), token + 'x'),
                           (urlsafe_base64_encode(force_bytes(otro.pk)), token)]:
            response = self.client.get(reverse('password_reset_confirm', args=[uid, clave]))
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context['validlink'])

    @override_settings(ALLOWED_HOSTS=['testserver', 'otro.example'])
    def test_enlace_no_utiliza_el_host_del_solicitante(self):
        self.solicitar(HTTP_HOST='otro.example')
        self.assertIn('https://manualcontable.online/restablecer/', mail.outbox[0].body)
        self.assertNotIn('https://otro.example', mail.outbox[0].body)

    def test_csrf_protege_solicitud_y_cambio_de_password(self):
        cliente = Client(enforce_csrf_checks=True)
        response = cliente.post(reverse('password_reset'), {'email': self.user.email})
        self.assertEqual(response.status_code, 403)
        self.solicitar()
        response = cliente.get(self.enlace())
        formulario = response.url
        cliente.get(formulario)
        response = cliente.post(formulario, {'new_password1': 'Nueva#Acceso2026', 'new_password2': 'Nueva#Acceso2026'})
        self.assertEqual(response.status_code, 403)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Anterior#Segura2026'))

    def test_paginas_no_se_guardan_en_cache_y_no_filtran_referer(self):
        for nombre in ['password_reset', 'password_reset_done', 'password_reset_complete']:
            response = self.client.get(reverse(nombre))
            self.assertIn('no-store', response['Cache-Control'])
            self.assertEqual(response['Referrer-Policy'], 'no-referrer')
        enlace, formulario = self.formulario_nueva()
        response = self.client.get(formulario)
        token = enlace.strip('/').split('/')[-1]
        self.assertNotContains(response, token)
        self.assertIn('no-store', response['Cache-Control'])

    def test_usuario_sin_organizacion_puede_abrir_recuperacion(self):
        self.client.force_login(self.user)
        for nombre in ['password_reset', 'password_reset_done', 'password_reset_complete']:
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 200)

    @patch('django.core.mail.message.EmailMultiAlternatives.send', side_effect=SMTPException('Fallo simulado'))
    def test_fallo_de_correo_no_revela_si_la_cuenta_existe(self, enviar):
        with self.assertLogs('cuentas.password_reset', level='ERROR'):
            response = self.solicitar()
        self.assertRedirects(response, reverse('password_reset_done'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Anterior#Segura2026'))

    @patch('cuentas.password_reset.get_connection')
    def test_correo_no_disponible_avisa_igual_para_todos(self, conexion):
        conexion.return_value.open.side_effect = SMTPException('Fallo simulado')
        for correo in [self.user.email, 'desconocido@example.com']:
            with self.assertLogs('cuentas.password_reset', level='ERROR'):
                response = self.solicitar(correo)
            self.assertEqual(response.status_code, 503)
            self.assertContains(response, 'no está disponible en este momento', status_code=503)
            self.assertEqual(response['Retry-After'], '300')
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Anterior#Segura2026'))
