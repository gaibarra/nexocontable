from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core import signing
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from .models import IdentidadDespacho, PresentacionEmpresa, LogoDocumento, Tenant, MembresiaTenant
from .marca_forms import IdentidadDespachoForm, PresentacionEmpresaForm
from catalogo.presentacion import construir_presentacion, contexto_presentacion


def puede_personalizar(usuario, tenant):
    return tenant.propietario_id == usuario.pk or MembresiaTenant.objects.filter(
        tenant=tenant, usuario=usuario, rol__in=['propietario', 'contador']).exists()


def _preparar_logo(form, usuario, titular, tenant=None):
    """La vista previa conserva el archivo sin publicar todavía la configuración."""
    obj = form.instance
    archivo = form.cleaned_data.get('archivo_logo')
    token = form.cleaned_data.get('logo_previo')
    if form.cleaned_data.get('quitar_logo'):
        obj.logo = None
        return ''
    if archivo:
        logo = LogoDocumento(propietario=titular, organizacion=tenant, ambito='empresa' if tenant else 'despacho')
        logo.imagen.save(archivo.name, archivo, save=True)
        obj.logo = logo
        return signing.dumps({'logo': str(logo.pk), 'usuario': usuario.pk,
                              'empresa': tenant.pk if tenant else None}, salt='logo-preview')
    if token:
        try:
            datos = signing.loads(token, salt='logo-preview', max_age=86400)
            if datos['usuario'] != usuario.pk or datos['empresa'] != (tenant.pk if tenant else None):
                raise signing.BadSignature
            obj.logo = LogoDocumento.objects.get(pk=datos['logo'], propietario=titular, organizacion=tenant)
        except (signing.BadSignature, KeyError, ValueError, LogoDocumento.DoesNotExist):
            form.add_error('archivo_logo', 'La vista previa del logo expiró o no es válida. Vuelve a seleccionar la imagen.')
            return None
    return token or ''


def _guardar(form, titular, tenant=None):
    with transaction.atomic():
        if tenant:
            Tenant.objects.select_for_update().get(pk=tenant.pk)
            existente = PresentacionEmpresa.objects.filter(organizacion=tenant).first()
        else:
            User.objects.select_for_update().get(pk=titular.pk)
            existente = IdentidadDespacho.objects.filter(titular=titular).first()
        obj = form.instance
        if existente and not obj.pk:
            obj.pk = existente.pk
        obj.save()
        return obj


def _form_con_logo(form, token):
    datos = form.data.copy()
    datos['logo_previo'] = token
    return type(form)(datos, instance=form.instance)


@login_required
@require_http_methods(['GET', 'POST'])
@never_cache
def mi_despacho(request):
    identidad = IdentidadDespacho.objects.filter(titular=request.user).first() or IdentidadDespacho(titular=request.user)
    form = IdentidadDespachoForm(request.POST or None, request.FILES or None, instance=identidad)
    preview = None
    ejemplo = Tenant.objects.filter(propietario=request.user, activo=True).first() or Tenant(
        nombre='Empresa de tu cliente', propietario=request.user)
    if request.method == 'POST' and form.is_valid():
        identidad = form.save(commit=False)
        token = _preparar_logo(form, request.user, request.user)
        preview = contexto_presentacion(construir_presentacion(ejemplo, despacho=identidad))
        if token is not None and request.POST.get('accion') == 'guardar':
            _guardar(form, request.user)
            messages.success(request, 'La identidad de tu despacho está guardada. Los manuales aprobados conservan su presentación.')
            return redirect('mi_despacho')
        if token is not None:
            form = _form_con_logo(form, token)
    if preview is None:
        preview = contexto_presentacion(construir_presentacion(ejemplo, despacho=identidad))
    return render(request, 'cuentas/presentacion_marca.html', {
        'form': form, 'presentacion': preview, 'es_despacho': True,
        'logo_actual': identidad.logo_id, 'titulo': 'Mi despacho',
        'vista_previa': request.method == 'POST' and not form.errors,
    })


@login_required
@require_http_methods(['GET', 'POST'])
@never_cache
def presentacion_empresa(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk, activo=True)
    if not puede_personalizar(request.user, tenant):
        raise PermissionDenied
    configuracion = PresentacionEmpresa.objects.filter(organizacion=tenant).first() or PresentacionEmpresa(organizacion=tenant)
    form = PresentacionEmpresaForm(request.POST or None, request.FILES or None, instance=configuracion)
    preview = None
    if request.method == 'POST' and form.is_valid():
        configuracion = form.save(commit=False)
        token = _preparar_logo(form, request.user, tenant.propietario, tenant)
        preview = contexto_presentacion(construir_presentacion(tenant, empresa=configuracion))
        if token is not None and request.POST.get('accion') == 'guardar':
            _guardar(form, tenant.propietario, tenant)
            messages.success(request, 'Presentación guardada. Los borradores usarán estos datos; los aprobados mantienen su encabezado.')
            return redirect('presentacion_empresa', pk=tenant.pk)
        if token is not None:
            form = _form_con_logo(form, token)
    if preview is None:
        preview = contexto_presentacion(construir_presentacion(tenant, empresa=configuracion))
    return render(request, 'cuentas/presentacion_marca.html', {
        'form': form, 'presentacion': preview, 'empresa': tenant,
        'logo_actual': configuracion.logo_id, 'titulo': 'Presentación de la empresa',
        'vista_previa': request.method == 'POST' and not form.errors,
    })


@login_required
@require_http_methods(['GET'])
@never_cache
def logo_documento(request, pk):
    logo = get_object_or_404(LogoDocumento, pk=pk)
    autorizado = logo.propietario_id == request.user.pk
    if logo.organizacion_id:
        autorizado |= MembresiaTenant.objects.filter(usuario=request.user, tenant_id=logo.organizacion_id,
                                                      tenant__activo=True).exists()
    elif logo.ambito == 'despacho' and logo.propietario_id:
        autorizado |= MembresiaTenant.objects.filter(usuario=request.user, tenant__propietario_id=logo.propietario_id,
                                                      tenant__activo=True).exists()
    if not autorizado:
        raise Http404
    try:
        response = FileResponse(logo.imagen.open('rb'), content_type='image/jpeg' if logo.imagen.name.endswith('.jpg') else 'image/png')
    except (FileNotFoundError, OSError):
        raise Http404
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
