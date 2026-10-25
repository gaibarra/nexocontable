(() => {
    'use strict';
    const form = document.getElementById('manual-generation-form');
    const dialog = document.getElementById('manual-confirmation');
    if (!form || !dialog) return;
    const inputs = () => [...form.querySelectorAll('input[name="cuentas"]')];
    const selection = () => inputs().find(input => input.checked && !input.matches(':disabled'));
    const confirm = dialog.querySelector('[data-manual-confirm]');
    const cancel = dialog.querySelector('[data-manual-cancel]');
    const existing = JSON.parse(document.getElementById('manual-existing-status')?.textContent || '{}');
    const warning = dialog.querySelector('[data-manual-existing]');
    const openExisting = dialog.querySelector('[data-manual-existing-link]');
    let approved = null;
    let submitting = false;
    const preview = () => {
        const input = selection();
        if (!input) {
            document.getElementById('account-search-status').textContent = 'Selecciona una cuenta para revisar sus datos y generar el manual.';
            document.getElementById('manual-account-search').focus();
            return;
        }
        const previous = existing[input.value];
        dialog.querySelector('#manual-confirmation-title').textContent = previous ? (previous.estado === 'aprobado' ? 'Manual ya aprobado' : 'Borrador existente') : 'Generar manual';
        dialog.querySelector('.manual-preview-scope').hidden = !!previous;
        dialog.querySelector('.manual-preview-privacy').hidden = !!previous;
        warning.hidden = !previous;
        confirm.hidden = !!previous;
        openExisting.hidden = !previous;
        if (previous) {
            warning.textContent = previous.estado === 'aprobado' ?
                'Esta cuenta ya tiene un manual aprobado. No se puede generar otro. Consulta el manual vigente.' :
                'Ya existe un borrador para esta cuenta. Revisa el borrador existente antes de continuar.';
            openExisting.href = previous.url;
            openExisting.textContent = previous.estado === 'aprobado' ? 'Ver manual aprobado' : 'Abrir borrador';
        } else {
            openExisting.removeAttribute('href');
        }
        const row = input.closest('[data-account-search-row]');
        dialog.querySelector('[data-preview-code]').textContent = row.dataset.accountCode;
        dialog.querySelector('[data-preview-name]').textContent = row.dataset.accountName;
        const sat = row.querySelector('[data-account-sat]');
        dialog.querySelector('[data-preview-sat]').textContent = sat ? sat.textContent.trim().replace(/^SAT:\s*/, '') : `${row.dataset.accountCode} — ${row.dataset.accountName}`;
        if (!dialog.open) dialog.showModal();
        cancel.focus();
    };
    // Solo se envía la cuenta habilitada de la vista actual del catálogo.
    form.addEventListener('change', event => {
        const input = event.target;
        if (submitting || !input.matches('input[name="cuentas"]')) return;
        approved = null;
        if (input.checked) {
            inputs().forEach(other => { if (other !== input) other.checked = false; });
            preview();
        } else {
            inputs().filter(other => other.value === input.value).forEach(other => { other.checked = false; });
        }
    }, true);
    form.addEventListener('click', event => {
        if (!submitting && !dialog.open && event.target.matches('input[name="cuentas"]:checked')) preview();
    });
    // Se valida antes de mostrar el progreso o deshabilitar el botón de envío.
    form.addEventListener('submit', event => {
        const input = selection();
        if (submitting || !input || existing[input.value] || approved !== input.value) {
            event.preventDefault();
            event.stopImmediatePropagation();
            if (!submitting) preview();
            return;
        }
        submitting = true;
        confirm.disabled = true;
    }, true);
    cancel.addEventListener('click', () => dialog.close());
    confirm.addEventListener('click', () => {
        if (submitting) return;
        const input = selection();
        if (!input) { dialog.close(); return; }
        if (existing[input.value]) { preview(); return; }
        approved = input.value;
        dialog.close();
        form.requestSubmit();
    });
    window.addEventListener('pageshow', event => {
        if (!event.persisted) return;
        submitting = false; approved = null; confirm.disabled = false;
        confirm.textContent = 'Generar manual';
        confirm.classList.remove('opacity-70', 'cursor-not-allowed');
        document.getElementById('manual-progress-wrap')?.classList.add('hidden');
    });
})();
