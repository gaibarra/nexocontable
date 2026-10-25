(() => {
    'use strict';
    const titles = {success: 'Listo', error: 'Ocurrió un problema', warning: 'Atención', info: 'Información'};
    const swal = window.Swal;
    let queue = Promise.resolve();
    const show = (options) => {
        const result = queue.then(() => swal.fire({
            confirmButtonText: 'Aceptar', confirmButtonColor: '#1a365d',
            ...options
        }));
        queue = result.catch(() => {});
        return result;
    };
    const data = document.getElementById('app-notifications');
    if (swal && data) {
        const notifications = JSON.parse(data.textContent);
        const fallback = document.getElementById('notification-fallback');
        fallback.hidden = true;
        notifications.forEach(({icon, title, text}) => {
            show({icon, titleText: title || titles[icon], text}).catch(() => { fallback.hidden = false; });
        });
    }

    const approved = new WeakSet();
    const pending = new WeakSet();
    document.addEventListener('submit', async (event) => {
        const form = event.target;
        if (!form.matches('form[data-confirm]')) return;
        if (approved.delete(form)) return;
        event.preventDefault();
        if (pending.has(form)) return;
        pending.add(form);
        const submitter = event.submitter;
        try {
            const confirmed = swal ? (await show({
                icon: 'warning', titleText: 'Confirmar acción', text: form.dataset.confirm,
                showCancelButton: true, confirmButtonText: 'Sí, continuar',
                cancelButtonText: 'Cancelar', focusCancel: true
            })).isConfirmed : window.confirm(form.dataset.confirm);
            if (confirmed) {
                approved.add(form);
                form.requestSubmit(submitter || undefined);
                approved.delete(form);
            }
        } finally {
            pending.delete(form);
        }
    });
})();
