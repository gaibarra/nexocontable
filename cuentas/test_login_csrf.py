import re

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse


@override_settings(DEBUG=False, SECURE_SSL_REDIRECT=False, CSRF_COOKIE_SECURE=False,
                   SESSION_COOKIE_SECURE=False, ALLOWED_HOSTS=['testserver'])
class LoginCsrfTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='login-test@example.com', email='login-test@example.com', password='StrongPass123!')
        self.client = Client(enforce_csrf_checks=True)

    def token(self, response):
        return re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.content.decode()).group(1)

    def credentials(self, token):
        return {'username': self.user.email, 'password': 'StrongPass123!', 'csrfmiddlewaretoken': token}

    def test_login_no_se_almacena_en_cache_y_un_token_actual_funciona(self):
        response = self.client.get(reverse('login'))
        self.assertIn('no-store', response['Cache-Control'])
        self.assertIn('private', response['Cache-Control'])
        response = self.client.post(reverse('login'), self.credentials(self.token(response)))
        self.assertRedirects(response, reverse('dashboard'), fetch_redirect_response=False)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_cookie_rotada_rechaza_post_y_recupera_formulario(self):
        first = self.client.get(reverse('login'))
        old_token = self.token(first)
        self.client.cookies.pop('csrftoken')
        self.client.get(reverse('login'))
        response = self.client.post(reverse('login') + '?next=/catalogo/', self.credentials(old_token))
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.url, '/login/?next=%2Fcatalogo%2F')
        self.assertNotIn('_auth_user_id', self.client.session)
        fresh = self.client.get(response.url)
        self.assertContains(fresh, 'El formulario de acceso se desactualizó')
        self.assertNotContains(fresh, 'StrongPass123!')
        response = self.client.post(response.url, self.credentials(self.token(fresh)))
        self.assertRedirects(response, '/catalogo/', fetch_redirect_response=False)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_sin_cookie_o_token_no_autentica_y_ofrece_reintento(self):
        response = self.client.post(reverse('login'), self.credentials(''))
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.url, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_origen_ajeno_sigue_rechazado(self):
        token = self.token(self.client.get(reverse('login')))
        response = self.client.post(reverse('login'), self.credentials(token), HTTP_ORIGIN='https://otro.example')
        self.assertEqual(response.status_code, 403)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_otros_formularios_siguen_rechazando_csrf_incorrecto(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('perfil'), {'nombre_completo': 'Cambio rechazado'})
        self.assertEqual(response.status_code, 403)

    def test_login_y_recuperacion_no_redirigen_a_sitios_ajenos(self):
        url = reverse('login') + '?next=https://otro.example/'
        response = self.client.post(url, self.credentials(''))
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.url, reverse('login'))
        token = self.token(self.client.get(url))
        response = self.client.post(url, self.credentials(token))
        self.assertRedirects(response, reverse('dashboard'), fetch_redirect_response=False)
