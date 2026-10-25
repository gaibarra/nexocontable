(() => {
    'use strict';
    // Una sola lista compartida: no se duplican miles de opciones en cada cuenta.
    const validCodes = new Set(Array.from(document.querySelectorAll('#codigos-sat option'), option => option.value));
    const pending = new WeakSet();
    const notify = options => {
        try {
            if (window.Swal) {
                Promise.resolve(window.Swal.fire({
                    confirmButtonText: 'Aceptar', confirmButtonColor: '#1a365d', ...options
                })).catch(() => {});
            } else {
                window.alert(options.text || options.titleText);
            }
        } catch (_) { /* Un aviso no debe dejar bloqueados los controles. */ }
    };
    document.querySelectorAll('form[data-confirmar-relacion]').forEach(form => {
        form.noValidate = true;
        const input = form.querySelector('input[name="codigoagrupador"]');
        const cell = form.closest('[data-relacion-cuenta]');
        const code = cell.querySelector('[data-relacion-codigo]');
        const status = cell.querySelector('[data-relacion-estado]');
        const hint = form.querySelector('[data-relacion-ayuda]');
        const button = form.querySelector('button[type="submit"]');
        const updateButton = () => {
            const value = input.value.trim();
            const valid = validCodes.has(value);
            const confirmed = valid && value === form.dataset.confirmedCode;
            button.disabled = pending.has(form) || !valid || confirmed;
            button.textContent = pending.has(form) ? 'Guardando...' : confirmed ? 'Relación confirmada' : 'Confirmar relación';
            hint.textContent = !value ? 'Primero selecciona un código SAT para habilitar la confirmación.' :
                !valid ? 'Elige un código existente de las sugerencias SAT; no escribas aquí el número de tu cuenta propia.' :
                confirmed ? 'Esta relación ya está confirmada. Puedes elegir otro código para cambiarla.' :
                'Código SAT válido. Confirma para guardar la vinculación de esta cuenta.';
        };
        input.addEventListener('input', updateButton);
        input.addEventListener('change', updateButton);
        updateButton();
        form.addEventListener('submit', async event => {
            event.preventDefault();
            if (pending.has(form)) return;
            const value = input.value.trim();
            if (!validCodes.has(value)) {
                updateButton();
                notify({icon: 'warning', titleText: 'Selecciona un código SAT válido',
                    text: 'Primero elige un código del catálogo SAT. No se ha guardado ningún cambio.',
                    toast: true, position: 'top-end', showConfirmButton: false, timer: 3000});
                input.focus();
                return;
            }
            if (value === form.dataset.confirmedCode) return;
            input.value = value;
            pending.add(form);
            const previousStatus = status.textContent;
            const controller = new AbortController();
            const timeout = window.setTimeout(() => controller.abort(), 15000);
            try {
                const data = new FormData(form);
                input.disabled = true;
                form.setAttribute('aria-busy', 'true');
                status.textContent = 'Guardando vinculación...';
                updateButton();
                const response = await fetch(form.action, {
                    method: 'POST', body: data, credentials: 'same-origin',
                    headers: {'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'},
                    signal: controller.signal
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
                code.textContent = `${result.cuenta.codigoagrupador} - ${result.cuenta.nombre_sat}`;
                input.value = result.cuenta.codigoagrupador;
                form.dataset.confirmedCode = result.cuenta.codigoagrupador;
                status.textContent = 'Vinculación confirmada';
                notify({icon: 'success', titleText: 'Vinculación confirmada', text: result.message,
                    toast: true, position: 'top-end', showConfirmButton: false, timer: 2400, timerProgressBar: true});
            } catch (error) {
                status.textContent = previousStatus;
                const uncertain = error.name === 'AbortError' || error instanceof TypeError;
                notify({icon: 'error', titleText: uncertain ? 'No se pudo comprobar el resultado' : 'No se pudo confirmar',
                    text: uncertain ? 'La conexión se interrumpió o tardó demasiado. La vinculación podría haberse guardado; vuelve a confirmar esta cuenta para comprobarlo.' : error.message});
            } finally {
                window.clearTimeout(timeout);
                input.disabled = false;
                form.removeAttribute('aria-busy');
                pending.delete(form);
                updateButton();
            }
        });
    });
})();
