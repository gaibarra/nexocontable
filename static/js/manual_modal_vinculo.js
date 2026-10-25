(() => {
    'use strict';
    const dialog = document.getElementById('modal-vincular-sat');
    const form = document.getElementById('manual-generation-form');
    if (!dialog || !form) return;
    const codes = JSON.parse(document.getElementById('opciones-sat-modal').textContent);
    const search = document.getElementById('buscar-sat-modal');
    const select = document.getElementById('codigo-sat-modal');
    const save = dialog.querySelector('[data-modal-guardar]');
    const cancel = dialog.querySelector('[data-modal-cancelar]');
    const feedback = dialog.querySelector('[data-modal-feedback]');
    let active = null;
    let busy = false;
    const normalize = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
    const filter = () => {
        const text = normalize(search.value.trim());
        const matches = codes.filter(code => normalize(`${code.codigo} ${code.nombre}`).includes(text));
        select.replaceChildren(...matches.map(code => new Option(`${code.codigo} — ${code.nombre}`, code.codigo)));
        select.selectedIndex = -1;
        save.disabled = true;
        feedback.textContent = matches.length ? `${matches.length} códigos disponibles. Selecciona uno para guardar.` : 'No se encontraron códigos. Prueba otro código o nombre.';
    };
    search.addEventListener('input', filter);
    select.addEventListener('change', () => {save.disabled = busy || !select.value;});
    cancel.addEventListener('click', () => {if (!busy) dialog.close();});
    dialog.addEventListener('cancel', event => {if (busy) event.preventDefault();});
    form.querySelectorAll('[data-vincular-sat]').forEach(button => button.addEventListener('click', () => {
        if (busy || dialog.open) return;
        active = button;
        dialog.querySelector('[data-modal-cuenta]').textContent = `Cuenta propia: ${button.dataset.cuenta}`;
        search.value = '';
        filter();
        dialog.showModal();
        search.focus();
    }));
    save.addEventListener('click', async () => {
        if (busy || !active || !codes.some(code => code.codigo === select.value)) return;
        busy = true;
        save.disabled = cancel.disabled = search.disabled = select.disabled = true;
        save.textContent = 'Guardando...';
        feedback.textContent = 'Guardando la vinculación de esta cuenta...';
        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), 15000);
        try {
            const response = await fetch(active.dataset.url, {
                method: 'POST', credentials: 'same-origin', signal: controller.signal,
                headers: {'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'},
                body: new URLSearchParams({codigoagrupador: select.value,
                    csrfmiddlewaretoken: form.querySelector('[name="csrfmiddlewaretoken"]').value})
            });
            if (response.redirected || response.status === 401) throw new Error('Tu sesión puede haber expirado. Inicia sesión de nuevo.');
            if (response.status === 403) throw new Error('La sesión o la validación de seguridad ya no es válida. Recarga la página e inténtalo de nuevo.');
            const isJson = (response.headers.get('content-type') || '').includes('application/json');
            const result = isJson ? await response.json() : null;
            if (!response.ok || !result || !result.ok) throw new Error((result && result.message) || 'No se pudo guardar la vinculación. Inténtalo de nuevo.');
            form.dispatchEvent(new CustomEvent('manual-vinculo-confirmado', {detail: result.cuenta}));
            dialog.close();
            try {
                if (window.Swal) Promise.resolve(window.Swal.fire({icon: 'success', titleText: 'Vinculación guardada',
                    text: result.message, toast: true, position: 'top-end', showConfirmButton: false, timer: 2400})).catch(() => {});
            } catch (_) { /* La cuenta ya está guardada; no bloquear controles por un aviso. */ }
        } catch (error) {
            const uncertain = error.name === 'AbortError' || error instanceof TypeError;
            feedback.textContent = uncertain ? 'No se pudo comprobar el guardado. Vuelve a guardar esta vinculación para verificarla.' : error.message;
        } finally {
            window.clearTimeout(timeout);
            busy = false;
            save.disabled = !select.value;
            cancel.disabled = search.disabled = select.disabled = false;
            save.textContent = 'Guardar vinculación';
        }
    });
})();
