from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .forms import RegistroUsuarioForm
from .models import ConstanciaPrivacidad
from .privacidad import VERSION_AVISO, huella_aviso

User = get_user_model()


class PrivacidadTests(TestCase):
    def datos(self):
        return {'email': 'privacidad-prueba@example.com', 'password': 'Password-prueba-996!',
                'password_confirm': 'Password-prueba-996!', 'nombre_completo': 'Persona de Prueba',
                'especialidad': 'contabilidad_general', 'ciudad': 'Mérida', 'estado': 'YUC',
                'acepta_terminos': 'on', 'version_aviso': VERSION_AVISO}

    def test_aviso_publico_con_identidad_domicilio_y_contacto(self):
        response = self.client.get(reverse('aviso_privacidad'))
        self.assertEqual(response.status_code, 200)
        for text in ['Gonzalo Arturo Ibarra Mendoza', 'Pedregales de Tanlum', '97210',
                     'proyectog40@gmail.com', '20 días hábiles', '15 días hábiles',
                     'Secretaría Anticorrupción y Buen Gobierno', 'DeepSeek', 'OpenAI', 'Mercado Pago']:
            self.assertContains(response, text)
        self.assertNotContains(response, 'Instituto Nacional de Transparencia')
        self.assertNotContains(response, 'soporte@manualcontable.online')

    def test_aviso_disponible_para_usuario_sin_organizacion(self):
        user = User.objects.create_user(username='sin-tenant')
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('aviso_privacidad')).status_code, 200)

    def test_enlaces_y_resumen_antes_del_consentimiento(self):
        for route in ['landing', 'login', 'registro', 'password_reset', 'donar']:
            response = self.client.get(reverse(route))
            self.assertContains(response, reverse('aviso_privacidad'))
        response = self.client.get(reverse('registro'))
        self.assertContains(response, 'Aviso de privacidad simplificado')
        self.assertContains(response, 'proyectog40@gmail.com')
        self.assertFalse(response.context['form']['acepta_terminos'].value())
        self.assertEqual(response.context['form']['version_aviso'].value(), VERSION_AVISO)

    def test_registro_sin_consentimiento_no_crea_cuenta(self):
        datos = self.datos(); datos.pop('acepta_terminos')
        response = self.client.post(reverse('registro'), datos)
        self.assertEqual(response.status_code, 200)
        self.assertIn('acepta_terminos', response.context['form'].errors)
        self.assertFalse(User.objects.filter(email=datos['email']).exists())
        self.assertFalse(ConstanciaPrivacidad.objects.exists())

    def test_version_caducada_o_ausente_requiere_revisar_aviso(self):
        for version in ['', '2025-01-01']:
            with self.subTest(version=version):
                datos = self.datos(); datos['version_aviso'] = version
                response = self.client.post(reverse('registro'), datos)
                self.assertEqual(response.status_code, 200)
                self.assertIn('version_aviso', response.context['form'].errors)
                self.assertFalse(User.objects.filter(email=datos['email']).exists())

    def test_registro_guarda_constancia_versionada_sin_datos_tecnicos_extra(self):
        response = self.client.post(reverse('registro'), self.datos())
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email=self.datos()['email'])
        constancia = ConstanciaPrivacidad.objects.get(usuario=user)
        self.assertEqual(constancia.version, VERSION_AVISO)
        self.assertEqual(constancia.contenido_hash, huella_aviso())
        self.assertEqual(len(constancia.contenido_hash), 64)
        self.assertEqual(constancia.canal, 'registro')
        self.assertIsNotNone(constancia.fecha)

    def test_usuarios_anteriores_no_reciben_consentimiento_retroactivo(self):
        User.objects.create_user(username='existente', email='existente@example.com')
        self.client.get(reverse('aviso_privacidad'))
        self.assertFalse(ConstanciaPrivacidad.objects.exists())

    def test_constancia_y_usuario_se_revierten_si_falla_registro(self):
        with patch('cuentas.views.login', side_effect=RuntimeError('Fallo de prueba')):
            with self.assertRaises(RuntimeError):
                self.client.post(reverse('registro'), self.datos())
        self.assertFalse(User.objects.filter(email=self.datos()['email']).exists())
        self.assertFalse(ConstanciaPrivacidad.objects.exists())

    def test_consentimiento_no_autoriza_publicidad_indiscriminada(self):
        response = self.client.get(reverse('aviso_privacidad'))
        self.assertContains(response, 'se informará y solicitará una decisión separada')
        self.assertContains(response, 'opción de aceptar o rechazar')
        self.assertContains(response, 'No vendemos tus datos')
