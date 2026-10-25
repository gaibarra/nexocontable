(() => {
    const heredar = document.getElementById('id_usar_color_despacho');
    const color = document.getElementById('id_color');
    if (!heredar || !color) return;
    const actualizar = () => { color.disabled = heredar.checked; };
    heredar.addEventListener('change', actualizar);
    actualizar();
})();
