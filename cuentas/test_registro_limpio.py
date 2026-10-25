from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from .forms import RegistroUsuarioForm


@override_settings(DEBUG=True, SECURE_SSL_REDIRECT=False)
class RegistroLimpioTests(TestCase):
    def test_registro_nuevo_vacio_y_sin_selecciones_automaticas(self):
        User.objects.create_user(username='cuenta-anterior', email='anterior@example.com')
        response = self.client.get(reverse('registro'))
        form = response.context['form']
        self.assertFalse(form.is_bound)
        for nombre in ['email', 'nombre_completo', 'ciudad', 'telefono', 'password', 'password_confirm']:
            self.assertIsNone(form[nombre].value())
        for nombre in ['especialidad', 'estado']:
            self.assertEqual(list(form.fields[nombre].choices)[0][0], '')
        self.assertContains(response, 'data-registration-fresh="true"')
        self.assertNotContains(response, 'anterior@example.com')
        self.assertIn('no-store', response['Cache-Control'])
        self.assertTrue(User.objects.filter(username='cuenta-anterior').exists())

    def test_contrasenas_nuevas_y_datos_personales_sin_autocompletado(self):
        form = RegistroUsuarioForm()
        for nombre in ['password', 'password_confirm']:
            self.assertEqual(form.fields[nombre].widget.attrs['autocomplete'], 'new-password')
        self.assertEqual(form.fields['email'].widget.attrs['autocomplete'], 'off')

    def test_error_conserva_datos_para_corregir_pero_get_nuevo_los_limpia(self):
        datos = {'email': 'nuevo@example.com', 'password': 'Password#2026', 'password_confirm': 'Distinta#2026',
                 'nombre_completo': 'Contador de Prueba', 'ciudad': 'Mexicali', 'estado': 'BC',
                 'especialidad': 'fiscal', 'acepta_terminos': 'on'}
        response = self.client.post(reverse('registro'), datos)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-registration-fresh="false"')
        self.assertEqual(response.context['form']['email'].value(), datos['email'])
        self.assertEqual(response.context['form']['estado'].value(), 'BC')
        self.assertNotContains(response, datos['password'])
        response = self.client.get(reverse('registro'))
        self.assertIsNone(response.context['form']['email'].value())
        self.assertFalse(User.objects.filter(email=datos['email']).exists())

    def test_registro_caducado_regresa_a_formulario_nuevo_sin_crear_cuenta(self):
        from django.test import Client
        from django.middleware.csrf import _get_new_csrf_string
        client = Client(enforce_csrf_checks=True)
        client.get(reverse('registro'))
        anterior = client.cookies['csrftoken'].value
        client.cookies['csrftoken'] = _get_new_csrf_string()
        response = client.post(reverse('registro'), {'email': 'caducado@example.com', 'csrfmiddlewaretoken': anterior})
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response['Location'], reverse('registro'))
        self.assertFalse(User.objects.filter(email='caducado@example.com').exists())
