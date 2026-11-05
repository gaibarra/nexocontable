from django import forms
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from catalogo.models import FuenteNormativa, VersionFuente, CriterioRevisado, ControlBiblioteca, AlertaFuente, ManualContable
from cuentas.models import Tenant
from .security import privado
from .audit import registrar

MODELOS={'fuente':FuenteNormativa,'version':VersionFuente,'criterio':CriterioRevisado}
CAMPOS={
 'fuente':['titulo','emisor','naturaleza','url','fiscal'],
 'version':['fuente','edicion','publicada_el','vigente_desde','vigente_hasta','consulta','almacenamiento','envio_ia','reproduccion','evidencia_permisos','huella_documento','evidencia_vigencia'],
 'criterio':['version','familia','perfil_tecnico','regimen','area','titulo','localizacion','explicacion','condiciones','excepciones','vigente_desde','vigente_hasta','cobertura'],
}


@privado()
def inicio(request):
    q=request.GET.get('q','').strip()[:100]
    criterios=CriterioRevisado.objects.select_related('version__fuente').filter(Q(familia__icontains=q)|Q(perfil_tecnico__icontains=q)|Q(regimen__icontains=q)|Q(titulo__icontains=q)|Q(localizacion__icontains=q)).order_by('familia','perfil_tecnico','regimen','area','pk')
    return render(request,'panel/biblioteca.html',{'titulo':'Fuentes y fundamentos',
        'fuentes':FuenteNormativa.objects.all().order_by('titulo'),
        'versiones':VersionFuente.objects.select_related('fuente').order_by('-pk'),
        'criterios':Paginator(criterios,24).get_page(request.GET.get('page')),
        'alertas':AlertaFuente.objects.select_related('fuente').filter(resuelta=False).order_by('-fecha'),
        'cambios_revisados':AlertaFuente.objects.select_related('fuente','revisor').filter(resuelta=True).order_by('-fecha')[:20],
        'activa':ControlBiblioteca.objects.filter(pk=1,activa=True).exists()})


@privado('propietario')
@require_http_methods(['GET','POST'])
def formulario(request,tipo,pk=None):
    if tipo not in MODELOS: raise PermissionDenied
    model=MODELOS[tipo]
    obj=get_object_or_404(model,pk=pk) if pk else None
    clonar=request.GET.get('nueva_version')=='1' and tipo!='fuente'
    if obj and getattr(obj,'publicado',False) and not clonar:
        messages.warning(request,'La publicación es inmutable. Usa Crear nueva versión.')
        return redirect('panel:biblioteca')
    if obj and tipo=='fuente' and obj.versiones.filter(publicado=True).exists():
        messages.info(request,'La identidad de una fuente publicada se conserva. Crea una nueva fuente si cambia.')
        return redirect('panel:biblioteca')
    initial={f:getattr(obj,f) for f in CAMPOS[tipo]} if obj and clonar else None
    if clonar: obj=None
    Form=forms.modelform_factory(model,fields=CAMPOS[tipo],widgets={k:forms.DateInput(format='%Y-%m-%d',attrs={'type':'date'}) for k in ('publicada_el','vigente_desde','vigente_hasta') if k in CAMPOS[tipo]})
    form=Form(request.POST if request.method=='POST' else None,instance=obj,initial=initial)
    if tipo=='criterio':
        from catalogo.desarrollo_uniforme import PERFILES
        form.fields['perfil_tecnico']=forms.ChoiceField(required=False,choices=[('','General de la familia')]+[(p,p.replace('_',' ').title()) for p in PERFILES],initial=getattr(obj,'perfil_tecnico',None) or (initial or {}).get('perfil_tecnico'))
        form.fields['perfil_tecnico'].help_text='Limita el criterio a la naturaleza indicada; debe corresponder a su familia. Vacío aplica a la familia completa.'
        form.fields['cobertura'].help_text='Completa significa revisión integral del área para esta familia, régimen y periodo; conserva Parcial si faltan disposiciones esenciales.'
        form.fields['regimen']=forms.ChoiceField(choices=Tenant.REGIMEN_CHOICES,initial=getattr(obj,'regimen',None) or (initial or {}).get('regimen'))
    if request.method=='POST' and form.is_valid():
        try:
            with transaction.atomic():
                if obj: model.objects.select_for_update().get(pk=obj.pk)
                saved=form.save()
                registrar('fuentes','biblioteca.borrador_guardado',actor=request.user.pk,referencia=f'{tipo}:{saved.pk}')
            return redirect('panel:biblioteca')
        except ValidationError as exc: form.add_error(None,exc)
    return render(request,'panel/biblioteca_form.html',{'titulo':'Editar '+tipo,'form':form})


@privado('propietario')
@require_POST
def estado(request,tipo,pk):
    if tipo not in ('version','criterio'): raise PermissionDenied
    with transaction.atomic():
        obj=get_object_or_404(MODELOS[tipo].objects.select_for_update(),pk=pk)
        if request.POST.get('accion')=='publicar' and not obj.publicado:
            obj.publicado=True; obj.revisor=request.user; obj.revisado_en=timezone.now()
        elif request.POST.get('accion')=='retirar' and obj.publicado:
            obj.retirado=True
        else: raise PermissionDenied
        try:
            obj.save()
        except ValidationError as exc:
            messages.error(request,'No se publicó: '+'; '.join(exc.messages))
            return redirect('panel:biblioteca')
        registrar('fuentes','biblioteca.'+request.POST['accion'],actor=request.user.pk,referencia=f'{tipo}:{pk}')
    return redirect('panel:biblioteca')


@privado('propietario')
@require_POST
def activar(request):
    # Para activar deben existir las seis familias; la cobertura parcial se muestra.
    from catalogo.biblioteca_models import FAMILIAS
    activar=request.POST.get('activa')=='1'
    if activar and any(not CriterioRevisado.objects.filter(familia=f,regimen=r,publicado=True,retirado=False,version__publicado=True,version__retirado=False).exists() for f,_ in FAMILIAS for r,_ in Tenant.REGIMEN_CHOICES):
        messages.error(request,'Faltan combinaciones de familia y régimen en la biblioteca.')
    else:
        ControlBiblioteca.objects.update_or_create(pk=1,defaults={'activa':activar})
        registrar('fuentes','biblioteca.activacion',actor=request.user.pk,detalle=str(activar))
    return redirect('panel:biblioteca')


class ResolverAlerta(forms.Form):
    revision=forms.CharField(min_length=40,max_length=2000,widget=forms.Textarea,label='Resultado de la revisión y disposiciones comprobadas')
    cambio_confirmado=forms.BooleanField(required=False,label='Se confirmó un cambio normativo')
    vigente_desde=forms.DateField(required=False,widget=forms.DateInput(format='%Y-%m-%d',attrs={'type':'date'}))

    def clean(self):
        d=super().clean()
        if d.get('cambio_confirmado') and not d.get('vigente_desde'): self.add_error('vigente_desde','Indica la vigencia del cambio confirmado.')
        return d


@privado('propietario')
@require_http_methods(['GET','POST'])
def resolver_alerta(request,pk):
    obj=get_object_or_404(AlertaFuente,pk=pk,resuelta=False)
    form=ResolverAlerta(request.POST if request.method=='POST' else None)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            obj=AlertaFuente.objects.select_for_update().get(pk=pk,resuelta=False)
            obj.revision=form.cleaned_data['revision']; obj.revisor=request.user; obj.resuelta=True
            if form.cleaned_data['cambio_confirmado']:
                obj.vigente_desde=form.cleaned_data['vigente_desde']
                # Conserva los IDs de documentos afectados; no cambia su contenido o aprobación.
                obj.manuales_afectados=[m.pk for m in ManualContable.objects.exclude(fundamentos_snapshot={}).only('id','fundamentos_snapshot') if any(f['fuente']==obj.fuente_id for f in m.fundamentos_snapshot.get('fuentes',[]))]
            obj.save()
            registrar('fuentes','cambio.revisado',actor=request.user.pk,referencia=pk,detalle=f'Manuales potencialmente afectados: {len(obj.manuales_afectados)}')
        return redirect('panel:biblioteca')
    return render(request,'panel/biblioteca_form.html',{'titulo':'Revisar cambio: '+str(obj.fuente),'form':form})
