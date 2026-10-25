from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, SimpleTestCase, override_settings
from django.urls import reverse

from cuentas.models import Tenant
from .consumo_ia import registrar_uso, resumen_uso
from .ia import generar_texto, ManualGenerationError, TextoGenerado
from .models import ManualContable, UsoIA
from . import tests as catalogo_tests


def respuesta(entrada=100, salida=50, total=150, contenido='Manual de prueba', motivo='stop'):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=contenido), finish_reason=motivo)],
        usage=SimpleNamespace(prompt_tokens=entrada, completion_tokens=salida, total_tokens=total),
    )


@override_settings(AI_PROVIDER='deepseek', AI_FALLBACK_PROVIDER='', DEEPSEEK_API_KEY='test',
                   DEEPSEEK_MODEL='deepseek-test', DEEPSEEK_MAX_TOKENS=4000)
class MedicionIATests(SimpleTestCase):
    @patch('catalogo.ia.OpenAI')
    def test_conserva_texto_y_medicion_real(self, factory):
        factory.return_value.__enter__.return_value.chat.completions.create.return_value = respuesta()
        texto = generar_texto('sistema', 'cuentas')
        self.assertEqual(texto, 'Manual de prueba')
        self.assertEqual(texto.consumos[0]['entrada'], 100)
        self.assertEqual(texto.consumos[0]['salida'], 50)
        self.assertEqual(texto.consumos[0]['total'], 150)

    @override_settings(AI_FALLBACK_PROVIDER='openai', OPENAI_API_KEY='test')
    @patch('catalogo.ia.OpenAI')
    def test_respaldo_conserva_consumo_del_intento_incompleto(self, factory):
        factory.return_value.__enter__.return_value.chat.completions.create.side_effect = [
            respuesta(total=150, motivo='length'), respuesta(200, 100, 300)]
        texto = generar_texto('sistema', 'cuentas')
        self.assertEqual([i['total'] for i in texto.consumos], [150, 300])
        self.assertEqual([i['resultado'] for i in texto.consumos], ['incompleto', 'completo'])

    @patch('catalogo.ia.OpenAI')
    def test_fallo_conserva_consumo_y_no_lo_presenta_como_manual(self, factory):
        factory.return_value.__enter__.return_value.chat.completions.create.return_value = respuesta(motivo='length')
        with self.assertRaises(ManualGenerationError) as error:
            generar_texto('sistema', 'cuentas')
        self.assertEqual(error.exception.consumos[0]['total'], 150)

    @patch('catalogo.ia.OpenAI')
    def test_uso_no_informado_no_se_convierte_en_cero(self, factory):
        factory.return_value.__enter__.return_value.chat.completions.create.return_value = respuesta(None, None, None)
        self.assertIsNone(generar_texto('sistema', 'cuentas').consumos[0]['total'])

    @patch('catalogo.ia.OpenAI')
    def test_suma_desglose_cuando_falta_total(self, factory):
        factory.return_value.__enter__.return_value.chat.completions.create.return_value = respuesta(100, 50, None)
        self.assertEqual(generar_texto('sistema', 'cuentas').consumos[0]['total'], 150)


@override_settings(DEBUG=True, SECURE_SSL_REDIRECT=False, AI_PROVIDER='deepseek',
                   AI_FALLBACK_PROVIDER='', DEEPSEEK_API_KEY='test', DEEPSEEK_MODEL='deepseek-test',
                   DEEPSEEK_MAX_TOKENS=4000)
class ReporteConsumoTests(TestCase):
    setUp = catalogo_tests.CatalogoCuentaDeleteTests.setUp

    def generar(self, response=None):
        with patch('catalogo.ia.OpenAI') as factory:
            factory.return_value.__enter__.return_value.chat.completions.create.return_value = response or respuesta()
            return self.client.post(reverse('generar_manual'), {'cuentas': [self.cuenta.pk]}, follow=True)

    def registro(self, **kwargs):
        tenant = kwargs.pop('tenant', self.tenant)
        return UsoIA.objects.create(usuario=kwargs.pop('usuario', self.user),
                                    tenant=tenant, organizacion_referencia=tenant.pk, **kwargs)

    def test_finalizar_muestra_reporte_y_persiste_consumo(self):
        response = self.generar()
        self.assertEqual(response.status_code, 200)
        registro = UsoIA.objects.get()
        self.assertEqual(registro.tokens_total, 150)
        self.assertEqual(registro.tokens_entrada, 100)
        self.assertEqual(registro.tokens_salida, 50)
        self.assertTrue(registro.manual_generado)
        self.assertEqual(registro.manual, ManualContable.objects.get())
        self.assertEqual(response.context['resumen_ia']['manuales'], 1)
        self.assertEqual(response.context['resumen_ia']['tokens'], 150)
        self.assertContains(response, 'Tu manual está listo para revisar')
        self.assertContains(response, 'no representa un cobro')
        self.assertContains(response, 'Los <strong>tokens</strong>')
        self.assertNotContains(response, 'deepseek-test')
        detalle = self.client.get(reverse('detalle_manual', args=[registro.manual_id]))
        self.assertContains(detalle, 'Consumo de esta generación')
        export = self.client.get(reverse('exportar_manual', args=[registro.manual_id]))
        from io import BytesIO
        from zipfile import ZipFile
        with ZipFile(BytesIO(export.content)) as archivo:
            self.assertNotIn('Tokens registrados', archivo.read('word/document.xml').decode())

    def test_acumula_entre_empresas_solo_para_el_usuario_actual(self):
        otra = Tenant.objects.create(nombre='Segunda empresa', propietario=self.user)
        colega = User.objects.create_user(username='colega')
        self.registro(tokens_total=150, manual_generado=True)
        self.registro(tenant=otra, tokens_total=250, manual_generado=True)
        self.registro(usuario=colega, tokens_total=99999, manual_generado=True)
        resumen = resumen_uso(self.user)
        self.assertEqual(resumen['tokens'], 400)
        self.assertEqual(resumen['manuales'], 2)
        self.assertEqual(resumen['organizaciones'], 2)
        self.assertEqual(self.client.get(reverse('dashboard')).context['resumen_ia']['tokens'], 400)

    def test_historial_se_conserva_al_eliminar_manual_y_empresa(self):
        self.generar()
        ManualContable.objects.get().delete()
        registro = UsoIA.objects.get()
        self.assertIsNone(registro.manual_id)
        self.assertEqual(resumen_uso(self.user)['tokens'], 150)
        self.assertEqual(resumen_uso(self.user)['manuales'], 1)
        self.tenant.delete()
        registro.refresh_from_db()
        self.assertIsNone(registro.tenant_id)
        self.assertEqual(resumen_uso(self.user)['organizaciones'], 1)
        self.assertEqual(resumen_uso(self.user)['tokens'], 150)

    def test_reutilizar_manual_no_genera_consumo_adicional(self):
        self.generar()
        with patch('catalogo.ia.OpenAI') as factory:
            self.client.post(reverse('generar_manual'), {'cuentas': [self.cuenta.pk]})
            factory.assert_not_called()
        self.assertEqual(UsoIA.objects.count(), 1)
        self.assertEqual(resumen_uso(self.user)['tokens'], 150)

    def test_incompleto_se_registra_sin_contar_un_manual(self):
        self.generar(respuesta(motivo='length'))
        self.assertFalse(ManualContable.objects.exists())
        self.assertEqual(UsoIA.objects.get().tokens_total, 150)
        self.assertFalse(UsoIA.objects.get().manual_generado)
        self.assertEqual(resumen_uso(self.user)['manuales'], 0)

    def test_consumo_ausente_muestra_no_disponible_sin_inventar(self):
        response = self.generar(respuesta(None, None, None))
        self.assertIsNone(UsoIA.objects.get().tokens_total)
        self.assertTrue(UsoIA.objects.get().total_parcial)
        self.assertContains(response, 'No disponible')
        self.assertContains(response, 'consumo no informado o parcial')

    def test_suma_respaldo_y_senala_si_hay_consumo_desconocido(self):
        texto = TextoGenerado('Manual', [
            {'entrada': None, 'salida': None, 'total': None, 'resultado': 'error'},
            {'entrada': 100, 'salida': 50, 'total': 150, 'resultado': 'completo'}])
        registro = registrar_uso(texto, self.user, self.tenant)
        self.assertEqual(registro.tokens_total, 150)
        self.assertTrue(registro.total_parcial)
        self.assertEqual(resumen_uso(self.user)['sin_dato'], 1)

    def test_otro_usuario_o_empresa_no_puede_abrir_reporte(self):
        self.generar()
        registro = UsoIA.objects.get()
        otra = Tenant.objects.create(nombre='Empresa privada', propietario=self.user)
        ajeno = self.registro(tenant=otra, tokens_total=999999, manual_generado=True)
        response = self.client.get(reverse('generar_manual'), {'reporte': ajeno.pk})
        self.assertIsNone(response.context['reporte_ia'])
        colega = User.objects.create_user(username='otro')
        registro.usuario = colega
        registro.save()
        response = self.client.get(reverse('generar_manual'), {'reporte': registro.pk})
        self.assertIsNone(response.context['reporte_ia'])

    def test_historico_no_se_reconstruye_con_estimaciones(self):
        ManualContable.objects.create(tenant=self.tenant, titulo='Manual anterior', contenido='Anterior', creado_por=self.user)
        self.assertEqual(resumen_uso(self.user)['registros'], 0)
        self.assertIsNone(resumen_uso(self.user)['tokens'])
        for parametro in ['abc', '9' * 100]:
            response = self.client.get(reverse('generar_manual'), {'reporte': parametro})
            self.assertEqual(response.status_code, 200)
            self.assertIsNone(response.context['reporte_ia'])

    def test_envio_simultaneo_registra_consumo_sin_duplicar_manual_preparado(self):
        def otro_envio(*args):
            manual = ManualContable.objects.create(
                tenant=self.tenant, titulo='Manual existente', contenido='Otro documento', creado_por=self.user)
            manual.cuentas.set([self.cuenta])
            return TextoGenerado('Otro borrador', [
                {'entrada': 100, 'salida': 50, 'total': 150, 'resultado': 'completo'}])
        with patch('catalogo.views.generar_contenido_manual', side_effect=otro_envio):
            self.client.post(reverse('generar_manual'), {'cuentas': [self.cuenta.pk]})
        self.assertEqual(ManualContable.objects.count(), 1)
        self.assertEqual(UsoIA.objects.get().manual, ManualContable.objects.get())
        self.assertFalse(UsoIA.objects.get().manual_generado)
        self.assertEqual(resumen_uso(self.user)['tokens'], 150)
        self.assertEqual(resumen_uso(self.user)['manuales'], 0)
