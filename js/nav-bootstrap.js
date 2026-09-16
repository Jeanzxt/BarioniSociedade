// Reserve the compact navigation before the first paint, with a fail-open fallback.
(() => {
    'use strict';

    const root = document.documentElement;
    root.classList.add('nav-pending');
    window.setTimeout(() => {
        const navbar = document.querySelector('.navbar');
        if (navbar?.dataset.navigationReady !== 'true') {
            navbar?.classList.remove('nav-enhanced');
            const menu = navbar?.querySelector('.nav-menu');
            if (menu) {
                menu.inert = false;
                menu.removeAttribute('aria-hidden');
            }
            document.body?.classList.remove('nav-open');
        }
        root.classList.remove('nav-pending');
    }, 3000);
})();
