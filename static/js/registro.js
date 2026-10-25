(() => {
    const form = document.getElementById('registration-form');
    if (!form || form.dataset.registrationFresh !== 'true') return;
    const limpiarRegistroNuevo = () => {
        for (const campo of form.elements) {
            if (!campo.name || campo.type === 'hidden' || campo.type === 'submit') continue;
            if (campo.type === 'checkbox' || campo.type === 'radio') campo.checked = false;
            else if (campo.matches('input, select, textarea')) campo.value = '';
        }
    };
    // También se ejecuta cuando el navegador restaura la página desde el historial.
    window.addEventListener('pageshow', limpiarRegistroNuevo);
    if (document.readyState === 'complete') limpiarRegistroNuevo();
})();
