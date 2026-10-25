"""Acciones del panel: campos explícitos, permisos, auditoría y borrado confirmado."""
import hashlib
import json
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core import signing
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models.deletion import Collector, ProtectedError, RestrictedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods
from cuentas.models import Tenant, PerfilCPC, MembresiaTenant
from catalogo.models import UsoIA
from donaciones.models import Donativo
from .audit import registrar
from .crud_forms import (UsuarioCrearForm, UsuarioEditarForm, OrganizacionForm,
                         NotaForm, SeguimientoForm, DonativoManualForm, ConfirmarEliminarForm)
from .forms import ContactoForm
from .models import AccesoPanel, Contacto, Nota, Tarea, Evento
from .security import privado

User = get_user_model()
REGISTROS = {
    'usuario': (User, 'Usuario', 'usuarios', ('propietario',), UsuarioCrearForm, UsuarioEditarForm),
    'organizacion': (Tenant, 'Organización', 'organizaciones', ('propietario',), OrganizacionForm, OrganizacionForm),
    'contacto': (Contacto, 'Contacto', 'crm', ('propietario', 'comercial'), ContactoForm, ContactoForm),
    'nota': (Nota, 'Nota', 'crm', ('propietario', 'comercial'), NotaForm, NotaForm),
    'tarea': (Tarea, 'Seguimiento', 'crm', ('propietario', 'comercial'), SeguimientoForm, SeguimientoForm),
    'donativo': (Donativo, 'Donativo manual', 'donativos', ('propietario',), DonativoManualForm, DonativoManualForm),
    'evento': (Evento, 'Evento de actividad', 'actividad', (), None, None),
    'consumo': (UsoIA, 'Consumo de IA', 'inteligencia', (), None, None),
}


def configuracion(tipo):
    if tipo not in REGISTROS:
        raise Http404
    return REGISTROS[tipo]


def es_pago_externo(obj):
    return bool(obj.referencia_mp or obj.preference_id or obj.datos_webhook)


def protegido(tipo, obj, user):
    if tipo == 'usuario' and (obj.pk == user.pk or obj.is_superuser or obj.is_staff or AccesoPanel.objects.filter(usuario=obj).exists()):
        return 'Esta cuenta administrativa está protegida. Sus permisos y credenciales se gestionan desde el servidor.'
    if tipo == 'donativo' and es_pago_externo(obj):
        return 'Este registro pertenece a Mercado Pago. Sus datos y estado se conservan conforme al proveedor.'
    return ''


def comprobar_escritura(request, tipo, obj=None):
    config = configuracion(tipo)
    if request.user.acceso_panel.rol not in config[3] or not config[4]:
        raise PermissionDenied
    if obj and protegido(tipo, obj, request.user):
        raise PermissionDenied(protegido(tipo, obj, request.user))
    return config


def retorno(tipo, obj=None):
    if tipo in ('nota', 'tarea') and obj is not None:
        return reverse('panel:contacto', args=[obj.contacto_id])
    return reverse('panel:' + configuracion(tipo)[2])


def detalle_url(tipo, obj):
    if tipo == 'usuario':
        return reverse('panel:usuario', args=[obj.pk])
    if tipo == 'contacto':
        return reverse('panel:contacto', args=[obj.pk])
    return reverse('panel:registro_ver', args=[tipo, obj.pk])


def firma_borrado(obj):
    collector = Collector(using='default')
    collector.collect([obj])
    ids = {}
    for model, objects in collector.data.items():
        ids[model._meta.label_lower] = sorted(item.pk for item in objects)
    for qs in collector.fast_deletes:
        ids.setdefault(qs.model._meta.label_lower, []).extend(qs.values_list('pk', flat=True))
    ids = {key: sorted(value) for key, value in ids.items()}
    fingerprint = hashlib.sha256(json.dumps(ids, sort_keys=True, default=str).encode()).hexdigest()
    resumen = [(key, len(value)) for key, value in ids.items() if value]
    return fingerprint, resumen


@privado()
@sensitive_post_parameters('password1', 'password2')
@require_http_methods(['GET', 'POST'])
def formulario(request, tipo, pk=None):
    config = configuracion(tipo)
    model = config[0]
    # Notas y tareas se crean desde su contacto para conservar el contexto.
    if tipo in ('nota', 'tarea') and pk is None:
        raise Http404
    obj = get_object_or_404(model, pk=pk) if pk else None
    owner_before = getattr(obj, 'propietario_id', None)
    comprobar_escritura(request, tipo, obj)
    form_class = config[5] if obj else config[4]
    form = form_class(request.POST if request.method == 'POST' else None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                if obj:
                    locked = model.objects.select_for_update().get(pk=obj.pk)
                    comprobar_escritura(request, tipo, locked)
                    owner_before = getattr(locked, 'propietario_id', None)
                    # Revalidar contra el registro vigente dentro de la transacción.
                    form = form_class(request.POST, instance=locked)
                    if not form.is_valid():
                        return render(request, 'panel/form.html', {'titulo': 'Editar ' + config[1], 'form': form, 'volver': retorno(tipo, obj)})
                anterior = dict((f.name, str(getattr(form.instance, f.attname))) for f in model._meta.fields
                                if f.name in form._meta.fields and f.name not in ('password',)) if pk else {}
                saved = form.save(commit=False)
                if tipo == 'usuario':
                    saved.save()
                    PerfilCPC.objects.update_or_create(usuario=saved, defaults={
                        'nombre_completo': saved.get_full_name() or saved.username,
                        'ciudad': form.cleaned_data.get('ciudad', ''), 'estado': form.cleaned_data.get('estado', ''),
                        'telefono': form.cleaned_data.get('telefono', '')})
                elif tipo == 'organizacion':
                    old_owner = owner_before
                    saved.save()
                    if old_owner and old_owner != saved.propietario_id:
                        MembresiaTenant.objects.filter(tenant=saved, usuario_id=old_owner, rol='propietario').update(rol='contador')
                    MembresiaTenant.objects.update_or_create(tenant=saved, usuario=saved.propietario, defaults={'rol': 'propietario'})
                elif tipo == 'contacto':
                    if not saved.usuario_id:
                        users = User.objects.filter(email__iexact=saved.email)
                        if users.count() == 1 and not Contacto.objects.filter(usuario=users.first()).exclude(pk=saved.pk).exists():
                            saved.usuario = users.first()
                    saved.save()
                else:
                    saved.save()
                cambios = ', '.join(form.changed_data)
                detalle = f'Campos: {cambios}'
                if tipo == 'donativo':
                    detalle += f'; anterior: {json.dumps(anterior, ensure_ascii=False)}; monto: {saved.monto}; estado: {saved.estado}'
                registrar('crm' if tipo in ('contacto', 'nota', 'tarea') else 'panel',
                          f'{tipo}.editado' if pk else f'{tipo}.creado', actor=request.user.pk,
                          referencia=saved.pk, organizacion_id=saved.pk if tipo == 'organizacion' else None, detalle=detalle)
            messages.success(request, config[1] + ' guardado correctamente.')
            return redirect(detalle_url(tipo, saved))
        except IntegrityError:
            form.add_error(None, 'No se pudo guardar: un dato único ya existe o cambió una relación. Revisa el formulario.')
    descripcion = 'Registro manual: no crea cobros ni realiza devoluciones en Mercado Pago.' if tipo == 'donativo' else ''
    return render(request, 'panel/form.html', {'titulo': ('Editar ' if pk else 'Crear ') + config[1],
                  'form': form, 'descripcion': descripcion, 'volver': retorno(tipo, obj)})


@privado()
@require_http_methods(['GET', 'POST'])
def eliminar(request, tipo, pk):
    config = configuracion(tipo)
    obj = get_object_or_404(config[0], pk=pk)
    comprobar_escritura(request, tipo, obj)
    volver = retorno(tipo, obj)
    texto = f'ELIMINAR #{obj.pk}'
    form = ConfirmarEliminarForm(request.POST if request.method == 'POST' else None)
    resumen, bloqueado = [], ''
    try:
        fingerprint, resumen = firma_borrado(obj)
    except (ProtectedError, RestrictedError):
        fingerprint = ''
        bloqueado = 'El registro tiene documentos o relaciones protegidas. No puede eliminarse; revisa sus dependencias.'
    if request.method == 'POST' and form.is_valid() and not bloqueado:
        try:
            token = signing.loads(form.cleaned_data['token'], salt='panel-eliminar', max_age=900)
            if token != {'tipo': tipo, 'pk': pk, 'actor': request.user.pk, 'firma': fingerprint}:
                raise signing.BadSignature
            if form.cleaned_data['confirmacion'].strip() != texto:
                form.add_error('confirmacion', f'Escribe exactamente {texto}.')
            else:
                with transaction.atomic():
                    obj = get_object_or_404(config[0].objects.select_for_update(), pk=pk)
                    comprobar_escritura(request, tipo, obj)
                    actual, _ = firma_borrado(obj)
                    if actual != fingerprint:
                        raise signing.BadSignature
                    label = str(obj)[:120]
                    obj.delete()
                    registrar('crm' if tipo in ('contacto', 'nota', 'tarea') else 'panel', f'{tipo}.eliminado',
                              actor=request.user.pk, referencia=pk, detalle=f'{label}; motivo: {form.cleaned_data["motivo"]}')
                messages.success(request, config[1] + ' eliminado correctamente.')
                return redirect(volver)
        except signing.BadSignature:
            form.add_error(None, 'La confirmación caducó o cambiaron los registros afectados. Revisa el resumen y confirma de nuevo.')
        except (ProtectedError, RestrictedError, IntegrityError):
            form.add_error(None, 'No se eliminó el registro porque sus relaciones están protegidas o cambiaron. Revisa sus dependencias.')
    token = signing.dumps({'tipo': tipo, 'pk': pk, 'actor': request.user.pk, 'firma': fingerprint}, salt='panel-eliminar')
    if request.method == 'POST':
        data = form.data.copy(); data['token'] = token; form.data = data
    else:
        form.initial['token'] = token
    advertencia = ('Se eliminarán también los registros relacionados que aparecen abajo. Esta acción es permanente.'
                   if tipo in ('usuario', 'organizacion') else
                   'Se eliminará este registro y sus dependencias indicadas. El usuario vinculado y la auditoría se conservan.')
    return render(request, 'panel/eliminar.html', {'titulo': 'Eliminar ' + config[1], 'objeto': obj,
                  'tipo': tipo, 'form': form, 'resumen': resumen, 'bloqueado': bloqueado,
                  'texto_confirmacion': texto, 'volver': volver, 'advertencia': advertencia})


@privado()
def ver(request, tipo, pk):
    config = configuracion(tipo)
    obj = get_object_or_404(config[0], pk=pk)
    if tipo in ('usuario', 'contacto'):
        return redirect(detalle_url(tipo, obj))
    campos = {
        'organizacion': ['nombre', 'propietario', 'rfc', 'giro', 'regimen_fiscal', 'ciudad', 'estado', 'telefono', 'activo', 'fecha_creacion'],
        'nota': ['texto', 'autor', 'fecha', 'contacto'],
        'tarea': ['titulo', 'contacto', 'responsable', 'vence', 'completada'],
        'donativo': ['nombre_donante', 'email_donante', 'monto', 'estado', 'fecha', 'referencia_mp'],
        'evento': ['fecha', 'actor', 'categoria', 'accion', 'referencia', 'organizacion_id', 'detalle', 'estado_http', 'duracion_ms'],
        'consumo': ['fecha', 'usuario', 'tenant', 'tokens_entrada', 'tokens_salida', 'tokens_total', 'total_parcial', 'manual_generado'],
    }
    fields = []
    for name in campos[tipo]:
        field = obj._meta.get_field(name)
        value = getattr(obj, 'get_' + name + '_display', lambda: getattr(obj, name))()
        if isinstance(value, bool):
            value = 'Sí' if value else 'No'
        fields.append((str(field.verbose_name).capitalize(), value if value is not None and value != '' else '—'))
    return render(request, 'panel/registro.html', {'titulo': config[1] + f' #{pk}', 'campos': fields,
                  'tipo': tipo, 'registro': obj, 'volver': retorno(tipo, obj),
                  'editable': request.user.acceso_panel.rol in config[3] and not protegido(tipo, obj, request.user),
                  'solo_lectura': tipo in ('evento', 'consumo') or (tipo == 'donativo' and es_pago_externo(obj))})
