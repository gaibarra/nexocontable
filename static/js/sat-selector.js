(() => {
    'use strict';
    const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
    const codes = Array.from(document.querySelectorAll('#codigos-sat option'), option => ({
        code: option.value, name: option.label, search: normalize(`${option.value} ${option.label}`)
    }));
    if (!codes.length) return;
    const byCode = new Map(codes.map(item => [item.code, item]));
    const panel = document.createElement('div');
    panel.className = 'sat-panel';
    panel.hidden = true;
    panel.innerHTML = '<div class="sat-panel-heading"><strong>Catálogo agrupador SAT</strong><span data-count role="status" aria-live="polite"></span></div><div class="sat-options" id="sat-options" role="listbox" aria-label="Códigos SAT"></div><div class="sat-panel-footer">↑ ↓ navegar &nbsp; · &nbsp; Enter elegir &nbsp; · &nbsp; Esc cerrar</div>';
    document.body.append(panel);
    const list = panel.querySelector('.sat-options');
    const count = panel.querySelector('[data-count]');
    let active = null, results = [], index = -1;
    const label = code => byCode.has(code) ? `${code} · ${byCode.get(code).name}` : code;
    const close = () => {
        if (active) {
            active.search.setAttribute('aria-expanded', 'false');
            active.search.removeAttribute('aria-activedescendant');
        }
        panel.hidden = true;
        active = null;
    };
    const position = () => {
        if (!active) return;
        const rect = active.search.getBoundingClientRect();
        const viewport = window.visualViewport;
        const height = viewport ? viewport.height : window.innerHeight;
        const width = Math.min(Math.max(rect.width, 430), window.innerWidth - 24);
        const below = height - rect.bottom - 12;
        const above = rect.top - 12;
        const upwards = below < 260 && above > below;
        const available = Math.max(100, Math.min(370, upwards ? above : below));
        panel.style.width = `${width}px`;
        panel.style.left = `${Math.max(12, Math.min(rect.left, window.innerWidth - width - 12))}px`;
        list.style.maxHeight = `${Math.max(40, available - 80)}px`;
        panel.style.top = `${upwards ? Math.max(8, rect.top - panel.offsetHeight - 6) : rect.bottom + 6}px`;
    };
    const highlight = next => {
        index = next;
        Array.from(list.children).forEach((node, i) => node.setAttribute('aria-selected', String(i === index)));
        const node = list.children[index];
        if (node) {
            active.search.setAttribute('aria-activedescendant', node.id);
            node.scrollIntoView({block: 'nearest'});
        } else active.search.removeAttribute('aria-activedescendant');
    };
    const choose = item => {
        if (!active || active.input.disabled) return;
        const current = active;
        current.input.value = item.code;
        current.search.value = label(item.code);
        current.input.dispatchEvent(new Event('change', {bubbles: true}));
        close();
        current.search.focus({preventScroll: true});
    };
    const render = query => {
        const terms = normalize(query).split(/\s+/).filter(Boolean);
        const matches = codes.filter(item => terms.every(term => item.search.includes(term)));
        matches.sort((a, b) => {
            const rank = item => item.code === query.trim() ? 0 : item.code.startsWith(query.trim()) ? 1 : 2;
            return rank(a) - rank(b);
        });
        results = matches.slice(0, 60);
        list.replaceChildren();
        count.textContent = `${matches.length} ${matches.length === 1 ? 'resultado' : 'resultados'}`;
        if (!results.length) {
            const empty = document.createElement('div');
            empty.className = 'sat-empty';
            empty.textContent = 'No encontramos ese código o nombre. Prueba con “caja”, “bancos” o “102.01”.';
            list.append(empty);
        } else results.forEach((item, i) => {
            const option = document.createElement('div');
            option.id = `sat-option-${i}`;
            option.className = 'sat-option';
            option.setAttribute('role', 'option');
            const code = document.createElement('span');
            code.className = 'sat-option-code';
            code.textContent = item.code;
            const name = document.createElement('span');
            name.className = 'sat-option-name';
            name.textContent = item.name;
            option.append(code, name);
            if (item.code === active.input.value) {
                const check = document.createElement('span');
                check.className = 'sat-option-check';
                check.textContent = '✓';
                option.append(check);
            }
            option.addEventListener('pointermove', () => highlight(i));
            option.addEventListener('click', () => choose(item));
            list.append(option);
        });
        index = -1;
        active.search.removeAttribute('aria-activedescendant');
        panel.hidden = false;
        active.search.setAttribute('aria-expanded', 'true');
        list.scrollTop = 0;
        position();
        panel.querySelector('.sat-panel-footer').textContent = matches.length > 60
            ? 'Mostrando 60 opciones. Escribe para afinar la búsqueda.'
            : '↑ ↓ navegar · Enter elegir · Esc cerrar';
    };
    document.querySelectorAll('[data-sat-input]').forEach(input => {
        const wrap = document.createElement('div');
        wrap.className = 'sat-search-wrap';
        const search = document.createElement('input');
        search.type = 'search';
        search.className = 'sat-search';
        search.autocomplete = 'off';
        search.spellcheck = false;
        search.placeholder = 'Buscar código o nombre SAT…';
        search.value = label(input.value);
        search.setAttribute('role', 'combobox');
        search.setAttribute('aria-autocomplete', 'list');
        search.setAttribute('aria-expanded', 'false');
        search.setAttribute('aria-controls', 'sat-options');
        search.setAttribute('aria-label', input.getAttribute('aria-label'));
        search.setAttribute('aria-describedby', input.getAttribute('aria-describedby'));
        const icon = document.createElement('span');
        icon.className = 'sat-search-icon';
        icon.setAttribute('aria-hidden', 'true');
        icon.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4.5 4.5"/></svg>';
        const arrow = document.createElement('span');
        arrow.className = 'sat-search-arrow';
        arrow.setAttribute('aria-hidden', 'true');
        arrow.textContent = '⌄';
        input.before(wrap);
        wrap.append(icon, search, arrow);
        input.type = 'hidden';
        input.required = false;
        const current = {input, search};
        const open = () => {
            if (input.disabled) return;
            active = current;
            render(search.value === label(input.value) ? '' : search.value);
        };
        search.addEventListener('click', () => { if (active !== current) open(); });
        search.addEventListener('focus', () => search.select());
        search.addEventListener('input', () => {active = current; render(search.value);});
        search.addEventListener('blur', () => {
            search.value = label(input.value);
            if (active === current) close();
        });
        search.addEventListener('keydown', event => {
            if (event.key === 'Escape') {close(); search.value = label(input.value); event.preventDefault();}
            if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
                event.preventDefault();
                if (active !== current) open();
                if (results.length) highlight((index + (event.key === 'ArrowDown' ? 1 : -1) + results.length) % results.length);
            }
            if (event.key === 'Enter') {
                event.preventDefault();
                if (active === current && results.length) choose(results[index < 0 ? 0 : index]);
                else open();
            }
        });
        // Mantiene la selección pendiente visible tras una respuesta del servidor.
        new MutationObserver(() => {search.disabled = input.disabled;}).observe(input, {attributes: true, attributeFilter: ['disabled']});
    });
    panel.addEventListener('mousedown', event => event.preventDefault());
    document.addEventListener('pointerdown', event => {
        if (active && !panel.contains(event.target) && event.target !== active.search) close();
    });
    window.addEventListener('resize', close);
    document.addEventListener('scroll', event => {if (!panel.contains(event.target)) close();}, true);
})();
