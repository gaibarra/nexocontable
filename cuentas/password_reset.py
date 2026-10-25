"""Recuperación de acceso con los tokens y validadores nativos de Django."""
import logging
from django import forms
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.urls import reverse_lazy
from django.core.mail import get_connection, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from .forms import INPUT_CLASS

logger = logging.getLogger(__name__)


class RecuperarPasswordForm(PasswordResetForm):
    email = forms.EmailField(label='Correo electrónico', max_length=254,
        widget=forms.EmailInput(attrs={'class': INPUT_CLASS, 'autocomplete': 'email',
                                      'placeholder': 'Correo con el que te registraste', 'autofocus': True}))

    def save(self, **kwargs):
        # El enlace utiliza siempre nuestro dominio, independientemente del Host recibido.
        kwargs['domain_override'] = settings.PASSWORD_RESET_DOMAIN
        kwargs['use_https'] = True
        super().save(**kwargs)


    def send_mail(self, subject_template_name, email_template_name, context, from_email,
                  to_email, html_email_template_name=None):
        subject = ''.join(render_to_string(subject_template_name, context).splitlines())
        mensaje = EmailMultiAlternatives(subject, render_to_string(email_template_name, context),
            from_email, [to_email], connection=getattr(self, 'mail_connection', None))
        if html_email_template_name:
            mensaje.attach_alternative(render_to_string(html_email_template_name, context), 'text/html')
        try:
            mensaje.send()
        except Exception as exc:
            # Mantiene la respuesta genérica; no registra correo, contraseña ni enlace.
            logger.error('No se pudo enviar la recuperación: %s', type(exc).__name__)


class NuevaPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, label in [('new_password1', 'Nueva contraseña'), ('new_password2', 'Confirmar nueva contraseña')]:
            self.fields[nombre].label = label
            self.fields[nombre].widget.attrs.update({'class': INPUT_CLASS, 'autocomplete': 'new-password'})
        self.fields['new_password1'].widget.attrs['placeholder'] = 'Escribe una contraseña nueva'
        self.fields['new_password2'].widget.attrs['placeholder'] = 'Repite la nueva contraseña'


@method_decorator(never_cache, name='dispatch')
class RecuperacionPrivadaMixin:
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        response['Referrer-Policy'] = 'no-referrer'
        return response


class RecuperarPasswordView(RecuperacionPrivadaMixin, auth_views.PasswordResetView):
    form_class = RecuperarPasswordForm
    template_name = 'cuentas/password_reset_form.html'
    email_template_name = 'emails/password_reset.txt'
    html_email_template_name = 'emails/password_reset.html'
    subject_template_name = 'emails/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')


    def form_valid(self, form):
        conexion = get_connection()
        try:
            # Se verifica antes de buscar cuentas, con la misma respuesta para todos.
            conexion.open()
        except Exception as exc:
            logger.error('Servicio de correo de recuperación no disponible: %s', type(exc).__name__)
            try:
                conexion.close()
            except Exception:
                pass
            form.add_error(None, 'El correo de recuperación no está disponible en este momento. Inténtalo más tarde.')
            response = self.form_invalid(form)
            response.status_code = 503
            response['Retry-After'] = '300'
            return response
        try:
            form.mail_connection = conexion
            return super().form_valid(form)
        finally:
            try:
                conexion.close()
            except Exception as exc:
                logger.warning('No se pudo cerrar la conexión de correo: %s', type(exc).__name__)


class RecuperarPasswordDoneView(RecuperacionPrivadaMixin, auth_views.PasswordResetDoneView):
    template_name = 'cuentas/password_reset_done.html'


class RecuperarPasswordConfirmView(RecuperacionPrivadaMixin, auth_views.PasswordResetConfirmView):
    form_class = NuevaPasswordForm
    template_name = 'cuentas/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
    post_reset_login = False


class RecuperarPasswordCompleteView(RecuperacionPrivadaMixin, auth_views.PasswordResetCompleteView):
    template_name = 'cuentas/password_reset_complete.html'
