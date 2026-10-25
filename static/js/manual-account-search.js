(() => {
    'use strict';
    const root = document.getElementById('manual-account-selector');
    const form = document.getElementById('manual-generation-form');
    if (!root || !form) return;
    const search = document.getElementById('manual-account-search');
    const status = document.getElementById('account-search-status');
    const clear = root.querySelector('[data-account-search-clear]');
    const empty = root.querySelector('[data-account-search-empty]');
    const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
    const checkbox = row => row.querySelector('input[name="cuentas"]');
    const active = element => !element.closest('fieldset[hidden]');
    const update = () => {
        const terms = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
        const matches = text => terms.every(term => normalize(text).includes(term));
        // Consultar las filas actuales también recoge cuentas movidas tras vincular al SAT.
        const rows = Array.from(root.querySelectorAll('[data-account-search-row]'));
        rows.forEach(row => { row.hidden = !matches(row.textContent); });
        const groups = Array.from(root.querySelectorAll('[data-account-search-group]'));
        groups.forEach(group => {
            const ownRows = Array.from(group.querySelectorAll('[data-account-search-row]'));
            const heading = group.querySelector('[data-account-search-heading]');
            const headerMatches = matches(heading ? heading.textContent : '');
            if (headerMatches) ownRows.forEach(row => { row.hidden = false; });
            group.hidden = !headerMatches && !ownRows.some(row => !row.hidden);
        });
        const currentRows = rows.filter(active);
        const visible = currentRows.filter(row => !row.hidden);
        const selected = new Set(rows.map(checkbox).filter(input => input && input.checked && !input.disabled).map(input => input.value));
        const visibleIds = new Set(visible.map(checkbox).filter(Boolean).map(input => input.value));
        const outside = [...selected].filter(id => !visibleIds.has(id)).length;
        const ownCatalog = !!root.querySelector('[data-manual-account]');
        const visibleGroups = groups.filter(group => active(group) && !group.hidden).length;
        status.textContent = `${visible.length} de ${currentRows.length} cuentas${ownCatalog ? ' propias' : ''} · ${selected.size} ${selected.size === 1 ? 'seleccionada' : 'seleccionadas'}` +
            (outside ? ` (${outside} fuera de la búsqueda)` : '') +
            (groups.some(active) ? ` · ${visibleGroups} ${visibleGroups === 1 ? 'código SAT visible' : 'códigos SAT visibles'}` : '');
        empty.hidden = visible.length > 0 || visibleGroups > 0;
        clear.hidden = !search.value;
    };
    const reset = () => { search.value = ''; update(); search.focus(); };
    search.addEventListener('input', update);
    search.addEventListener('keydown', event => {
        // Enter dentro del buscador no debe iniciar una llamada a IA.
        if (event.key === 'Enter') event.preventDefault();
        if (event.key === 'Escape') { event.preventDefault(); reset(); }
    });
    clear.addEventListener('click', reset);
    form.addEventListener('change', event => {
        if (event.target.matches('input[name="cuentas"]')) update();
    });
    root.querySelectorAll('[data-catalog-view]').forEach(button => button.addEventListener('click', () => queueMicrotask(update)));
    form.addEventListener('manual-vinculo-confirmado', () => queueMicrotask(update));
    update();
})();
