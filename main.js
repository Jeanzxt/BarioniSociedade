// Melhorias progressivas: a navegação continua usando documentos HTML completos.
(() => {
    'use strict';

    function initializePage() {
        const root = document.documentElement;
        const content = document.getElementById('conteudo');
        const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
        root.classList.add('js');
        document.body.classList.add('loaded');
        document.querySelectorAll('[data-current-year]').forEach(element => {
            element.textContent = String(new Date().getFullYear());
        });
        if (!content) return;

        let entryTimer = 0;
        let navigationTimer = 0;
        let recoveryTimer = 0;
        let pendingUrl = null;

        const canAnimate = () => !motion.matches &&
            getComputedStyle(root).getPropertyValue('--page-transition-enabled').trim() === '1';

        function resetPage() {
            window.clearTimeout(entryTimer);
            window.clearTimeout(navigationTimer);
            window.clearTimeout(recoveryTimer);
            pendingUrl = null;
            root.classList.remove('page-entering', 'page-leaving');
        }

        function enterPage() {
            resetPage();
            if (!canAnimate()) return;
            root.classList.add('page-entering');
            entryTimer = window.setTimeout(() => root.classList.remove('page-entering'), 400);
        }

        document.addEventListener('click', event => {
            if (event.defaultPrevented || event.button !== 0 || event.metaKey ||
                event.ctrlKey || event.shiftKey || event.altKey || !canAnimate()) return;
            const link = event.target instanceof Element ? event.target.closest('a[href]') : null;
            if (!link || link.hasAttribute('download') ||
                (link.target && link.target.toLowerCase() !== '_self')) return;
            const url = new URL(link.href, window.location.href);
            if (!['http:', 'https:', 'file:'].includes(url.protocol) || url.origin !== location.origin) return;
            if (url.pathname === location.pathname && url.search === location.search) return;
            if (!/\.html$/i.test(url.pathname) && !url.pathname.endsWith('/')) return;

            event.preventDefault();
            // Um clique duplo não cria duas navegações pendentes.
            if (pendingUrl) return;
            window.clearTimeout(entryTimer);
            root.classList.remove('page-entering');
            root.classList.add('page-leaving');
            pendingUrl = url.href;
            navigationTimer = window.setTimeout(() => {
                // Recupera o conteúdo se a navegação for cancelada ou demorar.
                recoveryTimer = window.setTimeout(resetPage, 1400);
                try {
                    window.location.assign(pendingUrl);
                } catch {
                    resetPage();
                }
            }, 160);
        });

        window.addEventListener('pageshow', event => {
            // O histórico pode recuperar o documento enquanto ele ainda estava esmaecido.
            if (event.persisted) enterPage();
        });
        enterPage();
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initializePage, { once: true });
    else initializePage();
})();
