(() => {
    'use strict';
    const form = document.getElementById('manual-generation-form');
    if (!form) return;
    const rows = new Map();
    const pending = new Set();
    form.querySelectorAll('[data-manual-account]').forEach(row => {
        const id = row.dataset.manualAccount;
        if (!rows.has(id)) rows.set(id, []);
        rows.get(id).push(row);
    });
    const notify = options => {
        try {
            if (window.Swal) Promise.resolve(window.Swal.fire({
                confirmButtonText: 'Aceptar', confirmButtonColor: '#1a365d', ...options
            })).catch(() => {});
            else window.alert(options.text || options.titleText);
        } catch (_) { /* El aviso no debe bloquear los controles. */ }
    };
    const applyConfirmation = ({id, codigoagrupador, nombre_sat}) => {
        const copies = rows.get(String(id)) || [];
        const target = Array.from(form.querySelectorAll('[data-sat-target]'))
            .find(item => item.dataset.satTarget === codigoagrupador);
        const unlinked = form.querySelector('[data-unlinked-list]');
        copies.forEach(row => {
            row.querySelector('input[data-account-id]').disabled = false;
            const status = row.querySelector('[data-account-status]');
            status.textContent = 'Vinculación confirmada';
            status.classList.remove('text-amber-700', 'text-red-700');
            status.classList.add('text-green-700');
            const sat = row.querySelector('[data-account-sat]');
            sat.textContent = `SAT: ${codigoagrupador} — ${nombre_sat}`;
            sat.hidden = row.dataset.mostrarSat !== 'true';
            row.classList.remove('bg-gray-50');
            row.querySelector('label').classList.add('cursor-pointer');
            const action = row.querySelector('[data-account-action]');
            if (action) action.remove();
            if (target && unlinked && unlinked.contains(row)) {
                const empty = target.querySelector('[data-sat-empty]');
                if (empty) empty.remove();
                target.appendChild(row);
            }
        });
        if (unlinked) {
            const count = unlinked.querySelectorAll('[data-manual-account]').length;
            form.querySelector('[data-unlinked-count]').textContent = String(count);
            form.querySelector('[data-unlinked-section]').hidden = count === 0;
        }
    };
    form.addEventListener('manual-vinculo-confirmado', event => applyConfirmation(event.detail));
    form.querySelectorAll('[data-confirmar-sugerencia]').forEach(button => {
        button.addEventListener('click', async () => {
            const id = button.dataset.accountId;
            if (pending.has(id)) return;
            const codigo = button.dataset.codigoSat;
            if (!codigo) return;
            pending.add(id);
            const copies = rows.get(id) || [];
            const buttons = copies.map(row => row.querySelector('[data-confirmar-sugerencia]')).filter(Boolean);
            buttons.forEach(item => {item.disabled = true; item.textContent = 'Guardando...';});
            const controller = new AbortController();
            const timeout = window.setTimeout(() => controller.abort(), 15000);
            try {
                const response = await fetch(button.dataset.url, {
                    method: 'POST', credentials: 'same-origin', signal: controller.signal,
                    headers: {'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'},
                    body: new URLSearchParams({codigoagrupador: codigo,
                        csrfmiddlewaretoken: form.querySelector('[name="csrfmiddlewaretoken"]').value})
                });
                if (response.redirected || response.status === 401) {
                    throw new Error('Tu sesión puede haber expirado. Inicia sesión de nuevo antes de confirmar.');
                }
                if (response.status === 403) {
                    throw new Error('La sesión o la validación de seguridad ya no es válida. Recarga la página e inténtalo de nuevo.');
                }
                const isJson = (response.headers.get('content-type') || '').includes('application/json');
                const result = isJson ? await response.json() : null;
                if (!response.ok || !result || !result.ok) {
                    throw new Error((result && result.message) || 'No se pudo confirmar la vinculación. Inténtalo de nuevo.');
                }
                applyConfirmation({id, codigoagrupador: codigo,
                    nombre_sat: result.cuenta.nombre_sat});
                notify({icon: 'success', titleText: 'Vinculación confirmada', text: result.message,
                    toast: true, position: 'top-end', showConfirmButton: false, timer: 2400});
            } catch (error) {
                const uncertain = error.name === 'AbortError' || error instanceof TypeError;
                notify({icon: 'error', titleText: 'No se pudo confirmar la vinculación',
                    text: uncertain ? 'No se pudo comprobar el guardado. Vuelve a confirmar esta cuenta para verificar la vinculación.' : error.message});
            } finally {
                window.clearTimeout(timeout);
                buttons.forEach(item => {item.disabled = false; item.textContent = 'Confirmar vinculación';});
                pending.delete(id);
            }
        });
    });
})();
