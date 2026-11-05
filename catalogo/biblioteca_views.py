from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from cuentas.marca_views import puede_personalizar
from panel.audit import registrar
from .models import ManualContable, RevisionFundamentos
from .biblioteca import huella, pendientes_manual


class VerificacionForm(forms.Form):
    pendiente = forms.ChoiceField(label='Pendiente a verificar')
    huella = forms.CharField(widget=forms.HiddenInput)
    norma = forms.CharField(max_length=250, label='Norma o disposición consultada')
    edicion = forms.CharField(max_length=200, label='Edición o versión')
    localizacion = forms.CharField(max_length=250, label='Artículo, fracción o párrafo exacto')
    fecha_consulta = forms.DateField(widget=forms.DateInput(format='%Y-%m-%d',attrs={'type':'date'}))
    nota = forms.CharField(min_length=40, max_length=2000, widget=forms.Textarea, label='Comprobación de aplicabilidad, requisitos, excepciones y conclusión')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not field.widget.is_hidden:
                field.widget.attrs['class']='w-full border border-slate-300 rounded-lg px-3 py-2 mt-1'

    def clean_fecha_consulta(self):
        fecha=self.cleaned_data['fecha_consulta']
        if fecha>timezone.localdate(): raise forms.ValidationError('La consulta no puede ser futura.')
        return fecha


@login_required
@never_cache
@require_http_methods(['GET','POST'])
def revisar(request, pk):
    manual=get_object_or_404(ManualContable,pk=pk,tenant=request.tenant)
    editable=puede_personalizar(request.user,manual.tenant)
    if request.method=='POST' and not editable: raise PermissionDenied
    pendientes=pendientes_manual(manual)
    form=VerificacionForm(request.POST if request.method=='POST' else None,initial={'huella':huella(manual),'fecha_consulta':timezone.localdate()})
    form.fields['pendiente'].choices=[(p['id'],p['titulo']) for p in pendientes]
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            manual=ManualContable.objects.select_for_update().get(pk=manual.pk,tenant=request.tenant)
            if form.cleaned_data['huella'] != huella(manual):
                form.add_error(None,'El contenido cambió; recarga y revisa la nueva versión.')
            elif form.cleaned_data['pendiente'] not in {p['id'] for p in pendientes_manual(manual)}:
                form.add_error(None,'El pendiente cambió; recarga la página.')
            else:
                evidencia={k:(v.isoformat() if hasattr(v,'isoformat') else v) for k,v in form.cleaned_data.items() if k!='huella'}
                RevisionFundamentos.objects.create(manual=manual,autor=request.user,huella=huella(manual),tipo='verificacion',evidencia=evidencia)
                registrar('fuentes','verificacion.documentada',actor=request.user.pk,organizacion_id=manual.tenant_id,referencia=manual.pk,detalle='Pendiente: '+evidencia['pendiente'])
                messages.success(request,'Verificación registrada para esta versión. No publica un criterio global ni aprueba el manual.')
                return redirect('revisar_fundamentos',pk=manual.pk)
    return render(request,'catalogo/revisar_fundamentos.html',{'manual':manual,'form':form,'pendientes':pendientes,'editable':editable,'historial':manual.revisiones_fundamentos.select_related('autor').order_by('-pk')})
