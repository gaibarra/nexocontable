import copy
import io
import json
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from bs4 import BeautifulSoup
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from docx import Document
from cuentas.models import Tenant, MembresiaTenant
from panel.models import AccesoPanel
from .models import (FuenteNormativa, VersionFuente, CriterioRevisado, ControlBiblioteca, AlertaFuente,
                     ManualContable, CodigoAgrupador, CatalogoCuentas, RevisionFundamentos)
from .biblioteca import seleccionar, validar_respuesta, pendientes_manual, huella, anexo, familia_cuenta
from .ia import TextoGenerado, ManualGenerationError
from .management.commands.comprobar_fuentes import obtener

EVIDENCIAS=str(Path(__file__).parent/'data'/'fundamentos_2026_10_29')


def respuesta(snapshot):
    data={}
    for area in ('contable','isr','iva','obligaciones','procedimiento'):
        refs=[f['id'] for f in snapshot['fuentes'] if f['area']==area]
        data[area]={'texto':'Caso ilustrativo personalizado: revisar los supuestos de la organización y separar el registro de los efectos fiscales y la operación propuesta.','referencias':refs}
    data['ejemplos']=[{'supuestos':'Supuesto ilustrativo de adquisición para la operación comercial; confirmar la actividad real del cliente.','contable':'Reconocer la operación con evidencia suficiente.','isr':'Comprobar los efectos y requisitos del régimen antes de aplicar.','iva':'Analizar el acto y los requisitos propios, sin presumir beneficios.','referencias':[],'movimientos':[{'cuenta':'Inventarios','debe':'100.00','haber':'0.00'},{'cuenta':'Bancos','debe':'0.00','haber':'100.00'}]} for _ in range(2)]
    if snapshot.get('esquema',1)>=2:
        desarrollo='La revisión de este supuesto ficticio documenta la naturaleza del saldo, la evidencia disponible, los responsables y la conciliación del periodo. Las cifras del ejemplo son ilustrativas y se comprueban antes de emplearse en una organización real. Se conserva soporte de los movimientos, fechas, cálculos y autorizaciones; el contador verifica su relación con el giro y el régimen fiscal y determina el tratamiento que procede. '
        for b in data.values():
            if isinstance(b,dict): b['texto'] += ' '+desarrollo*3
        for campo in ('introduccion','politicas','conclusion'):
            data[campo]={'texto':desarrollo*3,'referencias':[]}
        data['materialidad']=[{'contexto':desarrollo,'evidencia':'Conservar comprobante, contrato y confirmación del movimiento para esta prueba ficticia.','validacion':'Conciliar el auxiliar, comprobar autorización y confirmar la naturaleza de la operación.','riesgo':'Falta de soporte, clasificación indebida y efecto fiscal incorrecto sujeto a revisión profesional.'} for _ in range(2)]
    if snapshot.get('esquema',1)>=3:
        from .desarrollo_uniforme import EJES
        data['contable']['desarrollo']={k:t+'. '+desarrollo for k,t in EJES.items()}
        nombre=snapshot['perfil_contable']['descripcion']
        for n,e in enumerate(data['ejemplos'],1):
            e['supuestos']+=' Caso ficticio '+str(n)+'.'
            if snapshot['familia']=='impuestos_diferidos' and snapshot['regimen'].startswith('pf_'):
                e['supuestos']+=' Tasa hipotética ilustrativa, sujeta a revisión del régimen.'
            e['movimientos'][0]['cuenta']=nombre
    return data


@override_settings(SECURE_SSL_REDIRECT=False)
class BibliotecaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user=User.objects.create_user(username='revisor-ficticio',password='test')
        cls.tenant=Tenant.objects.create(nombre='Empresa ficticia',propietario=cls.user,regimen_fiscal='pm_general')
        MembresiaTenant.objects.create(tenant=cls.tenant,usuario=cls.user,rol='propietario')
        cls.sat=CodigoAgrupador.objects.create(codigoagrupador='115',nombre='Inventarios',nivel=1)
        cls.cuenta=CatalogoCuentas.objects.create(tenant=cls.tenant,cuenta='A',descripcion='Inventarios',codigoagrupador=cls.sat)
        call_command('cargar_fundamentos',evidencias=EVIDENCIAS,stdout=io.StringIO())
        call_command('cargar_fuentes_abiertas',stdout=io.StringIO())
        call_command('cargar_desarrollo_uniforme',stdout=io.StringIO())
        call_command('cargar_comparaciones_internacionales',stdout=io.StringIO())

    def setUp(self):
        self.client.force_login(self.user)
        s=self.client.session; s['tenant_id']=self.tenant.pk; s.save()
        self.snapshot=seleccionar(self.cuenta,self.tenant)

    def manual(self,aprobado=False,snapshot=True):
        return ManualContable.objects.create(tenant=self.tenant,titulo='Manual ficticio',contenido='Contenido original',creado_por=self.user,aprobado=aprobado,fundamentos_snapshot=self.snapshot if snapshot else {},fecha_referencia=self.snapshot['fecha'] if snapshot else None)

    def test_48_combinaciones_y_giros_no_heredan_regimen(self):
        for familia in ('inventarios','bancos','clientes','proveedores','ingresos','gastos'):
            c=SimpleNamespace(descripcion=familia,codigoagrupador=SimpleNamespace(nombre=familia,codigoagrupador=''))
            for regimen,_ in Tenant.REGIMEN_CHOICES:
                for giro in ('comercial','servicios',*(['restaurantes'] if familia=='inventarios' else [])):
                    tenant=SimpleNamespace(regimen_fiscal=regimen,giro=giro)
                    snap=seleccionar(c,tenant)
                    self.assertEqual(snap['familia'],familia)
                    self.assertEqual(snap['regimen'],regimen)
                    self.assertTrue(snap['fuentes'])
                    self.assertTrue(snap['pendientes'])
                    self.assertNotIn('completa',snap['cobertura'].values())
                    if regimen=='otro': self.assertEqual(snap['cobertura']['isr'],'pendiente')
                    validar_respuesta(TextoGenerado(json.dumps(respuesta(snap)),[]),snap)

    def test_carga_idempotente_no_activa(self):
        n=CriterioRevisado.objects.count()
        call_command('cargar_fundamentos',evidencias=EVIDENCIAS,stdout=io.StringIO())
        self.assertEqual(CriterioRevisado.objects.count(),n)
        self.assertFalse(ControlBiblioteca.objects.get(pk=1).activa)

    def test_resico_no_hereda_pm_inventarios(self):
        snap=seleccionar(self.cuenta,SimpleNamespace(regimen_fiscal='pf_resico'))
        self.assertIn('sin deducción alguna',' '.join(f['explicacion'] for f in snap['fuentes']))
        self.assertNotIn('Artículos 39 y 41',str(snap))

    def test_fuentes_publicadas_inmutables(self):
        for obj,field in [(FuenteNormativa.objects.first(),'titulo'),(VersionFuente.objects.first(),'edicion'),(CriterioRevisado.objects.first(),'explicacion')]:
            setattr(obj,field,'Cambio indebido')
            with self.assertRaises(ValidationError): obj.save()
        with self.assertRaises(ValidationError): VersionFuente.objects.first().delete()

    def test_solo_versiones_y_criterios_activos_autorizados_y_en_periodo(self):
        v=VersionFuente.objects.get(pk=self.snapshot['fuentes'][0]['version'])
        f=v.fuente
        b=VersionFuente.objects.create(fuente=f,edicion='Sin permiso',vigente_desde=timezone.localdate(),revisado_en=timezone.now(),evidencia_vigencia='Consulta ficticia para prueba',publicado=True)
        CriterioRevisado.objects.create(version=b,familia='inventarios',regimen='pm_general',area='isr',titulo='No enviar',localizacion='Pendiente',explicacion='CONTENIDO RESTRINGIDO',condiciones='Prueba',excepciones='Prueba',vigente_desde=timezone.localdate(),publicado=True,revisado_en=timezone.now())
        self.assertNotIn('CONTENIDO RESTRINGIDO',str(seleccionar(self.cuenta,self.tenant)))
        v.retirado=True; v.save()
        self.assertNotIn(v.pk,[f['version'] for f in seleccionar(self.cuenta,self.tenant)['fuentes']])
        self.assertFalse(seleccionar(self.cuenta,self.tenant,timezone.localdate()-timedelta(days=1))['fuentes'])

    def test_json_invalido_y_referencias_inventadas_rechazadas(self):
        for bad in ['Texto libre','[]','{}']:
            with self.assertRaises(ManualGenerationError): validar_respuesta(bad,self.snapshot)
        data=respuesta(self.snapshot); data['isr']['referencias']=['F999999']
        with self.assertRaises(ManualGenerationError): validar_respuesta(json.dumps(data),self.snapshot)

    def test_citas_libres_html_enlaces_y_afirmaciones_de_cumplimiento_rechazadas(self):
        for texto in ['Fundamento LISR artículo 41','https://ejemplo.invalid','<b>texto</b>','Cumple con las normas','NIF C-4 párrafo 99']:
            data=respuesta(self.snapshot); data['contable']['texto']=texto
            with self.assertRaises(ManualGenerationError): validar_respuesta(json.dumps(data),self.snapshot)

    def test_asiento_desbalanceado_nan_negativo_y_centavos_rechazados(self):
        for monto in ['99.00','NaN','-100','100.001','Infinity']:
            data=respuesta(self.snapshot); data['ejemplos'][0]['movimientos'][1]['haber']=monto
            with self.assertRaises(ManualGenerationError): validar_respuesta(json.dumps(data),self.snapshot)

    def test_fuente_de_area_distinta_no_fundamenta_isr(self):
        data=respuesta(self.snapshot); data['isr']['referencias']=[next(f['id'] for f in self.snapshot['fuentes'] if f['area']=='iva')]
        with self.assertRaises(ManualGenerationError): validar_respuesta(json.dumps(data),self.snapshot)

    def test_pipeline_conserva_consumo_y_snapshot_sin_cargar_fuentes_protegidas(self):
        from .views import generar_contenido_manual
        ControlBiblioteca.objects.filter(pk=1).update(activa=True)
        data=respuesta(self.snapshot)
        raw=TextoGenerado(json.dumps(data),[{'total':32}])
        with patch('catalogo.views.generar_texto',return_value=raw) as api:
            result=generar_contenido_manual([self.cuenta],self.tenant)
        self.assertEqual(result.consumos,[{'total':32}]); self.assertEqual(result.fundamentos_snapshot['fecha'],self.snapshot['fecha'])
        self.assertNotIn('Texto público emitido, edición 2022',str(api.call_args))
        self.assertIn('referencias',str(api.call_args))
        with patch('catalogo.views.generar_texto',return_value=TextoGenerado('fallo',[{'total':3}])):
            with self.assertRaises(ManualGenerationError) as caught: generar_contenido_manual([self.cuenta],self.tenant)
        self.assertEqual(sum(c['total'] for c in caught.exception.consumos),6)
        self.assertEqual([c['causa'] for c in caught.exception.consumos],['json_invalido','json_invalido'])

    def test_aprobacion_post_no_elude_pendientes(self):
        m=self.manual()
        r=self.client.post(reverse('aprobar_manual',args=[m.pk]))
        self.assertRedirects(r,reverse('revisar_fundamentos',args=[m.pk]))
        m.refresh_from_db(); self.assertFalse(m.aprobado)

    def evidencia(self,m,p):
        return dict(pendiente=p,huella=huella(m),norma='Disposición comprobada',edicion='Edición de prueba 2026',localizacion='Artículo específico de la prueba',fecha_consulta=str(timezone.localdate()),nota='Revisión ficticia de prueba suficientemente documentada: se comprobaron los hechos, requisitos y excepciones del supuesto.')

    def test_verificacion_documentada_aprobacion_y_huella(self):
        m=self.manual()
        for p in pendientes_manual(m):
            r=self.client.post(reverse('revisar_fundamentos',args=[m.pk]),self.evidencia(m,p['id']))
            self.assertEqual(r.status_code,302)
        self.assertFalse(pendientes_manual(m))
        self.client.post(reverse('aprobar_manual',args=[m.pk]));m.refresh_from_db()
        self.assertTrue(m.aprobado)
        self.assertEqual(m.revisiones_fundamentos.filter(tipo='aprobacion').get().huella,huella(m))
        n=CriterioRevisado.objects.count()
        self.assertEqual(n,CriterioRevisado.objects.count())
        self.assertIn('verificación profesional documentada',anexo(m))

    def test_casilla_sin_evidencia_y_huella_obsoleta_no_resuelven(self):
        m=self.manual()
        self.client.post(reverse('revisar_fundamentos',args=[m.pk]),{'acepto':'1'})
        self.assertFalse(m.revisiones_fundamentos.exists())
        data=self.evidencia(m,'contable'); data['huella']='incorrecta'
        self.assertContains(self.client.post(reverse('revisar_fundamentos',args=[m.pk]),data),'El contenido cambió')
        self.assertFalse(m.revisiones_fundamentos.exists())

    def test_solo_lectura_y_otra_organizacion_no_verifican(self):
        m=self.manual()
        otro=User.objects.create_user(username='otro-ficticio')
        self.client.force_login(otro)
        s=self.client.session;s['tenant_id']=self.tenant.pk;s.save()
        self.assertNotEqual(self.client.get(reverse('revisar_fundamentos',args=[m.pk])).status_code,200)
        MembresiaTenant.objects.create(usuario=otro,tenant=self.tenant,rol='solo_lectura')
        s=self.client.session;s['tenant_id']=self.tenant.pk;s.save()
        self.assertEqual(self.client.get(reverse('revisar_fundamentos',args=[m.pk])).status_code,200)
        self.assertEqual(self.client.post(reverse('revisar_fundamentos',args=[m.pk]),self.evidencia(m,'contable')).status_code,403)

    def test_editar_contenido_invalida_aprobacion_y_titulo_no(self):
        m=self.manual(aprobado=True)
        RevisionFundamentos.objects.create(manual=m,autor=self.user,huella=huella(m),tipo='verificacion',evidencia={'pendiente':'contable'})
        m.titulo='Título nuevo';m.save();self.assertTrue(m.aprobado)
        self.assertNotIn('contable',[p['id'] for p in pendientes_manual(m)])
        m.contenido='Contenido cambiado';m.save();self.assertFalse(m.aprobado)
        self.assertIn('contable',[p['id'] for p in pendientes_manual(m)])
        self.assertTrue(m.revisiones_fundamentos.filter(tipo='invalidacion',autor=None).exists())

    def test_snapshot_inmutable_y_historicos_conservados(self):
        m=self.manual(aprobado=True,snapshot=False)
        self.assertIn('Sin evaluación',anexo(m));self.assertTrue(m.aprobado)
        m.fundamentos_snapshot=self.snapshot
        with self.assertRaises(ValidationError): m.save()

    def test_retiro_y_cambio_confirmado_abren_pendientes_sin_modificar_manual(self):
        m=self.manual(aprobado=True); old=huella(m)
        f=self.snapshot['fuentes'][0]
        c=CriterioRevisado.objects.get(pk=f['criterio']);c.retirado=True;c.save()
        AlertaFuente.objects.create(fuente_id=f['fuente'],tipo='cambio',detalle='Prueba',resuelta=True,vigente_desde=timezone.localdate(),manuales_afectados=[m.pk])
        self.assertTrue(any(p['id'].startswith('retiro_') for p in pendientes_manual(m)))
        self.assertTrue(any(p['id'].startswith('cambio_') for p in pendientes_manual(m)))
        m.refresh_from_db();self.assertTrue(m.aprobado);self.assertEqual(huella(m),old)

    def test_anexo_visible_en_pantalla_word_y_pdf_impresion(self):
        m=self.manual();r=self.client.get(reverse('detalle_manual',args=[m.pk]))
        self.assertContains(r,'Fecha de referencia:');self.assertContains(r,'Referencia pendiente de revisión profesional en ejemplar autorizado')
        r=self.client.get(reverse('exportar_manual',args=[m.pk]));doc=Document(io.BytesIO(r.content))
        text='\n'.join(p.text for p in doc.paragraphs)
        self.assertIn('Fecha de referencia:',text);self.assertIn(self.snapshot['fuentes'][0]['edicion'],text)
        self.assertEqual(r['Cache-Control'].find('no-store')>=0,True)
        self.assertNotIn('<script',str(BeautifulSoup(text,'html.parser')))

    @override_settings(ROOT_URLCONF='panel.root_urls',MIDDLEWARE=['django.contrib.sessions.middleware.SessionMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware'])
    def test_panel_roles_y_mfa(self):
        AccesoPanel.objects.create(usuario=self.user,rol='consulta',secreto_totp='ABC')
        self.assertEqual(self.client.get(reverse('panel:biblioteca')).status_code,302)
        s=self.client.session;s['panel_2fa']=self.user.pk;s.save()
        self.assertEqual(self.client.get(reverse('panel:biblioteca')).status_code,200)
        for rol in ('consulta','comercial','soporte'):
            AccesoPanel.objects.filter(usuario=self.user).update(rol=rol)
            self.assertEqual(self.client.get(reverse('panel:fuente_nueva',args=['fuente'])).status_code,403)
            self.assertEqual(self.client.post(reverse('panel:biblioteca_activar'),{'activa':'1'}).status_code,403)
        AccesoPanel.objects.filter(usuario=self.user).update(rol='propietario')
        self.assertEqual(self.client.get(reverse('panel:fuente_nueva',args=['fuente'])).status_code,200)
        self.client.post(reverse('panel:biblioteca_activar'),{'activa':'1'})
        self.assertTrue(ControlBiblioteca.objects.get(pk=1).activa)

    def test_monitor_fallo_y_cambio_no_publican_ni_modifican(self):
        n=CriterioRevisado.objects.count()
        with patch('catalogo.management.commands.comprobar_fuentes.obtener',return_value='a'*64):
            call_command('comprobar_fuentes',stdout=io.StringIO());call_command('comprobar_fuentes',stdout=io.StringIO())
        self.assertEqual(AlertaFuente.objects.filter(tipo='cambio').count(),3)
        with patch('catalogo.management.commands.comprobar_fuentes.obtener',side_effect=ValueError('fallo')):
            call_command('comprobar_fuentes',stdout=io.StringIO())
        self.assertEqual(AlertaFuente.objects.filter(tipo='consulta_fallida').count(),3)
        self.assertEqual(CriterioRevisado.objects.count(),n)
        for url in ('http://www.sat.gob.mx/','https://127.0.0.1/','https://example.com/','https://www.sat.gob.mx:444/'):
            with self.assertRaises(ValueError): obtener(url)

    def test_generacion_post_guarda_fuentes_y_fecha_y_no_aprueba(self):
        ControlBiblioteca.objects.filter(pk=1).update(activa=True)
        raw=TextoGenerado(json.dumps(respuesta(self.snapshot)),[{'proveedor':'simulado','modelo':'prueba','entrada':10,'salida':20,'total':30,'resultado':'completo'}])
        with patch('catalogo.views.generar_texto',return_value=raw):
            r=self.client.post(reverse('generar_manual'),{'cuentas':[str(self.cuenta.pk)]})
        self.assertEqual(r.status_code,302)
        m=ManualContable.objects.get(tenant=self.tenant)
        self.assertFalse(m.aprobado)
        self.assertEqual(str(m.fecha_referencia),self.snapshot['fecha'])
        self.assertTrue(m.fundamentos_snapshot['fuentes'])
        self.assertTrue(m.usos_ia.get().manual_generado)

    def test_historico_aprobacion_nueva_exige_y_muestra_evidencia(self):
        ControlBiblioteca.objects.filter(pk=1).update(activa=True)
        m=self.manual(snapshot=False)
        self.client.post(reverse('aprobar_manual',args=[m.pk]));m.refresh_from_db();self.assertFalse(m.aprobado)
        self.client.post(reverse('revisar_fundamentos',args=[m.pk]),self.evidencia(m,'historico'))
        self.client.post(reverse('aprobar_manual',args=[m.pk]));m.refresh_from_db();self.assertTrue(m.aprobado)
        self.assertIn('Revisión profesional posterior:',anexo(m))
        self.assertIn('Revisión aprobada por',anexo(m))

    def test_no_aplica_requiere_justificacion_y_conserva_pendientes(self):
        data=respuesta(self.snapshot);data['iva']={'texto':'No aplica','referencias':[],'no_aplica':True}
        with self.assertRaises(ManualGenerationError):validar_respuesta(json.dumps(data),self.snapshot)
        data['iva']['texto']='No se puede concluir el tratamiento de esta operación porque faltan datos sobre el acto y sus condiciones; se requiere revisión profesional específica.'
        r=validar_respuesta(json.dumps(data),self.snapshot)
        self.assertIn('iva',[p['id'] for p in r.fundamentos_snapshot['pendientes']])

    def test_admin_no_elude_aprobacion_ni_instantanea(self):
        from django.contrib.admin.sites import AdminSite
        from django.test import RequestFactory
        from .admin import ManualContableAdmin
        m=self.manual()
        config=ManualContableAdmin(ManualContable,AdminSite())
        req=RequestFactory().get('/admin/catalogo/manualcontable/')
        req.user=self.user
        self.assertFalse(config.has_add_permission(req))
        campos=config.get_form(req,obj=m).base_fields
        for campo in ('aprobado','fundamentos_snapshot','fecha_referencia','tenant','creado_por'):
            self.assertNotIn(campo,campos)

    def test_recupera_automaticamente_sin_descartar_controles_y_suma_consumos(self):
        from .views import generar_contenido_manual
        ControlBiblioteca.objects.filter(pk=1).update(activa=True)
        mala=respuesta(self.snapshot);mala['isr']['referencias']=['F999999']
        bad=TextoGenerado(json.dumps(mala),[{'total':7}])
        good=TextoGenerado(json.dumps(respuesta(self.snapshot)),[{'total':11}])
        with patch('catalogo.views.generar_texto',side_effect=[bad,good]) as api:
            resultado=generar_contenido_manual([self.cuenta],self.tenant)
        self.assertEqual(api.call_count,2)
        self.assertTrue(api.call_args_list[0].kwargs['formato_json'])
        self.assertIn('referencia_no_autorizada',[c.get('causa') for c in resultado.consumos])
        self.assertEqual(sum(c['total'] for c in resultado.consumos),18)
        self.assertNotIn('F999999',str(resultado))
        self.assertNotIn(str(bad),api.call_args_list[1].args[1])

    def test_dos_fallos_conservan_cuenta_muestran_aviso_sin_modal_tecnico(self):
        from panel.models import Evento
        ControlBiblioteca.objects.filter(pk=1).update(activa=True)
        raw=TextoGenerado('malformado',[{'entrada':2,'salida':3,'total':5}])
        with patch('catalogo.views.generar_texto',return_value=raw) as api:
            r=self.client.post(reverse('generar_manual'),{'cuentas':[str(self.cuenta.pk)]},follow=True)
        self.assertEqual(api.call_count,2)
        self.assertContains(r,'No pudimos completar este manual')
        self.assertContains(r,'Volver a generar esta cuenta')
        self.assertContains(r,'data-retry-account="'+str(self.cuenta.pk)+'"')
        self.assertNotContains(r,'validación de estructura, referencias o asientos')
        self.assertFalse(ManualContable.objects.exists())
        from .models import UsoIA
        uso=UsoIA.objects.get();self.assertEqual(uso.tokens_total,10)
        self.assertFalse(uso.manual_generado)
        self.assertContains(r,'GEN-'+str(uso.pk))
        evento=Evento.objects.filter(accion='generacion.rechazada').latest('pk')
        self.assertEqual(evento.detalle,'Causa: json_invalido')

    def test_aviso_de_otro_tenant_o_expirado_no_se_muestra(self):
        for tenant,fecha in [(999999,timezone.now().timestamp()),(self.tenant.pk,0)]:
            session=self.client.session
            session['manual_generacion_pendiente']={'tenant':tenant,'usuario':self.user.pk,'fecha':fecha,'nombre':'No mostrar','cuenta':str(self.cuenta.pk)}
            session.save()
            self.assertNotContains(self.client.get(reverse('generar_manual')),'No pudimos completar este manual')

    def test_exito_limpia_incidencia_y_reintentos_no_crean_dos_manuales(self):
        ControlBiblioteca.objects.filter(pk=1).update(activa=True)
        session=self.client.session;session['manual_generacion_pendiente']={'tenant':self.tenant.pk};session.save()
        with patch('catalogo.views.generar_texto',side_effect=[TextoGenerado('fallo',[]),TextoGenerado(json.dumps(respuesta(self.snapshot)),[])]) as api:
            self.client.post(reverse('generar_manual'),{'cuentas':[str(self.cuenta.pk)]})
        self.assertEqual(api.call_count,2);self.assertEqual(ManualContable.objects.count(),1)
        self.assertNotIn('manual_generacion_pendiente',self.client.session)

    def test_esquema_sin_fuentes_no_inventa_ejemplos_de_identificadores(self):
        from .biblioteca import instrucciones
        snap=seleccionar(SimpleNamespace(descripcion='Terrenos',codigoagrupador=SimpleNamespace(nombre='Terrenos',codigoagrupador='151')),self.tenant)
        snap['fuentes']=[]
        prompt=instrucciones(snap)
        self.assertFalse(snap['fuentes']);self.assertNotIn('"F1"',prompt);self.assertNotIn('"F2"',prompt)
        self.assertNotIn('bibliografia',prompt)
        self.assertNotIn('https://cinif.org.mx',prompt)

    def test_json_cercado_valido_y_codigos_especificos(self):
        from .biblioteca import RespuestaManualInvalida
        validar_respuesta('```json\n'+json.dumps(respuesta(self.snapshot))+'\n```',self.snapshot)
        data=respuesta(self.snapshot);data['ejemplos'][0]['movimientos'][1]['haber']='99.00'
        with self.assertRaises(RespuestaManualInvalida) as caught:validar_respuesta(json.dumps(data),self.snapshot)
        self.assertEqual(caught.exception.codigo,'asiento_desbalanceado')

    def test_texto_de_articulos_comerciales_y_negacion_no_son_citas(self):
        data=respuesta(self.snapshot)
        data['contable']['texto']='Los artículos de inventario requieren conteo. Este borrador no acredita cumplimiento con las normas; requiere revisión profesional.'
        validar_respuesta(json.dumps(data),self.snapshot)

    def test_cuenta185_identifica_nif_d4_y_nic12_con_titulo_descriptivo(self):
        from .perfil_contable import titulo_cuenta
        c=SimpleNamespace(cuenta='185',descripcion='Impuestos diferidos',codigoagrupador=SimpleNamespace(nombre='Impuestos diferidos',codigoagrupador='185'))
        snap=seleccionar(c,SimpleNamespace(regimen_fiscal='pf_empresarial'))
        self.assertEqual(snap['familia'],'impuestos_diferidos')
        self.assertEqual(snap['perfil_contable']['normas'][0]['clave'],'NIF D-4')
        self.assertIn('NIC 12',snap['perfil_contable']['internacionales'][0])
        self.assertIn('Impuestos diferidos',titulo_cuenta(c))
        self.assertTrue(any(f['area']=='contable' for f in snap['fuentes']))

    def test_manuales_completos_conservan_estructura_y_nif(self):
        data=respuesta(self.snapshot)
        r=validar_respuesta(json.dumps(data),self.snapshot)
        for titulo in ('Introducción y alcance','NIF mexicanas aplicables','Referencia internacional','Políticas contables','Caso de materialidad 1','Caso de materialidad 2','Ejemplo 1','Ejemplo 2','Conclusión profesional','NIF C-4'):
            self.assertIn(titulo,str(r))
        data['politicas']['texto']='Sin desarrollo.'
        with self.assertRaises(ManualGenerationError):validar_respuesta(json.dumps(data),self.snapshot)

    def test_perfil_admite_nif_identificada_pero_no_parrafos_inventados(self):
        data=respuesta(self.snapshot)
        data['contable']['texto']+=' NIF C-4: comparar políticas de inventarios, sin declarar cumplimiento.'
        validar_respuesta(json.dumps(data),self.snapshot)
        data['contable']['texto']+=' NIF C-4 párrafo 999 establece este cálculo.'
        with self.assertRaises(ManualGenerationError):validar_respuesta(json.dumps(data),self.snapshot)

    def test_fuente_abierta_incluye_licencia_autoria_y_limites(self):
        fuentes=[f for f in self.snapshot['fuentes'] if f['area']=='contable']
        self.assertTrue(fuentes)
        for f in fuentes:
            self.assertIn('CC BY 4.0',f['atribucion'])
            self.assertIn('Arnold',f['atribucion'])
            self.assertIn('2021',f['edicion'])
        self.assertIn('Atribución y adaptación educativa',anexo(self.manual()))

    def test_reformulacion_archiva_snapshot_y_no_toca_aprobados(self):
        from .reformulacion import reformular_borrador
        m=self.manual(snapshot=False);old=huella(m)
        r=validar_respuesta(json.dumps(respuesta(self.snapshot)),self.snapshot)
        actualizado=reformular_borrador(m.pk,r,'Manual descriptivo',old)
        self.assertFalse(actualizado.aprobado)
        historial=actualizado.revisiones_fundamentos.get(tipo='reformulacion')
        self.assertEqual(historial.evidencia['contenido_anterior'],'Contenido original')
        self.assertEqual(historial.evidencia['fundamentos_anteriores'],{})
        self.assertEqual(historial.huella,old)
        actualizado.aprobado=True;actualizado.save()
        with self.assertRaises(ValidationError):reformular_borrador(actualizado.pk,r,'Otro título',huella(actualizado))

    def test_185_no_puede_presentarse_como_pasivo_en_los_ejemplos(self):
        c=SimpleNamespace(cuenta='185',descripcion='Impuestos diferidos',codigoagrupador=SimpleNamespace(nombre='Impuestos diferidos',codigoagrupador='185'))
        snap=seleccionar(c,SimpleNamespace(regimen_fiscal='pf_empresarial'))
        data=respuesta(snap)
        for e in data['ejemplos']:
            e['supuestos']+=' Tasa ilustrativa del 20%, sujeta a confirmación.'
            e['movimientos'][0]['cuenta']='185 Impuestos diferidos activo'
        validar_respuesta(json.dumps(data),snap)
        data['ejemplos'][0]['movimientos'][0]['cuenta']='185 Impuestos diferidos pasivo'
        with self.assertRaises(ManualGenerationError):validar_respuesta(json.dumps(data),snap)

    def test_variantes_de_formato_preservan_contenido_y_validan_referencias(self):
        data=respuesta(self.snapshot)
        data['procedimiento']={'texto':'Procedimiento propio para conciliar saldos y conservar evidencia.','pasos':['Conciliar el auxiliar con soporte.','Documentar revisión y autorización.']}
        data['introduccion'].pop('referencias')
        ref=next(f['id'] for f in self.snapshot['fuentes'] if f['area']=='contable')
        data['contable']['texto']+=' Apoyo educativo según '+ref+'.'
        r=validar_respuesta(json.dumps(data),self.snapshot)
        self.assertIn('Conciliar el auxiliar con soporte.',str(r))
        self.assertIn('Intermediate Financial Accounting',str(r))
        self.assertNotIn('según '+ref,str(r))
        data['contable']['texto']+=' Fundamento F999999.'
        with self.assertRaises(ManualGenerationError):validar_respuesta(json.dumps(data),self.snapshot)
