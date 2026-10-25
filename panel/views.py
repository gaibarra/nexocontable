import time
from datetime import timedelta
from urllib.parse import quote
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction, connection
from django.db.models import Count, Q, Sum, F
from django.db.models.functions import TruncDate, Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST, require_http_methods
from catalogo.models import ManualContable, UsoIA, CatalogoCuentas
from cuentas.models import Tenant
from donaciones.models import Donativo
from .audit import registrar
from .forms import ContactoForm, TareaForm, ControlForm
from .models import AccesoPanel, Contacto, Evento, Nota, Tarea, ControlPlataforma
from .security import privado, permitido, consumir_intento, secreto, validar_totp
from .services import pulso, radar, sincronizar_usuario

EDITORES = ('propietario', 'comercial')


def pagina(request, queryset):
    return Paginator(queryset, 30).get_page(request.GET.get('page'))


def buscar(request, queryset, fields):
    term = request.GET.get('q', '').strip()[:150]
    if term:
        query = Q()
        for field in fields:
            query |= Q(**{field + '__icontains': term})
        queryset = queryset.filter(query)
    return queryset


@never_cache
@sensitive_post_parameters('password')
@require_http_methods(['GET', 'POST'])
def login(request):
    if permitido(request.user):
        return redirect('panel:inicio' if request.session.get('panel_2fa') == request.user.pk else 'panel:verificar')
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST':
        nombre = request.POST.get('username', '').strip().lower()[:254]
        ip = request.META.get('HTTP_X_REAL_IP', request.META.get('REMOTE_ADDR', ''))
        if not consumir_intento('password:' + nombre) or not consumir_intento('ip:' + ip):
            form.add_error(None, 'Demasiados intentos. Vuelve a intentar dentro de 15 minutos.')
        elif form.is_valid():
            user = form.get_user()
            if permitido(user):
                auth_login(request, user)
                request.session['panel_password_at'] = time.time()
                request.session.pop('panel_2fa', None)
                return redirect('panel:verificar')
            form.add_error(None, 'No fue posible acceder con estas credenciales.')
    return render(request, 'panel/login.html', {'form': form})


@never_cache
@sensitive_post_parameters('codigo')
@require_http_methods(['GET', 'POST'])
def verificar(request):
    if not permitido(request.user):
        return redirect('panel:login')
    if request.session.get('panel_2fa') == request.user.pk:
        return redirect('panel:inicio')
    if time.time() - request.session.get('panel_password_at', 0) > 300:
        auth_logout(request)
        return redirect('panel:login')
    acceso = request.user.acceso_panel
    inicial = not acceso.secreto_totp
    if inicial and 'panel_enrolamiento' not in request.session:
        request.session['panel_enrolamiento'] = secreto()
    secret = acceso.secreto_totp or request.session['panel_enrolamiento']
    error = ''
    if request.method == 'POST':
        if not consumir_intento('otp:' + str(request.user.pk)):
            error = 'Demasiados intentos. Espera 15 minutos e inicia sesión de nuevo.'
        else:
            with transaction.atomic():
                acceso = AccesoPanel.objects.select_for_update().get(pk=acceso.pk)
                secret = acceso.secreto_totp or secret
                paso = validar_totp(secret, request.POST.get('codigo', '').strip(), acceso.ultimo_paso)
                if paso is not None and acceso.activo:
                    acceso.secreto_totp, acceso.ultimo_paso = secret, paso
                    acceso.save(update_fields=['secreto_totp', 'ultimo_paso'])
                    request.session.cycle_key()
                    request.session['panel_2fa'] = request.user.pk
                    request.session.pop('panel_enrolamiento', None)
                    registrar('panel', 'acceso.verificado', actor=request.user.pk)
                    return redirect('panel:inicio')
                error = 'Código inválido o ya utilizado. Prueba con el siguiente código.'
    uri = f'otpauth://totp/{quote("Manual Contable:" + request.user.username)}?secret={secret}&issuer=Manual%20Contable&digits=6&period=30'
    return render(request, 'panel/verificar.html', {'inicial': inicial, 'secret': secret if inicial else '', 'uri': uri if inicial else '', 'error': error})


@require_POST
def logout(request):
    auth_logout(request)
    return redirect('panel:login')


@privado()
def inicio(request):
    resumen = pulso()
    desde = timezone.now() - timedelta(days=30)
    valores = {row['dia']: row['n'] for row in ManualContable.objects.filter(fecha_creacion__gte=desde)
               .annotate(dia=TruncDate('fecha_creacion')).values('dia').annotate(n=Count('pk'))}
    dias = [timezone.localdate()-timedelta(days=i) for i in range(13, -1, -1)]
    maximo = max([valores.get(d, 0) for d in dias] + [1])
    serie = [{'dia': d, 'n': valores.get(d, 0), 'alto': max(3, round(valores.get(d, 0)*100/maximo))} for d in dias]
    etapas = [dict(key=k, nombre=n, total=Contacto.objects.filter(etapa=k).count()) for k, n in Contacto.ETAPAS[:6]]
    return render(request, 'panel/inicio.html', {
        'titulo': 'Vista de mando', 'resumen': resumen, 'serie': serie, 'etapas': etapas,
        'usuarios': get_user_model().objects.count(), 'organizaciones': Tenant.objects.count(),
        'activos': get_user_model().objects.filter(last_login__gte=desde, is_active=True).count(),
        'donativos': Donativo.objects.filter(estado__in=['aprobado', 'parcial']).aggregate(n=Sum(Coalesce('monto_confirmado', F('monto') - F('monto_reembolsado'))))['n'] or 0,
        'eventos': Evento.objects.select_related('actor')[:8],
        'tareas': Tarea.objects.filter(completada=False).select_related('contacto')[:5],
    })


@privado()
def crm(request):
    contactos = buscar(request, Contacto.objects.select_related('responsable', 'usuario'), ['nombre', 'email', 'despacho', 'etiquetas', 'origen'])
    etapa = request.GET.get('etapa', '')
    if etapa in dict(Contacto.ETAPAS):
        contactos = contactos.filter(etapa=etapa)
    columnas = [{'key': k, 'nombre': n, 'total': contactos.filter(etapa=k).count(), 'contactos': contactos.filter(etapa=k)[:12]} for k, n in Contacto.ETAPAS]
    return render(request, 'panel/crm.html', {'titulo': 'CRM · Relaciones que crecen', 'columnas': columnas,
                  'contactos': pagina(request, contactos), 'etapas': Contacto.ETAPAS, 'seleccion': etapa})


@privado(*EDITORES)
@require_http_methods(['GET', 'POST'])
def contacto_form(request, pk=None):
    obj = get_object_or_404(Contacto, pk=pk) if pk else None
    form = ContactoForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                obj = form.save(commit=False)
                if not obj.usuario_id:
                    users = get_user_model().objects.filter(email__iexact=obj.email)
                    if users.count() == 1:
                        user = users.first()
                        if not Contacto.objects.filter(usuario=user).exclude(pk=obj.pk).exists():
                            obj.usuario = user
                obj.save()
                registrar('crm', 'contacto.editado' if pk else 'contacto.creado', referencia=obj.pk)
            messages.success(request, 'Contacto guardado.')
            return redirect('panel:contacto', pk=obj.pk)
        except IntegrityError:
            form.add_error(None, 'El correo o usuario ya está vinculado a otro contacto. Revisa los datos.')
    return render(request, 'panel/form.html', {'titulo': 'Editar contacto' if pk else 'Nuevo contacto', 'form': form})


@privado()
def contacto(request, pk):
    obj = get_object_or_404(Contacto.objects.select_related('usuario', 'responsable'), pk=pk)
    eventos = Evento.objects.filter(actor_id=obj.usuario_id).select_related('actor')[:30] if obj.usuario_id else []
    return render(request, 'panel/contacto.html', {'titulo': obj.nombre, 'contacto': obj, 'eventos': eventos,
                  'tarea_form': TareaForm(), 'tareas': obj.tareas.select_related('responsable')[:40], 'notas': obj.notas.select_related('autor')[:40]})


@privado(*EDITORES)
@require_POST
def nota(request, pk):
    obj = get_object_or_404(Contacto, pk=pk)
    texto = request.POST.get('texto', '').strip()
    if texto and len(texto) <= 4000:
        with transaction.atomic():
            Nota.objects.create(contacto=obj, texto=texto, autor=request.user)
            registrar('crm', 'nota.creada', referencia=obj.pk)
        messages.success(request, 'Nota agregada.')
    else:
        messages.error(request, 'La nota debe contener entre 1 y 4000 caracteres.')
    return redirect('panel:contacto', pk=pk)


@privado(*EDITORES)
@require_POST
def tarea(request, pk):
    obj = get_object_or_404(Contacto, pk=pk)
    form = TareaForm(request.POST)
    if form.is_valid():
        with transaction.atomic():
            item = form.save(commit=False)
            item.contacto, item.responsable = obj, request.user
            item.save()
            registrar('crm', 'tarea.creada', referencia=item.pk)
        messages.success(request, 'Seguimiento programado.')
    else:
        messages.error(request, 'Revisa el título y la fecha del seguimiento.')
    return redirect('panel:contacto', pk=pk)


@privado(*EDITORES)
@require_POST
def completar_tarea(request, pk):
    with transaction.atomic():
        item = get_object_or_404(Tarea.objects.select_for_update(), pk=pk)
        item.completada = True
        item.save(update_fields=['completada'])
        registrar('crm', 'tarea.completada', referencia=item.pk)
    return redirect('panel:contacto', pk=item.contacto_id)


@privado(*EDITORES)
@require_POST
def sincronizar(request):
    count = 0
    for user in get_user_model().objects.filter(is_active=True).exclude(email='').iterator(chunk_size=100):
        try:
            if sincronizar_usuario(user):
                count += 1
        except IntegrityError:
            continue
    registrar('crm', 'contactos.sincronizados', detalle=f'{count} contactos procesados')
    messages.success(request, f'{count} contactos sincronizados. Se conservaron notas, tareas y responsables.')
    return redirect('panel:crm')


@privado()
def actividad(request):
    qs = Evento.objects.select_related('actor')
    qs = buscar(request, qs, ['accion', 'detalle', 'actor__username', 'referencia'])
    categoria = request.GET.get('categoria', '')
    if categoria:
        qs = qs.filter(categoria=categoria[:30])
    for param, field in [('usuario', 'actor_id'), ('organizacion', 'organizacion_id')]:
        value = request.GET.get(param, '')
        if value.isdecimal() and len(value) < 15:
            qs = qs.filter(**{field: int(value)})
    for param, field in [('desde', 'fecha__date__gte'), ('hasta', 'fecha__date__lte')]:
        from django.utils.dateparse import parse_date
        value = request.GET.get(param, '')
        try:
            date = parse_date(value)
        except ValueError:
            date = None
        if date:
            qs = qs.filter(**{field: date})
    if request.GET.get('errores') == '1':
        qs = qs.filter(estado_http__gte=500)
    return render(request, 'panel/actividad.html', {'titulo': 'Radar de actividad', 'eventos': pagina(request, qs),
                  'categorias': Evento.objects.order_by('categoria').values_list('categoria', flat=True).distinct()})


@privado()
def usuarios(request):
    qs = buscar(request, get_user_model().objects.annotate(total_org=Count('tenants_propios', distinct=True), total_manuales=Count('manualcontable', distinct=True)).order_by('-date_joined'), ['username', 'email', 'first_name', 'last_name'])
    return render(request, 'panel/usuarios.html', {'titulo': 'Usuarios de la plataforma', 'usuarios': pagina(request, qs)})


@privado()
def usuario(request, pk):
    obj = get_object_or_404(get_user_model(), pk=pk)
    return render(request, 'panel/usuario.html', {'titulo': obj.get_full_name() or obj.username, 'persona': obj,
                  'organizaciones': Tenant.objects.filter(propietario=obj)[:50],
                  'usos': UsoIA.objects.filter(usuario=obj).aggregate(tokens=Sum('tokens_total'), intentos=Count('pk')),
                  'eventos': Evento.objects.filter(actor=obj)[:40],
                  'contacto_crm': Contacto.objects.filter(usuario=obj).first()})


@privado('propietario')
@require_POST
def estado_usuario(request, pk):
    motivo = request.POST.get('motivo', '').strip()[:300]
    if not motivo:
        messages.error(request, 'Escribe el motivo antes de confirmar.')
        return redirect('panel:usuario', pk=pk)
    with transaction.atomic():
        obj = get_object_or_404(get_user_model().objects.select_for_update(), pk=pk)
        if obj.pk == request.user.pk or obj.is_superuser or AccesoPanel.objects.filter(usuario=obj).exists():
            raise PermissionDenied('Las cuentas administrativas se gestionan desde el servidor.')
        obj.is_active = not obj.is_active
        obj.save(update_fields=['is_active'])
        registrar('panel', 'usuario.activado' if obj.is_active else 'usuario.suspendido', referencia=obj.pk, detalle=motivo)
    messages.success(request, 'Estado del usuario actualizado.')
    return redirect('panel:usuario', pk=pk)


@privado()
def organizaciones(request):
    qs = buscar(request, Tenant.objects.select_related('propietario').annotate(total_manuales=Count('manuales', distinct=True), total_cuentas=Count('cuentas', distinct=True)).order_by('nombre', 'pk'), ['nombre', 'propietario__email', 'propietario__username'])
    return render(request, 'panel/organizaciones.html', {'titulo': 'Organizaciones', 'organizaciones': pagina(request, qs)})


@privado('propietario')
@require_POST
def estado_organizacion(request, pk):
    motivo = request.POST.get('motivo', '').strip()[:300]
    if motivo:
        with transaction.atomic():
            obj = get_object_or_404(Tenant.objects.select_for_update(), pk=pk)
            obj.activo = not obj.activo
            obj.save(update_fields=['activo'])
            registrar('panel', 'organizacion.activada' if obj.activo else 'organizacion.suspendida', referencia=obj.pk,
                      organizacion_id=obj.pk, detalle=motivo)
        messages.success(request, 'Estado de la organización actualizado.')
    else:
        messages.error(request, 'Escribe el motivo antes de confirmar.')
    return redirect('panel:organizaciones')


@privado()
def inteligencia(request):
    desde = timezone.now()-timedelta(days=30)
    qs = UsoIA.objects.filter(fecha__gte=desde)
    return render(request, 'panel/inteligencia.html', {'titulo': 'Inteligencia y consumo',
                  'totales': qs.aggregate(tokens=Sum('tokens_total'), entrada=Sum('tokens_entrada'), salida=Sum('tokens_salida'), intentos=Count('pk'), exito=Count('pk', filter=Q(manual_generado=True))),
                  'usos': pagina(request, qs.select_related('usuario', 'tenant')), 'proveedor': settings.AI_PROVIDER,
                  'respaldo': settings.AI_FALLBACK_PROVIDER,
                  'por_usuario': qs.values('usuario__username').annotate(total=Sum('tokens_total'), n=Count('pk')).order_by('-total')[:10],
                  'parciales': qs.filter(Q(total_parcial=True) | Q(tokens_total__isnull=True)).count()})


@privado()
def donativos(request):
    qs = Donativo.objects.all()
    return render(request, 'panel/donativos.html', {'titulo': 'Donativos', 'donativos': pagina(request, qs),
                  'total': qs.filter(estado__in=['aprobado', 'parcial']).aggregate(n=Sum(Coalesce('monto_confirmado', F('monto') - F('monto_reembolsado'))))['n'] or 0,
                  'pendientes': qs.filter(estado='pendiente').count()})


@privado()
def oportunidades(request):
    return render(request, 'panel/oportunidades.html', {'titulo': 'Radar de oportunidades', 'grupos': radar()})


@privado('propietario')
@require_http_methods(['GET', 'POST'])
def controles(request):
    obj, _ = ControlPlataforma.objects.get_or_create(pk=1)
    form = ControlForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            form.save()
            registrar('panel', 'controles.actualizados', detalle=form.cleaned_data['motivo'])
        messages.success(request, 'Configuración actualizada.')
        return redirect('panel:controles')
    return render(request, 'panel/form.html', {'titulo': 'Control de la plataforma', 'form': form,
                  'descripcion': 'Publica un aviso o pausa nuevas generaciones. Las solicitudes de IA ya iniciadas pueden terminar. El límite cuenta solicitudes diarias por usuario, incluidas las fallidas.'})


@privado('propietario', 'soporte', 'consulta')
def salud(request):
    inicio = time.monotonic()
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        cursor.fetchone()
    return render(request, 'panel/salud.html', {'titulo': 'Estado operativo', 'latencia': round((time.monotonic()-inicio)*1000, 1),
                  'errores': Evento.objects.filter(fecha__gte=timezone.now()-timedelta(hours=24), estado_http__gte=500).count(),
                  'ultimo': Evento.objects.exclude(categoria='panel').first(), 'proveedor': settings.AI_PROVIDER,
                  'ia_configurada': bool(settings.DEEPSEEK_API_KEY if settings.AI_PROVIDER == 'deepseek' else settings.OPENAI_API_KEY),
                  'smtp': bool(getattr(settings, 'EMAIL_HOST_USER', '')), 'pagos': bool(settings.MERCADOPAGO_ACCESS_TOKEN)})
