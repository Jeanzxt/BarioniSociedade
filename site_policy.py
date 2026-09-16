"""Lista pública e política de segurança compartilhadas por build, pacote e preview."""

PUBLIC_FILES = (
    'index.html', '404.html', 'robots.txt', 'sitemap.xml',
    'css/style.css', 'css/page-transitions.css',
    'css/contact-experience.css',
    'js/nav-bootstrap.js', 'js/navbar.js', 'js/main.js', 'js/contact.js',
    'lang/pt/index.html', 'lang/pt/sobre.html', 'lang/pt/servicos.html',
    'lang/pt/advogados.html', 'lang/pt/depoimentos.html',
    'lang/pt/contato.html', 'lang/pt/privacidade.html',
    'lang/pt/advogado-willian.html', 'lang/pt/advogado-LuizMarconato.html',
    'lang/pt/advogado-maria.html', 'lang/pt/advogado-ana.html',
    'lang/pt/advogado-luiz-marconato.html',
    'lang/pt/advogada-daniella-souza.html', 'lang/pt/advogada-fernanda-camargo.html',
    'assets/brand-mark.svg', 'assets/favicon.svg',
    'assets/willian-barioni.jpeg', 'assets/luiz-carlos-marconato-junior.jpeg',
    'assets/maria-silva.jpeg', 'assets/ana-costa.jpeg',
    'assets/willian-barioni-360.webp', 'assets/willian-barioni-720.webp',
    'assets/daniella-souza-360.webp', 'assets/daniella-souza-720.webp',
    'assets/luiz-carlos-marconato-junior-360.webp', 'assets/luiz-carlos-marconato-junior-720.webp',
    'assets/fernanda-camargo-360.webp', 'assets/fernanda-camargo-720.webp',
    'assets/social-card.png',
)

REDIRECTS = {
    'lang/pt/advogado-maria.html': 'lang/pt/advogada-daniella-souza.html',
    'lang/pt/advogado-ana.html': 'lang/pt/advogada-fernanda-camargo.html',
    'lang/pt/advogado-LuizMarconato.html': 'lang/pt/advogado-luiz-marconato.html',
}

# O formulário só prepara um link: não há API, POST, iframe ou scripts externos.
# A versão meta não pode conter frame-ancestors; essa proteção exige HTTP.
CSP_META = (
    "default-src 'none'; script-src 'self'; script-src-attr 'none'; "
    "style-src 'self'; style-src-attr 'none'; img-src 'self'; font-src 'self'; "
    "connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"
)
SECURITY_HEADERS = {
    'Content-Security-Policy': CSP_META + "; frame-ancestors 'none'",
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'no-referrer',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=()',
}

# Somente no HTTPS público, sem impor a política a subdomínios ainda desconhecidos.
HSTS = 'max-age=31536000'
