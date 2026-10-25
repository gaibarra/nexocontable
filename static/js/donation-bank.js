(() => {
    'use strict';
    const input = document.getElementById('donation-bank-clabe');
    const button = document.getElementById('copy-donation-clabe');
    const status = document.getElementById('bank-copy-status');
    if (!input || !button || !status) return;
    button.addEventListener('click', async () => {
        button.disabled = true;
        try {
            if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('clipboard-unavailable');
            await navigator.clipboard.writeText(input.value);
            status.textContent = 'CLABE copiada. Puedes pegarla en tu aplicación bancaria.';
        } catch (_) {
            input.focus();
            input.select();
            status.textContent = 'Selecciona y copia la CLABE con la opción Copiar de tu dispositivo.';
        } finally {
            button.disabled = false;
        }
    });
})();
