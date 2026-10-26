import logging
from types import SimpleNamespace
from .sat import asegurar_catalogo_sat
from .forms import ImportarCatalogoForm
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponsePermanentRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST, require_http_methods
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.db import transaction
from django.db.models import Q, Count
from django.template.loader import render_to_string
from django.utils.text import slugify
from django.urls import reverse
from cuentas.models import Tenant
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied

from .models import CatalogoCuentas, ManualContable, CodigoAgrupador, CatalogoPlantilla, CatalogoPlantillaCuenta
from .consumo_ia import registrar_uso, resumen_uso, reporte_uso
from .models import UsoIA, CambioPresentacionManual
from .presentacion import construir_presentacion, contexto_presentacion, datos_manual
from .documento_word import generar_docx
from .composicion_documento import componer_manual
from cuentas.marca_views import puede_personalizar
from django.core import signing
import hashlib
import json
from .prompts import build_manual_prompts
from .ia import generar_texto, ManualGenerationError
from .forms import CatalogoPlantillaForm, CatalogoPlantillaCuentaFormSet
from .importador import importar_csv, importar_excel, generar_plantilla_csv, obtener_plantilla_catalogo

logger = logging.getLogger(__name__)

# =========================================
# Catálogo de cuentas
# =========================================

@login_required
def catalogo_cuentas(request):
    """Lista el catálogo de cuentas del tenant activo."""
    tenant = request.tenant
    if not tenant:
        return redirect('lista_tenants')

    if request.method == 'POST':
        return confirmar_relacion(request, request.POST.get('cuenta_id'))

    asegurar_catalogo_sat()
    cuentas = CatalogoCuentas.objects.filter(tenant=tenant).select_related('codigoagrupador').order_by('cuenta')

    # Búsqueda
    busqueda = request.GET.get('q', '').strip()
    if busqueda:
        cuentas = cuentas.filter(
            Q(cuenta__icontains=busqueda) |
            Q(descripcion__icontains=busqueda) |
            Q(codigoagrupador__codigoagrupador__icontains=busqueda)
        )

    pagina = Paginator(cuentas, 25).get_page(request.GET.get('page'))
    return render(request, 'catalogo/catalogo_cuentas.html', {
        'cuentas': pagina,
        'busqueda': busqueda,
        'total': pagina.paginator.count,
        'codigos_sat': CodigoAgrupador.objects.all(),
    })

@login_required
@require_POST
def confirmar_relacion(request, pk):
    """Confirma una sola relación; las peticiones AJAX reciben solo esa cuenta."""
    ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    def error(mensaje, status):
        if ajax:
            return JsonResponse({'ok': False, 'message': mensaje}, status=status)
        if status == 404:
            from django.http import Http404
            raise Http404(mensaje)
        messages.error(request, mensaje)
        return redirect('catalogo_cuentas')

    if not request.tenant:
        return error('Selecciona una organización antes de confirmar la vinculación.', 400)
    try:
        cuenta_id = int(pk)
    except (TypeError, ValueError):
        return error('La cuenta indicada no es válida.', 400)
    cuenta = CatalogoCuentas.objects.filter(pk=cuenta_id, tenant=request.tenant).first()
    if cuenta is None:
        return error('La cuenta no está disponible en esta organización.', 404)
    codigo_valor = request.POST.get('codigoagrupador', '').strip()
    if not codigo_valor:
        return error('Selecciona un código del catálogo SAT antes de confirmar.', 400)
    codigo = CodigoAgrupador.objects.filter(codigoagrupador=codigo_valor).first()
    if codigo is None:
        return error('El código seleccionado no existe en el catálogo SAT.', 400)
    cuenta.codigoagrupador = codigo
    cuenta.relacion_sugerida = False
    cuenta.confianza_relacion = None
    cuenta.save(update_fields=['codigoagrupador', 'relacion_sugerida', 'confianza_relacion'])
    if ajax:
        return JsonResponse({
            'ok': True,
            'message': f'Cuenta {cuenta.cuenta} vinculada al código SAT {codigo.codigoagrupador}.',
            'cuenta': {
                'id': cuenta.pk, 'codigoagrupador': codigo.codigoagrupador,
                'nombre_sat': codigo.nombre,
            },
        })
    messages.success(request, 'Relación SAT confirmada.')
    return redirect('catalogo_cuentas')


@login_required
def agregar_cuenta(request):
    """Agregar una cuenta individual al catálogo del tenant."""
    tenant = request.tenant
    if not tenant:
        return redirect('lista_tenants')

    asegurar_catalogo_sat()
    cuentas = CatalogoCuentas.objects.filter(tenant=tenant).select_related('codigoagrupador').order_by('cuenta')
    busqueda = request.GET.get('q', '').strip()
    if busqueda:
        cuentas = cuentas.filter(
            Q(cuenta__icontains=busqueda) |
            Q(descripcion__icontains=busqueda) |
            Q(codigoagrupador__codigoagrupador__icontains=busqueda)
        )

    paginator = Paginator(cuentas, 10)
    pagina_actual = request.GET.get('page')
    cuentas_paginadas = paginator.get_page(pagina_actual)

    resultado_importacion = None
    importacion_form = ImportarCatalogoForm()
    plantillas = CatalogoPlantilla.objects.filter(activo=True).order_by('orden', 'nombre')
    plantilla_seleccionada = None
    plantilla_id = request.GET.get('plantilla_id') or request.POST.get('plantilla_id')
    if plantilla_id:
        plantilla_seleccionada = get_object_or_404(CatalogoPlantilla, pk=plantilla_id, activo=True)
    else:
        plantilla_seleccionada = obtener_plantilla_catalogo(tenant)

    if request.method == 'POST':
        accion = request.POST.get('accion', 'guardar_cuenta')

        if accion == 'importar_catalogo':
            importacion_form = ImportarCatalogoForm(request.POST, request.FILES)
            if importacion_form.is_valid():
                archivo = importacion_form.cleaned_data['archivo']
                nivel_maximo = importacion_form.cleaned_data['nivel_maximo']
                importar = importar_csv if archivo.name.lower().endswith('.csv') else importar_excel
                resultado_importacion = importar(archivo, tenant, nivel_maximo=nivel_maximo)
            else:
                from .importador import ResultadoImportacion
                resultado_importacion = ResultadoImportacion()

            if resultado_importacion.exitosas > 0:
                messages.success(request,
                    f'Importación completada: {resultado_importacion.creadas} creadas, {resultado_importacion.actualizadas} actualizadas.')
            if resultado_importacion.errores:
                messages.warning(request,
                    f'{len(resultado_importacion.errores)} errores durante la importación.')

            logger.info(f"Importación catálogo: tenant={tenant.nombre}, creadas={resultado_importacion.creadas}, "
                        f"actualizadas={resultado_importacion.actualizadas}, errores={len(resultado_importacion.errores)}")

            codigos = CodigoAgrupador.objects.all().order_by('codigoagrupador')
            return render(request, 'catalogo/agregar_cuenta.html', {
                'codigos_agrupadores': codigos,
                'cuentas': Paginator(cuentas, 10).get_page(pagina_actual),
                'total_cuentas': cuentas.count(),
                'busqueda': busqueda,
                'resultado_importacion': resultado_importacion,
                'importacion_form': importacion_form,
                'plantillas': plantillas,
                'plantilla_seleccionada': plantilla_seleccionada,
                'plantilla_cuentas': plantilla_seleccionada.cuentas.filter(activa=True).select_related('codigoagrupador').order_by('orden', 'cuenta') if plantilla_seleccionada else [],
            })

        cuenta = request.POST.get('cuenta', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        codigo_agrup = request.POST.get('codigoagrupador', '').strip()
        nivel1 = request.POST.get('nivel1', '').strip()
        nivel2 = request.POST.get('nivel2', '').strip()
        nivel3 = request.POST.get('nivel3', '').strip()
        nivel4 = request.POST.get('nivel4', '').strip()

        if not cuenta or not descripcion or not codigo_agrup:
            messages.error(request, 'Cuenta, descripción y código agrupador son obligatorios.')
            return redirect('agregar_cuenta')

        try:
            codigo_obj = CodigoAgrupador.objects.get(codigoagrupador=codigo_agrup)
        except CodigoAgrupador.DoesNotExist:
            messages.error(request, f'El código agrupador "{codigo_agrup}" no existe en el catálogo del SAT.')
            return redirect('agregar_cuenta')

        _, created = CatalogoCuentas.objects.update_or_create(
            tenant=tenant, cuenta=cuenta,
            defaults={
                'descripcion': descripcion,
                'codigoagrupador': codigo_obj,
                'relacion_sugerida': False,
                'confianza_relacion': None,
                'nivel1': int(nivel1) if nivel1 else None,
                'nivel2': int(nivel2) if nivel2 else None,
                'nivel3': int(nivel3) if nivel3 else None,
                'nivel4': int(nivel4) if nivel4 else None,
            }
        )

        action = 'creada' if created else 'actualizada'
        messages.success(request, f'Cuenta {cuenta} {action} exitosamente.')
        return redirect('catalogo_cuentas')

    codigos = CodigoAgrupador.objects.all().order_by('codigoagrupador')
    return render(request, 'catalogo/agregar_cuenta.html', {
        'codigos_agrupadores': codigos,
        'cuentas': cuentas_paginadas,
        'total_cuentas': cuentas.count(),
        'busqueda': busqueda,
        'resultado_importacion': resultado_importacion,
        'importacion_form': importacion_form,
        'plantillas': plantillas,
        'plantilla_seleccionada': plantilla_seleccionada,
        'plantilla_cuentas': plantilla_seleccionada.cuentas.filter(activa=True).select_related('codigoagrupador').order_by('orden', 'cuenta') if plantilla_seleccionada else [],
    })


@login_required
def subir_catalogo(request):
    """Redirige permanentemente a la interfaz unificada de alta de cuentas."""
    return HttpResponsePermanentRedirect(redirect('agregar_cuenta').url)


@login_required
def descargar_plantilla(request):
    """Descargar plantilla CSV de ejemplo."""
    contenido = generar_plantilla_csv()
    response = HttpResponse(contenido, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="plantilla_catalogo_cuentas.csv"'
    return response


@login_required
def gestionar_plantillas(request):
    """Vista interna simple para revisar plantillas de catálogo."""
    if not request.user.is_superuser:
        raise PermissionDenied

    plantillas = (
        CatalogoPlantilla.objects
        .filter()
        .prefetch_related('cuentas__codigoagrupador')
        .order_by('giro', 'orden', 'nombre')
    )

    return render(request, 'catalogo/gestionar_plantillas.html', {
        'plantillas': plantillas,
    })


@login_required
def crear_plantilla(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    if request.method == 'POST':
        form = CatalogoPlantillaForm(request.POST)
        if form.is_valid():
            plantilla = form.save()
            messages.success(request, f'Plantilla {plantilla.nombre} creada.')
            return redirect('gestionar_plantillas')
    else:
        form = CatalogoPlantillaForm()

    return render(request, 'catalogo/formulario_plantilla.html', {
        'form': form,
        'modo': 'crear',
    })


@login_required
def editar_plantilla(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied

    plantilla = get_object_or_404(CatalogoPlantilla, pk=pk)
    if request.method == 'POST':
        form = CatalogoPlantillaForm(request.POST, instance=plantilla)
        formset = CatalogoPlantillaCuentaFormSet(request.POST, instance=plantilla)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f'Plantilla {plantilla.nombre} actualizada.')
            return redirect('gestionar_plantillas')
    else:
        form = CatalogoPlantillaForm(instance=plantilla)
        formset = CatalogoPlantillaCuentaFormSet(instance=plantilla)

    return render(request, 'catalogo/formulario_plantilla.html', {
        'form': form,
        'plantilla': plantilla,
        'modo': 'editar',
        'formset': formset,
    })


@login_required
@require_POST
def eliminar_plantilla(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied

    plantilla = get_object_or_404(CatalogoPlantilla, pk=pk)
    nombre = plantilla.nombre
    plantilla.delete()
    messages.success(request, f'Plantilla {nombre} eliminada.')
    return redirect('gestionar_plantillas')


@login_required
@require_POST
def eliminar_cuenta(request, pk):
    """Eliminar una cuenta del catálogo."""
    tenant = request.tenant
    cuenta = get_object_or_404(CatalogoCuentas, pk=pk, tenant=tenant)
    desc = str(cuenta)
    cuenta.delete()
    messages.success(request, f'Cuenta {desc} eliminada.')
    return redirect('catalogo_cuentas')


# =========================================
# Generación de Manuales (FASE 3: Dinámico)
# =========================================

def buscar_manual_existente(tenant, cuentas, usar_sat):
    """Una cuenta ya cubierta por un manual se reutiliza, incluso en manuales previos conjuntos."""
    cuentas = list(cuentas)
    if len(cuentas) == 1:
        cuenta = cuentas[0]
        sat_id = cuenta.codigoagrupador.pk if usar_sat else cuenta.codigoagrupador_id
        match = (Q(codigos_sat__pk=sat_id) | Q(cuentas__codigoagrupador_id=sat_id)) if usar_sat else (Q(cuentas__pk=cuenta.pk) | Q(codigos_sat__pk=sat_id))
        return (ManualContable.objects.filter(tenant=tenant).filter(match).distinct()
                .order_by('-aprobado', '-fecha_creacion', '-pk').first())
    relation = 'codigos_sat' if usar_sat else 'cuentas'
    opposite = 'cuentas' if usar_sat else 'codigos_sat'
    ids = {c.codigoagrupador.pk if usar_sat else c.pk for c in cuentas}
    return (ManualContable.objects.filter(tenant=tenant)
            .annotate(total=Count(relation, distinct=True),
                      coincidentes=Count(relation, filter=Q(**{f'{relation}__pk__in': ids}), distinct=True),
                      otras=Count(opposite, distinct=True))
            .filter(total=len(ids), coincidentes=len(ids), otras=0)
            .order_by('-aprobado', '-fecha_creacion').first())


def advertir_manual_existente(request, manual):
    if manual.aprobado:
        messages.warning(request, 'Esta cuenta ya tiene un manual aprobado. No se puede generar otro; abrimos el manual vigente.')
    else:
        messages.warning(request, 'Ya existe un borrador para esta cuenta. Revísalo antes de continuar; abrimos el borrador existente.')
    return redirect('detalle_manual', pk=manual.pk)


def estados_manuales_por_cuenta(tenant, cuentas, usar_sat):
    """Mismo alcance del bloqueo del servidor, con consultas agrupadas por organización."""
    propias, sat_directo, sat_total = {}, {}, {}
    for manual in (ManualContable.objects.filter(tenant=tenant)
                   .order_by('-aprobado', '-fecha_creacion', '-pk')
                   .prefetch_related('cuentas', 'codigos_sat')):
        datos = {'estado': 'aprobado' if manual.aprobado else 'borrador',
                 'url': reverse('detalle_manual', args=[manual.pk])}
        for cuenta in manual.cuentas.all():
            propias.setdefault(cuenta.pk, datos)
            sat_total.setdefault(cuenta.codigoagrupador_id, datos)
        for codigo in manual.codigos_sat.all():
            sat_directo.setdefault(codigo.pk, datos)
            sat_total.setdefault(codigo.pk, datos)
    resultado = {}
    for cuenta in cuentas:
        if usar_sat:
            candidatos = [sat_total.get(cuenta.codigoagrupador.pk)]
        else:
            candidatos = [propias.get(cuenta.pk), sat_directo.get(cuenta.codigoagrupador_id)]
        candidatos = [dato for dato in candidatos if dato]
        if candidatos:
            resultado[str(cuenta.id)] = next((dato for dato in candidatos if dato['estado'] == 'aprobado'), candidatos[0])
    return resultado


@login_required
def generar_manual(request):
    """Vista principal para generar manuales contables con IA."""
    tenant = request.tenant
    if not tenant:
        return redirect('lista_tenants')

    cuentas = CatalogoCuentas.objects.filter(tenant=tenant).select_related('codigoagrupador')
    asegurar_catalogo_sat()
    usar_sat = not cuentas.exists()
    cuentas_sat = [SimpleNamespace(id=f'sat:{c.pk}', cuenta=c.codigoagrupador,
                   descripcion=c.nombre, codigoagrupador=c) for c in CodigoAgrupador.objects.all()] if usar_sat else []
    manuales = ManualContable.objects.filter(tenant=tenant).order_by('-fecha_creacion')

    if request.method == 'POST':
        cuentas_ids = request.POST.getlist('cuentas')
        if not cuentas_ids:
            messages.warning(request, 'Selecciona una cuenta para generar su manual.')
            return redirect('generar_manual')

        if len(cuentas_ids) != 1:
            messages.warning(request, 'Solo puedes generar el manual de una cuenta a la vez. Selecciona una sola cuenta para disponer de suficiente espacio.')
            return redirect('generar_manual')

        if usar_sat:
            cuentas_seleccionadas = [c for c in cuentas_sat if c.id in cuentas_ids]
        else:
            if not all(valor.isdecimal() for valor in cuentas_ids):
                messages.error(request, 'La selección contiene cuentas no disponibles.')
                return redirect('generar_manual')
            cuentas_seleccionadas = list(CatalogoCuentas.objects.filter(
                id__in=cuentas_ids, tenant=tenant
            ).select_related('codigoagrupador'))
        if not cuentas_seleccionadas or len(cuentas_seleccionadas) != len(set(cuentas_ids)):
            messages.error(request, 'La selección contiene cuentas no disponibles.')
            return redirect('generar_manual')
        if any(c.codigoagrupador is None or getattr(c, 'relacion_sugerida', False) for c in cuentas_seleccionadas):
            messages.warning(request, 'Confirma las relaciones SAT del catálogo antes de generar el manual.')
            return redirect('catalogo_cuentas')

        existente = buscar_manual_existente(tenant, cuentas_seleccionadas, usar_sat)
        if existente:
            return advertir_manual_existente(request, existente)

        from panel.controls import reservar_generacion
        impedimento = reservar_generacion(request.user)
        if impedimento:
            messages.warning(request, impedimento)
            return redirect('generar_manual')

        try:
            contenido_generado = generar_contenido_manual(cuentas_seleccionadas, tenant)
        except ManualGenerationError as exc:
            registrar_uso(exc, request.user, tenant)
            messages.error(request, str(exc))
            return redirect('generar_manual')

        registro_ia = registrar_uso(contenido_generado, request.user, tenant)
        if contenido_generado:
            titulo = "Manual: " + ", ".join(
                [c.cuenta for c in cuentas_seleccionadas[:3]]
            )
            if len(cuentas_seleccionadas) > 3:
                titulo += f" (+{len(cuentas_seleccionadas) - 3} más)"

            # Serializa solo el guardado por organización; la llamada de IA queda fuera
            # de la transacción. Otro envío simultáneo puede haber terminado primero.
            with transaction.atomic():
                Tenant.objects.select_for_update().get(pk=tenant.pk)
                existente = buscar_manual_existente(tenant, cuentas_seleccionadas, usar_sat)
                if existente:
                    if registro_ia:
                        registro_ia.manual = existente
                        registro_ia.save(update_fields=['manual'])
                    return advertir_manual_existente(request, existente)
                manual = ManualContable.objects.create(
                    tenant=tenant, titulo=titulo, contenido=contenido_generado,
                    creado_por=request.user,
                )
                if usar_sat:
                    manual.codigos_sat.set([c.codigoagrupador for c in cuentas_seleccionadas])
                else:
                    manual.cuentas.set(cuentas_seleccionadas)
                if registro_ia:
                    registro_ia.manual = manual
                    registro_ia.manual_generado = True
                    registro_ia.save(update_fields=['manual', 'manual_generado'])
            if registro_ia:
                return redirect(f"{reverse('generar_manual')}?reporte={registro_ia.pk}#reporte-ia")
            messages.success(request, 'Manual generado exitosamente con IA.')
            return redirect('generar_manual')
        else:
            messages.error(request, 'No se pudo generar el manual. Intenta de nuevo más tarde; si el problema persiste, contacta al administrador.')

    grupos_sat = []
    cuentas_sin_vinculo = []
    if not usar_sat:
        # Solo se agrupan cuentas del tenant activo; una consulta para todas sus cuentas.
        cuentas = list(cuentas)
        vinculadas = {}
        for cuenta in cuentas:
            if cuenta.codigoagrupador_id:
                vinculadas.setdefault(cuenta.codigoagrupador_id, []).append(cuenta)
            else:
                cuentas_sin_vinculo.append(cuenta)
        grupos_sat = [
            {'codigo': codigo, 'cuentas': vinculadas.get(codigo.pk, [])}
            for codigo in CodigoAgrupador.objects.all()
        ]

    registro_ia = None
    reporte_id = request.GET.get('reporte', '')
    if reporte_id.isdecimal() and len(reporte_id) < 19:
        registro_ia = UsoIA.objects.select_related('manual').filter(
            pk=reporte_id, usuario=request.user, tenant=tenant, manual_generado=True).first()

    return render(request, 'catalogo/generar_manual.html', {
        'reporte_ia': reporte_uso(registro_ia),
        'resumen_ia': resumen_uso(request.user),
        'cuentas': cuentas_sat if usar_sat else cuentas,
        'usar_sat': usar_sat,
        'estados_manuales': estados_manuales_por_cuenta(tenant, cuentas_sat if usar_sat else cuentas, usar_sat),
        'grupos_sat': grupos_sat,
        'opciones_sat_modal': [{'codigo': g['codigo'].codigoagrupador, 'nombre': g['codigo'].nombre} for g in grupos_sat],
        'cuentas_sin_vinculo': cuentas_sin_vinculo,
        'manuales': manuales,
    })


def generar_contenido_manual(cuentas, tenant):
    """Genera el manual con el proveedor configurado, sin exponerlo al usuario."""
    cuentas = list(cuentas)
    if len(cuentas) != 1:
        raise ManualGenerationError('Selecciona una sola cuenta para generar un manual completo.')
    system_prompt, prompt = build_manual_prompts(cuentas, tenant)
    return generar_texto(system_prompt, prompt)


# =========================================
# Operaciones sobre manuales
# =========================================

@login_required
def detalle_manual(request, pk):
    """Ver detalle de un manual."""
    manual = get_object_or_404(ManualContable, pk=pk, tenant=request.tenant)
    return render(request, 'catalogo/detalle_manual.html', {
        'manual': manual, 'imprimir': request.GET.get('imprimir') == '1',
        'presentacion': contexto_presentacion(datos_manual(manual)),
        'composicion_documento': componer_manual(manual),
        'puede_personalizar': puede_personalizar(request.user, manual.tenant),
        'ultimo_cambio_presentacion': manual.cambios_presentacion.select_related('autor').first(),
        'reporte_ia': reporte_uso(manual.usos_ia.filter(manual_generado=True).first()),
        'resumen_ia': resumen_uso(request.user),
    })


@login_required
@require_http_methods(["GET"])
def exportar_manual(request, pk):
    """Word nativo con logos integrados y contenido sanitizado."""
    manual = get_object_or_404(ManualContable, pk=pk, tenant=request.tenant)
    response = HttpResponse(generar_docx(manual),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    filename = slugify(manual.titulo)[:100] or f'manual-{manual.pk}'
    response['Content-Disposition'] = f'attachment; filename="{filename}.docx"'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@login_required
@require_http_methods(["GET", "POST"])
def editar_manual(request, pk):
    """Editar un manual existente."""
    manual = get_object_or_404(ManualContable, pk=pk, tenant=request.tenant)

    if request.method == 'POST':
        manual.titulo = request.POST.get('titulo', manual.titulo)
        manual.contenido = request.POST.get('contenido', manual.contenido)
        manual.save()
        messages.success(request, 'Manual actualizado.')
        return redirect('detalle_manual', pk=manual.pk)

    return render(request, 'catalogo/editar_manual.html', {'manual': manual})


@login_required
@require_POST
def eliminar_manual(request, pk):
    """Eliminar un manual."""
    manual = get_object_or_404(ManualContable, pk=pk, tenant=request.tenant)
    manual.delete()
    messages.success(request, 'Manual eliminado.')
    return redirect('dashboard' if request.POST.get('origen') == 'dashboard' else 'generar_manual')


@login_required
@require_POST
def aprobar_manual(request, pk):
    """Fija la identidad aprobada; repetir la aprobación no cambia el encabezado."""
    with transaction.atomic():
        manual = get_object_or_404(ManualContable.objects.select_for_update(), pk=pk, tenant=request.tenant)
        if not puede_personalizar(request.user, manual.tenant):
            raise PermissionDenied
        if not manual.aprobado:
            manual.presentacion_snapshot = construir_presentacion(manual.tenant)
            manual.aprobado = True
            ManualContable.objects.filter(pk=manual.pk).update(
                aprobado=True, presentacion_snapshot=manual.presentacion_snapshot)
    messages.success(request, f'Manual "{manual.titulo}" aprobado con su presentación actual.')
    return redirect('generar_manual')


def _huella_presentacion(datos):
    return hashlib.sha256(json.dumps(datos, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


@login_required
@require_http_methods(['GET', 'POST'])
def actualizar_presentacion_manual(request, pk):
    """Reemplaza expresamente una identidad fijada, sin llamar a la IA."""
    with transaction.atomic():
        manual = get_object_or_404(ManualContable.objects.select_for_update(), pk=pk, tenant=request.tenant)
        if not puede_personalizar(request.user, manual.tenant):
            raise PermissionDenied
        if not manual.aprobado:
            messages.info(request, 'Los borradores ya utilizan los logos y datos vigentes.')
            return redirect('detalle_manual', pk=manual.pk)
        vigente = construir_presentacion(manual.tenant)
        anterior = datos_manual(manual)
        datos_token = {'manual': manual.pk, 'usuario': request.user.pk,
                       'vigente': _huella_presentacion(vigente), 'anterior': _huella_presentacion(anterior)}
        error = ''
        if request.method == 'POST':
            try:
                recibido = signing.loads(request.POST.get('version_previa', ''), salt='presentacion-manual', max_age=3600)
                if recibido != datos_token:
                    raise signing.BadSignature
            except (signing.BadSignature, ValueError, TypeError):
                error = 'La presentación cambió o la vista previa expiró. Revisa de nuevo el encabezado y confirma la actualización.'
            if not error:
                if vigente != anterior:
                    CambioPresentacionManual.objects.create(manual=manual, autor=request.user, anterior=anterior, nueva=vigente)
                    manual.presentacion_snapshot = vigente
                    ManualContable.objects.filter(pk=manual.pk).update(presentacion_snapshot=vigente)
                messages.success(request, 'Presentación actualizada. El contenido y la aprobación se conservan.')
                return redirect('detalle_manual', pk=manual.pk)
        return render(request, 'catalogo/actualizar_presentacion.html', {
            'manual': manual, 'presentacion': contexto_presentacion(vigente),
            'version_previa': signing.dumps(datos_token, salt='presentacion-manual'), 'error_presentacion': error,
        }, status=409 if error else 200)
