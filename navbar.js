// Accessible disclosure navigation. CSS controls when the mobile button is shown.
(() => {
    'use strict';

    function initializeNavbar() {
        const navbar = document.querySelector('.navbar');
        const button = navbar?.querySelector('.hamburger');
        const menu = navbar?.querySelector('.nav-menu');
        if (!navbar || !button || !menu || navbar.dataset.navigationReady) return;

        navbar.classList.add('nav-enhanced');
        menu.id ||= 'navMenu';
        button.setAttribute('aria-controls', menu.id);

        let isOpen = false;
        let mobile = false;
        let resizeFrame = 0;

        function setOpen(open, restoreFocus = false) {
            isOpen = mobile && open;
            // Move focus before making the menu inert.
            if (!isOpen && restoreFocus) button.focus();
            menu.classList.toggle('active', isOpen);
            button.classList.toggle('active', isOpen);
            document.body.classList.toggle('nav-open', isOpen);
            button.setAttribute('aria-expanded', String(isOpen));
            button.setAttribute('aria-label', isOpen ? 'Fechar menu de navegação' : 'Abrir menu de navegação');
            menu.inert = mobile && !isOpen;
            if (mobile && !isOpen) menu.setAttribute('aria-hidden', 'true');
            else menu.removeAttribute('aria-hidden');
        }

        function updateLayout() {
            const buttonStyle = window.getComputedStyle(button);
            const nextMobile = buttonStyle.display !== 'none' && buttonStyle.visibility !== 'hidden';
            if (nextMobile !== mobile) {
                const focusInMenu = menu.contains(document.activeElement);
                mobile = nextMobile;
                setOpen(false, mobile && focusInMenu);
            } else {
                setOpen(isOpen);
            }
        }

        button.addEventListener('click', () => setOpen(!isOpen));
        menu.addEventListener('click', event => {
            if (event.target.closest('a[href]')) setOpen(false);
        });
        document.addEventListener('click', event => {
            if (isOpen && !menu.contains(event.target) && !button.contains(event.target)) {
                setOpen(false, menu.contains(document.activeElement));
            }
        });
        document.addEventListener('keydown', event => {
            if (event.key === 'Escape' && isOpen) {
                event.preventDefault();
                setOpen(false, true);
            }
        });
        // Leaving the disclosure closes it without trapping keyboard users.
        document.addEventListener('focusin', event => {
            if (isOpen && !menu.contains(event.target) && !button.contains(event.target)) setOpen(false);
        });
        window.addEventListener('resize', () => {
            window.cancelAnimationFrame(resizeFrame);
            resizeFrame = window.requestAnimationFrame(updateLayout);
        }, { passive: true });
        window.addEventListener('pageshow', updateLayout);

        const normalizePath = path => path.replace(/\/index\.html$/i, '/').replace(/\/$/, '') || '/';
        const currentPath = normalizePath(window.location.pathname);
        const isProfile = /\/advogad[oa]-[^/]+\.html$/i.test(currentPath);
        navbar.querySelectorAll('.nav-link').forEach(link => {
            const target = new URL(link.href, window.location.href);
            const exactMatch = target.origin === window.location.origin && normalizePath(target.pathname) === currentPath;
            const parentMatch = target.origin === window.location.origin && isProfile && /\/advogados\.html$/i.test(target.pathname);
            link.classList.toggle('active', exactMatch || parentMatch);
            if (exactMatch || parentMatch) link.setAttribute('aria-current', exactMatch ? 'page' : 'location');
            else link.removeAttribute('aria-current');
        });

        const updateScroll = () => navbar.classList.toggle('is-scrolled', window.scrollY > 16);
        window.addEventListener('scroll', updateScroll, { passive: true });
        updateLayout();
        updateScroll();
        navbar.dataset.navigationReady = 'true';
        document.documentElement.classList.remove('nav-pending');
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initializeNavbar, { once: true });
    else initializeNavbar();
})();
