from django import template
from django.forms import BaseForm
from django.forms.formsets import BaseFormSet

register = template.Library()


@register.inclusion_tag('_messages.html', takes_context=True)
def app_notifications(context):
    icons = {40: 'error', 30: 'warning', 25: 'success', 20: 'info', 10: 'info'}
    notifications = [
        {'icon': icons.get(message.level, 'info'), 'text': str(message)}
        for message in context.get('messages', [])
    ]
    errors = []
    seen = set()

    def collect(form, prefix=''):
        if id(form) in seen or not form.is_bound:
            return
        seen.add(id(form))
        for name, field_errors in form.errors.items():
            label = str(form.fields[name].label or name) if name in form.fields else 'Formulario'
            errors.extend(f'{prefix}{label}: {error}' for error in field_errors)

    for value in context.flatten().values():
        if isinstance(value, BaseForm):
            collect(value)
        elif isinstance(value, BaseFormSet) and value.is_bound:
            errors.extend(str(error) for error in value.non_form_errors())
            for index, form in enumerate(value.forms, 1):
                if value.can_delete and value._should_delete_form(form):
                    continue
                collect(form, f'Fila {index} — ')
    if errors:
        notifications.append({'icon': 'error', 'title': 'Revisa los datos', 'text': '\n'.join(errors)})
    return {'notifications': notifications}
