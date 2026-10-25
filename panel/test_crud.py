from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from cuentas.models import Tenant, MembresiaTenant, PerfilCPC
from catalogo.models import UsoIA, ManualContable
from donaciones.models import Donativo
from .models import AccesoPanel, Contacto, Nota, Tarea, Evento

User = get_user_model()


class CrudTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('owner', password='Owner-test-995!')
        self.access = AccesoPanel.objects.create(usuario=self.owner, rol='propietario')
        self.persona = User.objects.create_user('contador', email='contador@example.com')
        self.org = Tenant.objects.create(nombre='Organización de prueba', propietario=self.persona)
        MembresiaTenant.objects.create(tenant=self.org, usuario=self.persona, rol='propietario')
        self.contacto = Contacto.objects.create(nombre='Prospecto', email='prospecto@example.com')
        self.nota = Nota.objects.create(contacto=self.contacto, autor=self.owner, texto='Nota original')
        self.tarea = Tarea.objects.create(contacto=self.contacto, titulo='Seguimiento', vence=timezone.localdate())
        self.donativo = Donativo.objects.create(nombre_donante='Donante manual', monto='50', estado='pendiente')
        self.entrar()

    def entrar(self):
        self.client.force_login(self.owner)
        session = self.client.session; session['panel_2fa'] = self.owner.pk; session.save()

    def url(self, accion, tipo, pk=None):
        return reverse('panel:registro_' + accion, args=[tipo] + ([pk] if pk is not None else []))

    def payload_delete(self, tipo, obj):
        response = self.client.get(self.url('eliminar', tipo, obj.pk))
        self.assertEqual(response.status_code, 200)
        return {'token': response.context['form']['token'].value(), 'confirmacion': f'ELIMINAR #{obj.pk}', 'motivo': 'Solicitud de prueba'}

    def test_acciones_visibles_en_todas_las_listas(self):
        Evento.objects.create(categoria='test', accion='ejemplo')
        UsoIA.objects.create(usuario=self.persona)
        for pagina in ['usuarios', 'organizaciones', 'crm', 'donativos', 'actividad', 'inteligencia']:
            response = self.client.get(reverse('panel:' + pagina))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '<th>Acciones</th>', html=True)
        self.assertContains(self.client.get(reverse('panel:contacto', args=[self.contacto.pk])), self.url('editar', 'nota', self.nota.pk))
        self.assertContains(self.client.get(reverse('panel:contacto', args=[self.contacto.pk])), self.url('eliminar', 'tarea', self.tarea.pk))

    def test_acciones_registradas_sin_descubrimiento_automatico(self):
        from copy import deepcopy
        from unittest.mock import patch
        from django.conf import settings
        from django.template.backends.django import DjangoTemplates
        from django.test import RequestFactory
        config = deepcopy(settings.TEMPLATES[0])
        config.pop('BACKEND')
        config['NAME'] = 'regresion-panel'
        with patch('django.template.backends.django.get_installed_libraries',
                   return_value={'static': 'django.templatetags.static'}):
            backend = DjangoTemplates(config)
            self.assertIn('panel_acciones', backend.engine.template_libraries)
            request = RequestFactory().get('/panel/organizaciones/')
            request.user = self.owner
            html = backend.get_template('panel/organizaciones.html').render(
                {'organizaciones': [self.org], 'titulo': 'Organizaciones'}, request)
        self.assertIn('Editar Organización', html)
        self.assertIn('Eliminar Organización', html)

    def test_crear_usuario_con_password_validado_y_perfil(self):
        data = {'username': 'nuevo', 'email': 'NUEVO@EXAMPLE.COM', 'first_name': 'Ana', 'last_name': 'García',
                'ciudad': 'Mérida', 'estado': 'YUC', 'telefono': '9991234567',
                'password1': 'Unique-password-689!', 'password2': 'Unique-password-689!', 'is_superuser': 'on', 'is_staff': 'on'}
        response = self.client.post(self.url('nuevo', 'usuario'), data)
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='nuevo')
        self.assertTrue(user.check_password(data['password1']))
        self.assertFalse(user.is_superuser); self.assertFalse(user.is_staff)
        self.assertEqual(user.email, 'nuevo@example.com')
        self.assertEqual(user.perfil_cpc.nombre_completo, 'Ana García')
        self.assertFalse(user.perfil_cpc.acepta_terminos)
        self.assertFalse(AccesoPanel.objects.filter(usuario=user).exists())

    def test_usuario_rechaza_correo_y_nombre_duplicados(self):
        response = self.client.post(self.url('editar', 'usuario', self.persona.pk), {
            'username': 'OWNER', 'email': self.persona.email, 'first_name': 'Nombre'})
        self.assertContains(response, 'Ya existe un usuario con este nombre')
        self.persona.refresh_from_db(); self.assertEqual(self.persona.username, 'contador')

    def test_editar_usuario_no_cambia_privilegios_password_o_estado(self):
        old = self.persona.password
        response = self.client.post(self.url('editar', 'usuario', self.persona.pk), {
            'username': 'contador', 'email': 'cambiado@example.com', 'first_name': 'Carlos',
            'is_superuser': 'on', 'is_staff': 'on', 'password': 'injected'})
        self.assertEqual(response.status_code, 302)
        self.persona.refresh_from_db()
        self.assertEqual(self.persona.email, 'cambiado@example.com')
        self.assertEqual(self.persona.password, old)
        self.assertTrue(self.persona.is_active); self.assertFalse(self.persona.is_superuser)

    def test_cuentas_administrativas_protegidas(self):
        for user in [self.owner, User.objects.create_user('staff', is_staff=True), User.objects.create_superuser('super', password='test')]:
            for accion in ['editar', 'eliminar']:
                self.assertEqual(self.client.get(self.url(accion, 'usuario', user.pk)).status_code, 403)
                self.assertEqual(self.client.post(self.url(accion, 'usuario', user.pk), {}).status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.owner.pk).exists())

    def test_crear_y_editar_organizacion_asegura_membresias(self):
        response = self.client.post(self.url('nuevo', 'organizacion'), {'nombre': 'Nueva empresa', 'propietario': self.persona.pk,
                                      'giro': 'servicios', 'regimen_fiscal': 'pm_general'})
        self.assertEqual(response.status_code, 302)
        org = Tenant.objects.get(nombre='Nueva empresa')
        self.assertTrue(MembresiaTenant.objects.filter(tenant=org, usuario=self.persona, rol='propietario').exists())
        otro = User.objects.create_user('nuevo_propietario')
        response = self.client.post(self.url('editar', 'organizacion', org.pk), {'nombre': 'Empresa actualizada', 'propietario': otro.pk,
                                      'giro': 'comercial', 'regimen_fiscal': 'pm_general'})
        self.assertEqual(response.status_code, 302)
        org.refresh_from_db(); self.assertEqual(org.propietario, otro)
        self.assertEqual(MembresiaTenant.objects.get(tenant=org, usuario=self.persona).rol, 'contador')
        self.assertEqual(MembresiaTenant.objects.get(tenant=org, usuario=otro).rol, 'propietario')

    def test_editar_nota_y_tarea_conserva_contacto(self):
        otro = Contacto.objects.create(nombre='Otro', email='otro@example.com')
        response = self.client.post(self.url('editar', 'nota', self.nota.pk), {'texto': 'Nota actualizada', 'contacto': otro.pk})
        self.assertEqual(response.status_code, 302)
        self.nota.refresh_from_db(); self.assertEqual(self.nota.texto, 'Nota actualizada'); self.assertEqual(self.nota.contacto, self.contacto)
        response = self.client.post(self.url('editar', 'tarea', self.tarea.pk), {'titulo': 'Llamar mañana', 'vence': '2026-11-02', 'completada': 'on', 'responsable': self.owner.pk})
        self.assertEqual(response.status_code, 302)
        self.tarea.refresh_from_db(); self.assertTrue(self.tarea.completada)
        self.assertEqual(self.tarea.contacto, self.contacto)
        self.assertEqual(self.client.get(self.url('nuevo', 'nota')).status_code, 404)

    def test_crud_contacto_elimina_solo_relaciones_crm(self):
        self.contacto.usuario = self.persona; self.contacto.save()
        preview = self.client.get(self.url('eliminar', 'contacto', self.contacto.pk))
        self.assertContains(preview, 'panel.nota')
        self.assertTrue(Contacto.objects.filter(pk=self.contacto.pk).exists())
        response = self.client.post(self.url('eliminar', 'contacto', self.contacto.pk), self.payload_delete('contacto', self.contacto))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Contacto.objects.filter(pk=self.contacto.pk).exists())
        self.assertFalse(Nota.objects.filter(pk=self.nota.pk).exists())
        self.assertFalse(Tarea.objects.filter(pk=self.tarea.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.persona.pk).exists())
        self.assertTrue(Tenant.objects.filter(pk=self.org.pk).exists())
        self.assertTrue(Evento.objects.filter(accion='contacto.eliminado', actor=self.owner).exists())

    def test_eliminar_usuario_muestra_cascada_y_conserva_auditoria(self):
        Evento.objects.create(actor=self.persona, categoria='test', accion='conservar')
        response = self.client.get(self.url('eliminar', 'usuario', self.persona.pk))
        self.assertContains(response, 'cuentas.tenant')
        self.assertTrue(User.objects.filter(pk=self.persona.pk).exists())
        response = self.client.post(self.url('eliminar', 'usuario', self.persona.pk), self.payload_delete('usuario', self.persona))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=self.persona.pk).exists())
        self.assertFalse(Tenant.objects.filter(pk=self.org.pk).exists())
        self.assertIsNone(Evento.objects.get(accion='conservar').actor)

    def test_confirmacion_firma_y_motivo_obligatorios(self):
        data = self.payload_delete('nota', self.nota)
        for changed in [{'token': 'invalid'}, {'motivo': ''}, {'confirmacion': 'sí'}]:
            response = self.client.post(self.url('eliminar', 'nota', self.nota.pk), data | changed)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(Nota.objects.filter(pk=self.nota.pk).exists())
        self.assertEqual(self.client.post(self.url('eliminar', 'nota', self.nota.pk), data).status_code, 302)
        self.assertFalse(Nota.objects.filter(pk=self.nota.pk).exists())

    def test_confirmacion_no_se_reutiliza_para_otro_registro(self):
        data = self.payload_delete('nota', self.nota)
        otra = Nota.objects.create(contacto=self.contacto, texto='Otra')
        data['confirmacion'] = f'ELIMINAR #{otra.pk}'
        self.client.post(self.url('eliminar', 'nota', otra.pk), data)
        self.assertTrue(Nota.objects.filter(pk=otra.pk).exists())

    def test_cambios_en_cascada_exigen_reconfirmacion(self):
        data = self.payload_delete('contacto', self.contacto)
        Nota.objects.create(contacto=self.contacto, texto='Nueva dependencia')
        response = self.client.post(self.url('eliminar', 'contacto', self.contacto.pk), data)
        self.assertContains(response, 'cambiaron los registros afectados')
        self.assertTrue(Contacto.objects.filter(pk=self.contacto.pk).exists())

    def test_donativos_manuales_crear_editar_eliminar(self):
        response = self.client.post(self.url('nuevo', 'donativo'), {'nombre_donante': 'Manual', 'monto': '75.50', 'estado': 'aprobado'})
        self.assertEqual(response.status_code, 302)
        obj = Donativo.objects.get(nombre_donante='Manual')
        self.assertIsNone(obj.preference_id); self.assertIsNone(obj.referencia_mp)
        response = self.client.post(self.url('editar', 'donativo', obj.pk), {'nombre_donante': 'Manual editado', 'monto': '80', 'estado': 'aprobado'})
        self.assertEqual(response.status_code, 302)
        obj.refresh_from_db(); self.assertEqual(obj.monto, 80)
        self.client.post(self.url('eliminar', 'donativo', obj.pk), self.payload_delete('donativo', obj))
        self.assertFalse(Donativo.objects.filter(pk=obj.pk).exists())

    def test_checkout_fallido_externo_no_se_edita_ni_elimina(self):
        from uuid import uuid4
        externo = Donativo.objects.create(monto=100, checkout_clave=uuid4(), estado='error_checkout')
        for accion in ['editar', 'eliminar']:
            self.assertEqual(self.client.post(self.url(accion, 'donativo', externo.pk), {}).status_code, 403)
        self.assertTrue(Donativo.objects.filter(pk=externo.pk).exists())

    def test_totales_usen_neto_y_conserven_historicos(self):
        Donativo.objects.create(monto=100, estado='parcial', monto_confirmado=70, monto_reembolsado=30)
        Donativo.objects.create(monto=50, estado='aprobado')
        Donativo.objects.create(monto=100, estado='reembolsado', monto_confirmado=0)
        response = self.client.get(reverse('panel:donativos'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 120)

    def test_pago_externo_y_registros_operativos_no_se_mutan(self):
        externo = Donativo.objects.create(monto=100, preference_id='mp-test', estado='aprobado')
        evento = Evento.objects.create(categoria='test', accion='inmutable')
        consumo = UsoIA.objects.create(usuario=self.persona)
        for tipo, obj in [('donativo', externo), ('evento', evento), ('consumo', consumo)]:
            self.assertEqual(self.client.get(self.url('ver', tipo, obj.pk)).status_code, 200)
            for accion in ['editar', 'eliminar']:
                self.assertEqual(self.client.get(self.url(accion, tipo, obj.pk)).status_code, 403)
                self.assertEqual(self.client.post(self.url(accion, tipo, obj.pk), {}).status_code, 403)
        self.assertEqual(self.client.post(self.url('nuevo', 'evento'), {}).status_code, 403)

    def test_roles_de_consulta_y_soporte_no_mutan(self):
        for rol in ['consulta', 'soporte']:
            self.access.rol = rol; self.access.save()
            for tipo, obj in [('usuario', self.persona), ('organizacion', self.org), ('contacto', self.contacto), ('nota', self.nota), ('tarea', self.tarea), ('donativo', self.donativo)]:
                for accion in ['editar', 'eliminar']:
                    self.assertEqual(self.client.post(self.url(accion, tipo, obj.pk), {}).status_code, 403)
            self.assertNotContains(self.client.get(reverse('panel:usuarios')), 'Eliminar Usuario')

    def test_comercial_solo_muta_crm(self):
        self.access.rol = 'comercial'; self.access.save()
        self.assertEqual(self.client.get(self.url('editar', 'nota', self.nota.pk)).status_code, 200)
        self.assertEqual(self.client.get(self.url('eliminar', 'contacto', self.contacto.pk)).status_code, 200)
        for tipo, obj in [('usuario', self.persona), ('organizacion', self.org), ('donativo', self.donativo)]:
            self.assertEqual(self.client.get(self.url('editar', tipo, obj.pk)).status_code, 403)

    def test_csrf_y_2fa_siguen_obligatorios(self):
        session = self.client.session; session.pop('panel_2fa'); session.save()
        self.assertRedirects(self.client.post(self.url('editar', 'nota', self.nota.pk), {'texto': 'no'}), reverse('panel:verificar'), fetch_redirect_response=False)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        session = client.session; session['panel_2fa'] = self.owner.pk; session.save()
        self.assertEqual(client.post(self.url('eliminar', 'nota', self.nota.pk), {}).status_code, 403)

    def test_detalles_y_formularios_renderizan(self):
        for tipo, obj in [('organizacion', self.org), ('nota', self.nota), ('tarea', self.tarea), ('donativo', self.donativo)]:
            for accion in ['ver', 'editar', 'eliminar']:
                self.assertEqual(self.client.get(self.url(accion, tipo, obj.pk)).status_code, 200)
        for tipo in ['usuario', 'organizacion', 'contacto', 'donativo']:
            self.assertEqual(self.client.get(self.url('nuevo', tipo)).status_code, 200)
        self.assertEqual(self.client.get(self.url('nuevo', 'desconocido')).status_code, 404)
