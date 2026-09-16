"""Teste de integração no Edge. Instale playwright no ambiente de desenvolvimento.

Execute com servidor local rodando: python scripts/verify_site.py
Nenhuma mensagem é enviada: a abertura do WhatsApp é interceptada no navegador.
"""
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import json
import os
import sys
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.site_policy import REDIRECTS

CONFIG = json.loads((ROOT / 'site-config.json').read_text(encoding='utf-8'))
BASE = os.environ.get('SITE_TEST_URL', 'http://127.0.0.1:8000').rstrip('/')
CANONICAL_BASE = CONFIG['base_url'].rstrip('/')
PAGES = sorted(file for file in (ROOT / 'lang/pt').glob('*.html')
               if file.relative_to(ROOT).as_posix() not in REDIRECTS)
WIDTHS = (320, 390, 640, 768, 900, 1024, 1440)
PROFILE_PAGES = {
    'advogado-willian.html', 'advogado-luiz-marconato.html',
    'advogada-daniella-souza.html', 'advogada-fernanda-camargo.html',
}
failures, errors = [], []


def has_type(node, name):
    value = node.get('@type', [])
    return value == name or isinstance(value, list) and name in value


def check_schema(page, filename):
    schema = json.loads(page.locator('script[type="application/ld+json"]').inner_text())
    assert schema.get('@context') == 'https://schema.org', filename
    graph = schema.get('@graph')
    assert isinstance(graph, list), filename
    assert any(has_type(node, 'LegalService') for node in graph), filename
    expected_type = 'ProfilePage' if filename in PROFILE_PAGES else 'WebPage'
    page_node = next((node for node in graph if has_type(node, expected_type)), None)
    assert page_node is not None, (filename, expected_type)
    if filename in PROFILE_PAGES:
        person = page_node.get('mainEntity', {})
        if not has_type(person, 'Person'):
            person = next((node for node in graph
                           if node.get('@id') == person.get('@id')), {})
        assert has_type(person, 'Person'), filename
        assert person.get('name'), filename
    if filename != 'index.html':
        assert any(has_type(node, 'BreadcrumbList') for node in graph), filename


def check_images(page, filename):
    for image in page.locator('main img').all():
        image.scroll_into_view_if_needed()
        image.evaluate('''img => img.decode()''')
        assert image.evaluate('(img) => img.complete && img.naturalWidth > 0'), filename
        if image.evaluate('(img) => !!img.closest(".hero-portrait, .portrait-link, .about-portrait, .profile-portrait")'):
            assert image.evaluate('''img => {
                const source = img.closest('picture')?.querySelector('source[srcset]');
                return !!(source?.getAttribute('srcset')?.trim()
                    && (source.getAttribute('sizes') || img.getAttribute('sizes'))?.trim()
                    && img.currentSrc);
            }'''), (filename, 'Retrato sem fontes responsivas completas')
    page.evaluate('window.scrollTo(0, 0)')


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel='msedge', headless=True)
    context = browser.new_context(reduced_motion='reduce')
    page = context.new_page()
    page.on('pageerror', lambda error: errors.append(str(error)))
    for width in WIDTHS:
        page.set_viewport_size({'width': width, 'height': 900})
        for file in PAGES:
            response = page.goto(BASE + '/lang/pt/' + file.name)
            assert response.status == 200, file.name
            assert page.locator('main').count() == 1, file.name
            assert page.locator('h1').count() == 1, file.name
            assert page.locator('h1').is_visible(), file.name
            assert page.locator('link[rel="canonical"]').get_attribute('href') == CANONICAL_BASE + '/lang/pt/' + file.name, file.name
            check_schema(page, file.name)
            check_images(page, file.name)
            layout = page.evaluate('''() => ({
                width: document.documentElement.scrollWidth,
                overflow: [...document.querySelectorAll('main *, footer *')].filter(el => {
                    const r = el.getBoundingClientRect();
                    return r.width > 0 && (r.right > innerWidth + 1 || r.left < -1);
                }).slice(0, 6).map(el => el.tagName + '.' + el.className)
            })''')
            if layout['width'] > width or layout['overflow']:
                failures.append((width, file.name, layout))
            assert page.locator('meta[name="description"]').get_attribute('content'), file.name
            assert page.locator('a:not([href])').count() == 0, file.name
            assert page.locator('img:not([alt])').count() == 0, file.name
            mobile_contact = page.locator('.mobile-contact')
            if file.name in ('contato.html', 'privacidade.html'):
                assert mobile_contact.count() == 0, file.name
            else:
                assert mobile_contact.count() == 1, file.name
                assert mobile_contact.is_visible() == (width <= 900), (width, file.name)
                if width <= 900:
                    box = mobile_contact.bounding_box()
                    assert box['height'] >= 48 and box['x'] >= 0 and box['x'] + box['width'] <= width, (width, file.name)
        print(f'{width}px: {len(PAGES)} páginas verificadas.', flush=True)

    for alias, canonical in REDIRECTS.items():
        suffix = '?origem=teste%20local&via=legado#conteudo'
        response = page.goto(BASE + '/' + alias + suffix)
        assert response.status == 200, alias
        assert response.request.redirected_from is not None, alias
        assert response.request.redirected_from.response().status == 301, alias
        assert page.url == BASE + '/' + canonical + suffix, (alias, page.url)

    page.set_viewport_size({'width': 390, 'height': 844})
    page.goto(BASE + '/lang/pt/index.html')
    page.locator('.hamburger').click()
    assert page.locator('.nav-menu').is_visible()
    assert not page.locator('.mobile-contact').is_visible()
    page.keyboard.press('Escape')
    assert page.locator('.hamburger').evaluate('(el) => el === document.activeElement')
    assert not page.locator('.nav-menu').is_visible()
    assert page.locator('.mobile-contact').is_visible()
    page.locator('.hamburger').click()
    page.locator('.nav-menu a[href="contato.html"]').click()
    assert page.url.endswith('contato.html')
    assert page.locator('.nav-link[aria-current="page"]').inner_text() == 'Contato'
    page.set_viewport_size({'width': 1440, 'height': 1000})
    page.wait_for_timeout(150)
    assert page.locator('.nav-menu').is_visible()
    assert not page.locator('.nav-menu').evaluate('(el) => el.inert')

    page.evaluate('''() => { window.testOpenings = []; window.open = (...args) => { window.testOpenings.push(args); return null; }; }''')
    submit = page.locator('button[type="submit"]')
    assert submit.is_enabled()
    submit.click()
    assert page.locator('#name').get_attribute('aria-invalid') == 'true'
    page.locator('#name').fill('Teste João & Maria')
    page.locator('#phone').fill('abc')
    page.locator('#subject').select_option(label='Direito Civil')
    page.locator('#message').fill('Teste de interface: contrato & orientação. Nenhuma mensagem real.')
    submit.click()
    assert page.locator('#phone').get_attribute('aria-invalid') == 'true'
    page.locator('#phone').fill('(43) 99999-9999')
    submit.click()
    opening = page.evaluate('window.testOpenings')
    assert len(opening) == 1
    message = parse_qs(urlparse(opening[0][0]).query)['text'][0]
    assert 'Nome: Teste João & Maria' in message
    assert 'Assunto: Direito Civil' in message
    assert page.locator('#name').input_value() == 'Teste João & Maria'
    assert page.locator('.form-message a').get_attribute('href') == opening[0][0]
    page.wait_for_timeout(1300)
    assert submit.locator('span').count() == 1

    page.goto(BASE + '/lang/pt/advogado-willian.html')
    assert page.locator('.nav-link[aria-current="location"]').inner_text() == 'Equipe'
    page.goto(BASE + '/lang/pt/index.html')
    summary = page.locator('details summary').first
    summary.focus()
    page.keyboard.press('Enter')
    assert page.locator('details').first.get_attribute('open') is not None

    for width in (390, 1440):
        page.set_viewport_size({'width': width, 'height': 960})
        page.goto(BASE + '/lang/pt/index.html')
        for y in range(0, page.evaluate('document.body.scrollHeight'), 650):
            page.evaluate('(y) => window.scrollTo(0, y)', y)
            page.wait_for_timeout(50)
        page.wait_for_function('Array.from(document.images).every(img => img.complete && img.naturalWidth > 0)')
        page.evaluate('window.scrollTo(0, 0)')
        page.screenshot(path=str(Path(os.environ['TEMP']) / f'barioni-final-{width}.png'), full_page=True)

    no_js = browser.new_context(java_script_enabled=False, viewport={'width': 390, 'height': 844})
    fallback = no_js.new_page()
    fallback.goto(BASE + '/lang/pt/contato.html')
    assert fallback.locator('.nav-menu').is_visible()
    assert fallback.locator('button[type="submit"]').is_disabled()
    assert fallback.locator('noscript').is_visible()
    assert fallback.locator('a[href^="https://wa.me/"]').count() > 0
    no_js.close()
    browser.close()

assert not errors, errors
assert not failures, failures
print(f'OK: {len(PAGES) * len(WIDTHS)} combinações de página/tela; {len(REDIRECTS)} redirecionamentos; navegação, teclado, FAQ, imagens responsivas, metadados, contato móvel, formulário e alternativa sem JavaScript. Zero erros JS. WhatsApp interceptado, sem envio.')
