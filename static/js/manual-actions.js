(() => {
    'use strict';
    const page = document.querySelector('.manual-generation-page');
    const bar = document.querySelector('.manual-action-bar');
    if (!page || !bar) return;
    const tabs = document.querySelector('.mobile-tabs');
    const update = () => {
        const tabsHeight = tabs ? tabs.getBoundingClientRect().height : 0;
        // Mantener la acción por encima del teclado cuando el navegador reduce
        // el viewport visual, sin desplazarla artificialmente al hacer zoom.
        const viewport = window.visualViewport;
        const keyboardInset = viewport && viewport.scale === 1 ?
            Math.max(0, window.innerHeight - viewport.height - viewport.offsetTop) : 0;
        page.style.setProperty('--manual-action-bottom', `${Math.max(tabsHeight, keyboardInset)}px`);
        page.style.setProperty('--manual-action-height', `${Math.ceil(bar.getBoundingClientRect().height)}px`);
    };
    if ('ResizeObserver' in window) {
        const observer = new ResizeObserver(update);
        observer.observe(bar);
        if (tabs) observer.observe(tabs);
    }
    window.addEventListener('resize', update);
    if (window.visualViewport) {
        window.visualViewport.addEventListener('resize', update);
        window.visualViewport.addEventListener('scroll', update);
    }
    update();
})();
