import logging
import secrets
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.db import transaction
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.csrf import csrf_failure as default_csrf_failure
from django.http import HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme
from urllib.parse import urlencode
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.forms import SetPasswordForm
from .forms import RegistroUsuarioForm, LoginForm, TenantForm, PerfilCPCForm, RegistrarColegaForm
from .models import Tenant, MembresiaTenant, PerfilCPC, InvitacionAcceso

logger = logging.getLogger(__name__)


def landing(request):
    """Página de inicio: si está autenticado va al dashboard, si no al landing."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'cuentas/landing.html')


@never_cache
@sensitive_post_parameters('password', 'password_confirm')
@transaction.atomic
def registro_view(request):
    """Registro de nuevo usuario + perfil CPC."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='cuentas.backends.EmailOrUsernameBackend')
            logger.info(f"Nuevo usuario registrado: {user.email}")
            messages.success(request, '¡Bienvenido! Ahora crea tu primera organización.')
            return redirect('crear_tenant')
    else:
        form = RegistroUsuarioForm()

    return render(request, 'cuentas/registro.html', {'form': form})


def safe_login_next(request):
    target = request.GET.get('next', '')
    return target if url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ) else ''


@never_cache
def csrf_failure(request, reason=''):
    """Un formulario obsoleto se vuelve a abrir; nunca se procesa el POST rechazado."""
    if (request.method == 'POST' and request.path == reverse('registro')
            and reason.startswith(('CSRF cookie', 'CSRF token'))):
        messages.warning(request, 'El formulario de registro se desactualizó. Completa de nuevo tus datos para crear la cuenta.')
        return HttpResponseRedirect(reverse('registro'), status=303)
    if (request.method == 'POST' and request.path == reverse('login')
            and reason.startswith(('CSRF cookie', 'CSRF token'))):
        messages.warning(request, 'El formulario de acceso se desactualizó. Vuelve a introducir tus datos para iniciar sesión.')
        target = reverse('login')
        next_url = safe_login_next(request)
        if next_url:
            target += '?' + urlencode({'next': next_url})
        return HttpResponseRedirect(target, status=303)
    return default_csrf_failure(request, reason=reason)


@never_cache
@sensitive_post_parameters('password')
def login_view(request):
    """Inicio de sesión."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            logger.info(f"Login: {user.email}")

            # Auto-seleccionar primer tenant si existe
            primera_membresia = MembresiaTenant.objects.filter(
                usuario=user, tenant__activo=True
            ).select_related('tenant').first()
            if primera_membresia:
                request.session['tenant_id'] = primera_membresia.tenant.id

            next_url = safe_login_next(request) or 'dashboard'
            return redirect(next_url)
    else:
        form = LoginForm()

    return render(request, 'cuentas/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión.')
    return redirect('landing')


@login_required
def dashboard(request):
    """Dashboard principal del tenant activo."""
    tenant = getattr(request, 'tenant', None)
    context = {}

    if tenant:
        from catalogo.models import CatalogoCuentas, ManualContable
        context['total_cuentas'] = CatalogoCuentas.objects.filter(tenant=tenant).count()
        context['total_manuales'] = ManualContable.objects.filter(tenant=tenant).count()
        context['manuales_pendientes'] = ManualContable.objects.filter(tenant=tenant, aprobado=False).count()
        context['manuales_recientes'] = ManualContable.objects.filter(tenant=tenant).select_related('creado_por').prefetch_related('cuentas', 'codigos_sat').order_by('-fecha_creacion')[:5]

    from catalogo.consumo_ia import resumen_uso
    context['resumen_ia'] = resumen_uso(request.user)

    context['mis_tenants'] = Tenant.objects.filter(
        membresias__usuario=request.user, activo=True
    ).distinct()

    return render(request, 'cuentas/dashboard.html', context)


@login_required
def perfil_view(request):
    """Editar perfil CPC."""
    perfil, created = PerfilCPC.objects.get_or_create(
        usuario=request.user,
        defaults={'nombre_completo': request.user.get_full_name() or request.user.username,
                  'ciudad': '', 'estado': 'CDMX'}
    )

    if request.method == 'POST':
        form = PerfilCPCForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('perfil')
    else:
        form = PerfilCPCForm(instance=perfil)

    return render(request, 'cuentas/perfil.html', {'form': form, 'perfil': perfil})


@login_required
def lista_tenants(request):
    """Listar organizaciones del usuario."""
    membresias = MembresiaTenant.objects.filter(
        usuario=request.user, tenant__activo=True
    ).select_related('tenant').order_by('tenant__nombre')

    return render(request, 'cuentas/lista_tenants.html', {'membresias': membresias})


@login_required
def crear_tenant(request):
    """Crear nueva organización."""
    if request.method == 'POST':
        form = TenantForm(request.POST)
        if form.is_valid():
            tenant = form.save(commit=False)
            tenant.propietario = request.user
            tenant.save()

            # Crear membresía como propietario
            MembresiaTenant.objects.create(
                tenant=tenant, usuario=request.user, rol='propietario'
            )

            # Seleccionar como tenant activo
            request.session['tenant_id'] = tenant.id

            logger.info(f"Nuevo tenant creado: {tenant.nombre} por {request.user.email}")
            messages.success(request, f'Organización "{tenant.nombre}" creada exitosamente.')
            return redirect('dashboard')
    else:
        form = TenantForm()

    return render(request, 'cuentas/crear_tenant.html', {'form': form})


@login_required
def equipo_tenant(request, pk):
    """Gestión de equipo de una organización."""
    tenant = get_object_or_404(Tenant, pk=pk)
    membresia_actual = get_object_or_404(MembresiaTenant, tenant=tenant, usuario=request.user)

    if membresia_actual.rol not in ('propietario', 'contador'):
        messages.error(request, 'No tienes permisos para gestionar el equipo de esta organización.')
        return redirect('dashboard')

    membresias = tenant.membresias.all().select_related('usuario', 'usuario__perfil_cpc')

    return render(request, 'cuentas/equipo.html', {
        'tenant': tenant,
        'membresias': membresias,
        'es_propietario': membresia_actual.rol == 'propietario'
    })


@login_required
def editar_tenant(request, pk):
    """Editar organización."""
    tenant = get_object_or_404(Tenant, pk=pk)
    membresia = get_object_or_404(MembresiaTenant, tenant=tenant, usuario=request.user)

    if membresia.rol not in ('propietario', 'contador'):
        messages.error(request, 'No tienes permisos para editar esta organización.')
        return redirect('lista_tenants')

    if request.method == 'POST':
        form = TenantForm(request.POST, instance=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Organización actualizada.')
            return redirect('lista_tenants')
    else:
        form = TenantForm(instance=tenant)

    return render(request, 'cuentas/editar_tenant.html', {'form': form, 'tenant': tenant})


@login_required
def seleccionar_tenant(request, pk):
    """Cambiar el tenant activo en la sesión."""
    membresia = get_object_or_404(
        MembresiaTenant, tenant_id=pk, usuario=request.user, tenant__activo=True
    )
    request.session['tenant_id'] = membresia.tenant.id
    messages.info(request, f'Cambiaste a "{membresia.tenant.nombre}".')
    return redirect('dashboard')

def _crear_invitacion_acceso(usuario, tenant, rol, creado_por):
    InvitacionAcceso.objects.filter(usuario=usuario, usado_en__isnull=True).update(usado_en=timezone.now())
    token = secrets.token_urlsafe(48)
    return InvitacionAcceso.objects.create(
        token=token,
        usuario=usuario,
        tenant=tenant,
        rol=rol,
        creado_por=creado_por,
        expira_en=timezone.now() + timedelta(hours=24),
    )


def enviar_correo_invitacion(usuario, tenant, rol, invitation_url=None):
    """Envía un correo electrónico notificando la invitación."""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    from django.conf import settings

    rol_display = dict(MembresiaTenant.ROL_CHOICES).get(rol, rol)
    site_url = "https://manualcontable.online" if not settings.DEBUG else "http://localhost:8000"

    context = {
        'usuario': usuario,
        'tenant': tenant,
        'rol_display': rol_display,
        'site_url': site_url,
        'invitation_url': invitation_url,
    }

    html_message = render_to_string('emails/invitacion_miembro.html', context)
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject=f'Invitación a colaborar en {tenant.nombre}',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger('cuentas')
        logger.error(f"Error al enviar correo de invitación a {usuario.email}: {e}")
        return False


@login_required
@require_POST
def registrar_usuario(request, tenant_pk):
    """
    Registra directamente a un colega en la organización.
    Genera un enlace temporal de establecimiento de contraseña por correo.
    """
    tenant = get_object_or_404(Tenant, pk=tenant_pk)
    # Verificar permisos: Propietario o Contador
    membresia = get_object_or_404(MembresiaTenant, tenant=tenant, usuario=request.user)
    if membresia.rol not in ['propietario', 'contador']:
        messages.error(request, 'No tienes permisos para registrar nuevos miembros.')
        return redirect('equipo_tenant', pk=tenant_pk)

    form = RegistrarColegaForm(request.POST)

    if form.is_valid():
        email = form.cleaned_data['email']
        nombre = form.cleaned_data['nombre']
        rol = form.cleaned_data['rol']

        from django.contrib.auth.models import User
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': nombre.split()[0],
                'last_name': ' '.join(nombre.split()[1:]) if len(nombre.split()) > 1 else '',
            }
        )

        if created:
            user.set_unusable_password()
            user.save()
            # Crear perfil CPC básico
            PerfilCPC.objects.create(
                usuario=user,
                nombre_completo=nombre,
                ciudad='',
                estado='CDMX'
            )
            logger.info(f"Nuevo colega registrado: {email} por {request.user.email}")
        else:
            logger.info(f"Usuario existente {email} vinculado a tenant {tenant.nombre}")

        # Crear membresía si no existe o actualizar rol si ya existe (opcional, aquí solo creamos)
        membresia, m_created = MembresiaTenant.objects.get_or_create(
            tenant=tenant,
            usuario=user,
            defaults={'rol': rol}
        )

        if m_created:
            if not created:
                messages.success(request, f'El usuario {email} ya existía y ha sido añadido a tu equipo.')
        else:
            messages.warning(request, f'El usuario {email} ya es parte de tu equipo.')

        invitacion = _crear_invitacion_acceso(
            usuario=user,
            tenant=tenant,
            rol=rol,
            creado_por=request.user,
        )
        invitation_url = request.build_absolute_uri(
            reverse('establecer_password_invitacion', args=[invitacion.token])
        )
        email_ok = enviar_correo_invitacion(user, tenant, rol, invitation_url=invitation_url)

        if email_ok:
            messages.success(request, f'Se envió un enlace de acceso seguro a {email}. El enlace vence en 24 horas.')
        else:
            messages.warning(request, f'No se pudo enviar el correo a {email}. Verifica la configuración SMTP.')

    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")

    return redirect('equipo_tenant', pk=tenant_pk)


@require_http_methods(["GET", "POST"])
def establecer_password_invitacion(request, token):
    """Permite establecer contraseña mediante token de invitación temporal."""
    invitacion = get_object_or_404(InvitacionAcceso, token=token)

    if not invitacion.esta_vigente:
        messages.error(request, 'El enlace de invitación expiró o ya fue utilizado.')
        return redirect('login')

    form = SetPasswordForm(user=invitacion.usuario, data=request.POST or None)
    for field in form.fields.values():
        field.widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-500 outline-none transition'
        })

    if request.method == 'POST' and form.is_valid():
        form.save()
        invitacion.usado_en = timezone.now()
        invitacion.save(update_fields=['usado_en'])
        messages.success(request, 'Contraseña establecida correctamente. Ahora puedes iniciar sesión.')
        return redirect('login')

    return render(request, 'cuentas/establecer_password_invitacion.html', {
        'form': form,
        'invitacion': invitacion,
    })


@login_required
@require_POST
def eliminar_miembro(request, tenant_pk, membresia_pk):
    """Eliminar un miembro de la organización."""
    tenant = get_object_or_404(Tenant, pk=tenant_pk)
    # Solo el propietario puede eliminar miembros
    get_object_or_404(MembresiaTenant, tenant=tenant, usuario=request.user, rol='propietario')

    membresia = get_object_or_404(MembresiaTenant, pk=membresia_pk, tenant=tenant)

    if membresia.rol == 'propietario':
        messages.error(request, 'No se puede eliminar al propietario original.')
    else:
        email = membresia.usuario.email
        membresia.delete()
        messages.success(request, f'Se ha eliminado a {email} de la organización.')

    return redirect('equipo_tenant', pk=tenant.pk)
