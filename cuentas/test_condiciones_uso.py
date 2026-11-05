from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class CondicionesUsoTests(TestCase):
    def test_publicacion_accesible_sin_sesion_y_con_version(self):
        response = self.client.get(reverse('condiciones_uso'))
        self.assertContains(response, 'Versión 2026-10-29')
        self.assertContains(response, 'incluidos servicios remunerados')
        self.assertContains(response, 'No atribuye aceptación retroactiva')
        self.assertContains(response, 'proyectog40@gmail.com')
        self.assertContains(response, reverse('aviso_privacidad'))

    def test_usuario_sin_organizacion_puede_consultar_sin_mutacion(self):
        user = get_user_model().objects.create_user(username='consulta-condiciones')
        self.client.force_login(user)
        session_before = dict(self.client.session)
        self.assertEqual(self.client.get(reverse('condiciones_uso')).status_code, 200)
        self.assertEqual(dict(self.client.session), session_before)
        self.assertNotIn('tenant_id', self.client.session)

    def test_enlaces_publicos_y_pagina_tecnica(self):
        for route in ('landing', 'uso_seguridad', 'registro'):
            with self.subTest(route=route):
                self.assertContains(self.client.get(reverse(route)), reverse('condiciones_uso'))
