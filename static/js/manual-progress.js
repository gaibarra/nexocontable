(() => {
    'use strict';
    const form = document.getElementById('manual-generation-form');
    const dialog = document.getElementById('manual-progress-dialog');
    if (!form || !dialog) return;
    const bar = document.getElementById('manual-progress-bar');
    const track = document.getElementById('manual-progress-track');
    const percent = document.getElementById('manual-progress-percent');
    const label = document.getElementById('manual-progress-label');
    const steps = [...dialog.querySelectorAll('.manual-step')];
    let intervalId = null;
    const stages = [
        {progress: 12, text: 'Validando la cuenta seleccionada', step: 0},
        {progress: 28, text: 'Adaptando al contexto de la organización', step: 1},
        {progress: 52, text: 'Personalizando el contenido y los ejemplos', step: 2},
        {progress: 76, text: 'Organizando el documento final', step: 3},
        {progress: 90, text: 'Esperando el documento completo…', step: 3},
    ];
    const showStage = stage => {
        bar.style.width = `${stage.progress}%`;
        track.setAttribute('aria-valuenow', stage.progress);
        percent.textContent = `${stage.progress}%`;
        label.textContent = stage.text;
        steps.forEach((step, index) => step.classList.toggle('is-active', index <= stage.step));
    };
    // Cerrar la ventana no cancela la petición: se mantiene visible hasta la respuesta.
    dialog.addEventListener('cancel', event => event.preventDefault());
    form.addEventListener('submit', event => {
        if (event.defaultPrevented || dialog.open) return;
        const input = form.querySelector('input[name="cuentas"]:checked:not(:disabled)');
        if (!input) return;
        const row = input.closest('[data-account-search-row]');
        document.getElementById('manual-progress-account').textContent = `${row.dataset.accountCode} · ${row.dataset.accountName}`;
        dialog.showModal();
        document.getElementById('manual-progress-title').focus();
        showStage(stages[0]);
        let stageIndex = 0;
        intervalId = window.setInterval(() => {
            stageIndex += 1;
            if (stageIndex < stages.length) showStage(stages[stageIndex]);
            if (stageIndex >= stages.length - 1) window.clearInterval(intervalId);
        }, 1400);
    });
    window.addEventListener('pagehide', () => window.clearInterval(intervalId));
    window.addEventListener('pageshow', event => {
        if (!event.persisted) return;
        window.clearInterval(intervalId);
        if (dialog.open) dialog.close();
    });
})();
