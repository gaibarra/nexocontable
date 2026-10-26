from types import SimpleNamespace
from unittest.mock import patch

import httpx
from django.test import SimpleTestCase, override_settings
from openai import APIStatusError

from .ia import generar_texto, ManualGenerationError


def respuesta(content='Manual', finish_reason='stop'):
    return SimpleNamespace(choices=[SimpleNamespace(
        message=SimpleNamespace(content=content), finish_reason=finish_reason)], usage=None)


@override_settings(AI_PROVIDER='deepseek', AI_FALLBACK_PROVIDER='',
                   DEEPSEEK_API_KEY='deepseek-test', OPENAI_API_KEY='',
                   DEEPSEEK_MODEL='deepseek-flash', DEEPSEEK_MAX_TOKENS=4000)
class ProveedorIATests(SimpleTestCase):
    @patch('catalogo.ia.OpenAI')
    def test_deepseek_works_without_openai_key(self, factory):
        client = factory.return_value.__enter__.return_value
        client.chat.completions.create.return_value = respuesta()
        self.assertEqual(generar_texto('Sistema', 'Cuentas'), 'Manual')
        self.assertEqual(factory.call_args.kwargs['api_key'], 'deepseek-test')
        self.assertEqual(factory.call_args.kwargs['base_url'], 'https://api.deepseek.com')
        self.assertEqual(client.chat.completions.create.call_args.kwargs['model'], 'deepseek-flash')
        self.assertEqual(client.chat.completions.create.call_args.kwargs['extra_body'],
                         {'thinking': {'type': 'disabled'}})

    @override_settings(AI_PROVIDER='openai', AI_FALLBACK_PROVIDER='deepseek', OPENAI_API_KEY='openai-test')
    @patch('catalogo.ia.OpenAI')
    def test_fallback_on_primary_failure(self, factory):
        client = factory.return_value.__enter__.return_value
        error = APIStatusError('test', response=httpx.Response(402,
            request=httpx.Request('POST', 'https://api.openai.com/v1/chat/completions')), body={})
        client.chat.completions.create.side_effect = [error, respuesta()]
        self.assertEqual(generar_texto('Sistema', 'Cuentas'), 'Manual')
        self.assertEqual([c.kwargs['api_key'] for c in factory.call_args_list],
                         ['openai-test', 'deepseek-test'])

    @override_settings(AI_FALLBACK_PROVIDER='openai', OPENAI_API_KEY='openai-test')
    @patch('catalogo.ia.OpenAI')
    def test_success_does_not_call_fallback(self, factory):
        factory.return_value.__enter__.return_value.chat.completions.create.return_value = respuesta()
        generar_texto('Sistema', 'Cuentas')
        factory.assert_called_once()

    @patch('catalogo.ia.OpenAI')
    def test_incomplete_or_empty_content_is_not_saved(self, factory):
        for content, reason in [('', 'stop'), ('partial', 'length'), (None, 'stop')]:
            with self.subTest(content=content, reason=reason):
                factory.return_value.__enter__.return_value.chat.completions.create.return_value = respuesta(content, reason)
                with self.assertRaises(ManualGenerationError):
                    generar_texto('Sistema', 'Cuentas')

    @override_settings(DEEPSEEK_API_KEY='')
    @patch('catalogo.ia.OpenAI')
    def test_missing_credentials_do_not_make_requests(self, factory):
        with self.assertRaises(ManualGenerationError):
            generar_texto('Sistema', 'Cuentas')
        factory.assert_not_called()

    @override_settings(AI_PROVIDER='invalid')
    @patch('catalogo.ia.OpenAI')
    def test_unknown_provider_fails_safely(self, factory):
        with self.assertRaises(ManualGenerationError):
            generar_texto('Sistema', 'Cuentas')
        factory.assert_not_called()

    @patch('catalogo.ia.OpenAI')
    def test_balance_error_does_not_expose_provider(self, factory):
        factory.side_effect = APIStatusError('secret server details', response=httpx.Response(402,
            request=httpx.Request('POST', 'https://api.deepseek.com/chat/completions')), body={})
        with self.assertRaises(ManualGenerationError) as caught:
            generar_texto('Sistema', 'Cuentas')
        self.assertIn('recargar el saldo', str(caught.exception))
        self.assertNotIn('DeepSeek', str(caught.exception))
        self.assertNotIn('secret', str(caught.exception))

    @override_settings(AI_PROVIDER='openai', OPENAI_API_KEY='openai-test')
    @patch('catalogo.ia.OpenAI')
    def test_opcion_deepseek_no_se_envia_a_openai(self, factory):
        client = factory.return_value.__enter__.return_value
        client.chat.completions.create.return_value = respuesta()
        generar_texto('Sistema', 'Cuentas')
        self.assertNotIn('extra_body', client.chat.completions.create.call_args.kwargs)

    @patch('catalogo.ia.OpenAI')
    def test_limite_de_salida_tiene_mensaje_accionable_y_log_sin_contenido(self, factory):
        client = factory.return_value.__enter__.return_value
        client.chat.completions.create.return_value = respuesta('contenido privado', 'length')
        with self.assertLogs('catalogo.ia', level='WARNING') as logs:
            with self.assertRaisesRegex(ManualGenerationError, 'No se guardó un documento parcial'):
                generar_texto('Sistema privado', 'Cuentas privadas')
        self.assertIn('motivo=length', ' '.join(logs.output))
        self.assertNotIn('contenido privado', ' '.join(logs.output))
        self.assertNotIn('Cuentas privadas', ' '.join(logs.output))

    @patch('catalogo.ia.OpenAI')
    def test_respuesta_vacia_informa_motivo(self, factory):
        factory.return_value.__enter__.return_value.chat.completions.create.return_value = respuesta(None)
        with self.assertRaisesRegex(ManualGenerationError, 'respuesta vacía o incompleta'):
            generar_texto('Sistema', 'Cuentas')

    @override_settings(AI_FALLBACK_PROVIDER='openai', OPENAI_API_KEY='openai-test')
    @patch('catalogo.ia.OpenAI')
    def test_respaldo_se_usa_si_respuesta_principal_es_incompleta(self, factory):
        client = factory.return_value.__enter__.return_value
        client.chat.completions.create.side_effect = [respuesta('incompleto', 'length'), respuesta('Manual completo')]
        self.assertEqual(generar_texto('Sistema', 'Cuentas'), 'Manual completo')
        self.assertEqual(client.chat.completions.create.call_count, 2)


class ContextoPersonalizacionTests(SimpleTestCase):
    def test_misma_cuenta_recibe_el_contexto_de_cada_organizacion(self):
        from cuentas.models import Tenant
        from .prompts import build_manual_prompts
        cuenta = SimpleNamespace(cuenta='101', descripcion='Caja',
            codigoagrupador=SimpleNamespace(codigoagrupador='101', nombre='Caja'))
        restaurante = Tenant(nombre='Restaurante de prueba', giro='restaurantes', regimen_fiscal='pm_general')
        asociacion = Tenant(nombre='Asociación de prueba', giro='ong', regimen_fiscal='pm_sin_fines')
        for org, ajena in [(restaurante, asociacion), (asociacion, restaurante)]:
            with self.subTest(giro=org.giro):
                sistema, solicitud = build_manual_prompts([cuenta], org)
                self.assertIn(org.get_giro_display(), sistema)
                self.assertIn(org.get_regimen_fiscal_display(), sistema)
                self.assertIn(org.nombre, solicitud)
                self.assertIn(org.get_giro_display(), solicitud)
                self.assertIn(org.get_regimen_fiscal_display(), solicitud)
                self.assertNotIn(ajena.nombre, solicitud)
                self.assertIn('casos hipotéticos', solicitud)
                self.assertIn('hechos no proporcionados', solicitud)
