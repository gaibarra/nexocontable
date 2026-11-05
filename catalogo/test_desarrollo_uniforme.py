import copy
import io
import json
from types import SimpleNamespace
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from .desarrollo_uniforme import categoria, PERFILES, EJES, VERSION
from .perfil_contable import perfil
from .biblioteca import seleccionar, validar_respuesta, RespuestaManualInvalida
from .models import CriterioRevisado, ManualContable
from . import test_biblioteca as base
from cuentas.models import Tenant


def cuenta(codigo,nombre):
    return SimpleNamespace(cuenta=codigo,descripcion=nombre,
        codigoagrupador=SimpleNamespace(codigoagrupador=codigo,nombre=nombre))


class ClasificacionTests(SimpleTestCase):
    def test_naturalezas_que_no_deben_mezclarse(self):
        casos=[('120','Anticipo a proveedores','anticipos','NIF C-5'),
               ('206','Anticipo de cliente','anticipos_recibidos','NIF D-1'),
               ('210','Provisión de sueldos por pagar','empleados','NIF D-3'),
               ('108','Estimación de cuentas incobrables','cobrar','NIF C-16'),
               ('171','Depreciación acumulada','ppe','NIF C-6'),
               ('613','Depreciación contable','ppe','NIF C-6'),
               ('259','Impuestos diferidos','impuestos_utilidad','NIF D-4'),
               ('702','Productos financieros','inversiones','NIF C-2'),
               ('801','UFIN del ejercicio','orden',None),
               ('899','Otras cuentas de orden','orden',None)]
        for codigo,nombre,tipo,norma in casos:
            with self.subTest(codigo=codigo):
                c=cuenta(codigo,nombre);self.assertEqual(categoria(c),tipo)
                p=perfil(c,PERFILES[tipo]['familia'])
                if norma:self.assertIn(norma,[n['clave'] for n in p['normas']])
                else:self.assertEqual(p['normas'],[])
    
    def test_codigo_interno_no_sustituye_agrupador_y_cuenta_ambigua_no_fuerza_nif(self):
        c=cuenta('206','Anticipo de cliente');c.cuenta='101'
        self.assertEqual(categoria(c),'anticipos_recibidos')
        p=perfil(SimpleNamespace(cuenta='XX',descripcion='Partida pendiente de identificar'),'otra')
        self.assertEqual(p['categoria'],'general');self.assertEqual(p['normas'],[])
        self.assertEqual(set(p['guia_tecnica']['ejes']),set(EJES))


class ContratoDesarrolloTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        base.BibliotecaTests.setUpTestData.__func__(cls)

    def setUp(self):
        self.snapshot=seleccionar(self.cuenta,self.tenant)

    def test_carga_idempotente_y_perfiles_no_contaminan_otras_cuentas(self):
        qs=CriterioRevisado.objects.filter(titulo=VERSION).exclude(perfil_tecnico='')
        n=qs.count();self.assertEqual(n,len(PERFILES)*len(Tenant.REGIMEN_CHOICES))
        call_command('cargar_desarrollo_uniforme',stdout=io.StringIO());self.assertEqual(n,qs.count())
        refs=[f for f in self.snapshot['fuentes'] if f['area']=='contable']
        self.assertEqual({f['perfil_tecnico'] for f in refs},{'inventarios'})
        self.assertEqual(len(refs),2)
        self.assertEqual(self.snapshot['esquema'],3)
        self.assertEqual(self.snapshot['estandar'],VERSION)

    def test_campos_omitidos_cortos_o_duplicados_no_se_aceptan(self):
        for modo in ('omitido','corto','duplicado'):
            with self.subTest(modo=modo):
                data=base.respuesta(self.snapshot)
                if modo=='omitido':del data['contable']['desarrollo']['baja']
                if modo=='corto':data['contable']['desarrollo']['baja']='Pendiente de revisar.'
                if modo=='duplicado':data['contable']['desarrollo']['baja']=data['contable']['desarrollo']['reconocimiento']
                with self.assertRaises(RespuestaManualInvalida) as caught:
                    validar_respuesta(json.dumps(data),self.snapshot)
                self.assertEqual(caught.exception.codigo,'desarrollo_contable_incompleto')

    def test_ejemplos_ajenos_o_copiados_no_se_aceptan(self):
        for modo in ('ajeno','copiado'):
            data=base.respuesta(self.snapshot)
            if modo=='ajeno':data['ejemplos'][0]['movimientos'][0]['cuenta']='Caja'
            else:data['ejemplos'][1]=copy.deepcopy(data['ejemplos'][0])
            with self.assertRaises(RespuestaManualInvalida) as caught:validar_respuesta(json.dumps(data),self.snapshot)
            self.assertEqual(caught.exception.codigo,'ejemplo_fuera_de_alcance')

    def test_iva_declarado_no_puede_faltar_del_asiento(self):
        data=base.respuesta(self.snapshot)
        data['ejemplos'][0]['contable']='Se registra la adquisición y el IVA acreditable por separado.'
        with self.assertRaises(RespuestaManualInvalida) as caught:validar_respuesta(json.dumps(data),self.snapshot)
        self.assertEqual(caught.exception.codigo,'iva_asiento_incompleto')

    def test_correctora_no_sustituye_cuenta_de_gasto_seleccionada(self):
        snap=seleccionar(cuenta('613','Depreciación contable'),self.tenant)
        data=base.respuesta(snap)
        data['ejemplos'][0]['movimientos'][0]['cuenta']='Depreciación acumulada'
        with self.assertRaises(RespuestaManualInvalida) as caught:validar_respuesta(json.dumps(data),snap)
        self.assertEqual(caught.exception.codigo,'ejemplo_fuera_de_alcance')

    def test_retiro_y_permisos_impiden_incorporar_la_guia_publicada(self):
        c=CriterioRevisado.objects.get(pk=next(f['criterio'] for f in self.snapshot['fuentes'] if f['perfil_tecnico']=='inventarios'))
        c.retirado=True;c.save(update_fields=['retirado'])
        nuevo=seleccionar(self.cuenta,self.tenant)
        self.assertNotIn('guia_tecnica',nuevo['perfil_contable'])
        self.assertNotIn(c.pk,[f['criterio'] for f in nuevo['fuentes']])
        # El documento histórico conserva su instantánea, incluso después del retiro.
        self.assertIn('guia_tecnica',self.snapshot['perfil_contable'])

    def test_esquema_anterior_sigue_exportable_sin_reescribir_su_contenido(self):
        snap=copy.deepcopy(self.snapshot);snap['esquema']=2;snap.pop('estandar')
        data=base.respuesta(snap)
        r=validar_respuesta(json.dumps(data),snap)
        self.assertNotIn('### Valuación inicial',r)
        self.assertEqual(r.fundamentos_snapshot['esquema'],2)

    def test_matriz_perfiles_regimenes_y_giros_conserva_los_seis_ejes(self):
        for tipo,p in PERFILES.items():
            # Los nombres son categorías ficticias, sin datos de clientes.
            nombres={'caja':'Caja','bancos':'Bancos','inversiones':'Inversiones',
                'cobrar':'Cuentas por cobrar','anticipos':'Pagos anticipados','inventarios':'Inventarios',
                'ppe':'Equipo de oficina','intangibles':'Software','deuda':'Proveedores',
                'anticipos_recibidos':'Anticipo de cliente','ingresos':'Ingresos','gastos':'Gastos',
                'costos':'Costo de servicios','impuestos':'Impuestos a favor',
                'impuestos_utilidad':'Impuestos diferidos','empleados':'Sueldos',
                'provisiones':'Provisión por litigio','arrendamientos':'Arrendamiento',
                'capital':'Capital','participaciones':'Inversión permanente en acciones',
                'especializada':'Activo biológico','orden':'Otras cuentas de orden','general':'Partida por identificar'}
            codigos={'participaciones':'188','orden':'899'}
            c=cuenta(codigos.get(tipo,''),nombres[tipo]);c.cuenta='PRUEBA'
            for reg,_ in Tenant.REGIMEN_CHOICES:
                for giro in (('comercial','servicios','restaurantes') if tipo=='inventarios' else ('comercial','servicios')):
                    with self.subTest(tipo=tipo,regimen=reg,giro=giro):
                        org=SimpleNamespace(nombre='Organización ficticia',regimen_fiscal=reg, get_giro_display=lambda g=giro:g, get_regimen_fiscal_display=lambda r=reg:r)
                        snap=seleccionar(c,org)
                        self.assertEqual(snap['perfil_contable']['categoria'],tipo)
                        self.assertEqual(set(snap['perfil_contable']['guia_tecnica']['ejes']),set(EJES))
                        from .prompts import build_manual_prompts
                        _,prompt=build_manual_prompts([c],org,biblioteca_snapshot=snap)
                        self.assertIn(giro,prompt)
                        r=validar_respuesta(json.dumps(base.respuesta(snap)),snap)
                        for titulo in EJES.values():self.assertIn('### '+titulo,r)
                        self.assertIn('Referencia pendiente de revisión profesional',r)
