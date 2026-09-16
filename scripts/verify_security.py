"""Verifica as proteções no navegador e em HTTP, sem acessar serviços externos.

Execute: python scripts/verify_security.py
Usa um servidor temporário restrito a 127.0.0.1 e uma porta livre automaticamente.
"""
from contextlib import contextmanager
from functools import partial
from html.parser import HTMLParser
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs, urlsplit
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright
from scripts.site_policy import PUBLIC_FILES, REDIRECTS, SECURITY_HEADERS
from start_server import SiteRequestHandler


class QuietHandler(SiteRequestHandler):
    def log_message(self, format, *args):
        pass


class StructuredData(HTMLParser):
    def __init__(self):
        super().__init__()
        self.collecting = False
        self.content = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type') == 'application/ld+json':
            self.collecting = True

    def handle_endtag(self, tag):
        if tag == 'script':
            self.collecting = False

    def handle_data(self, data):
        if self.collecting:
            self.content += data


@contextmanager
def preview(handler=None):
    handler = handler or partial(QuietHandler, directory=str(ROOT))
    with ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield server.server_port
        finally:
            server.shutdown()
            thread.join(timeout=5)


def request(port, path, method='GET'):
    connection = HTTPConnection('127.0.0.1', port, timeout=5)
    try:
        connection.request(method, path)
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


def check_http(port):
    for path in PUBLIC_FILES:
        status, headers, body = request(port, '/' + path)
        assert status == (301 if path in REDIRECTS else 200), (path, status)
        for name, value in SECURITY_HEADERS.items():
            assert headers.get(name) == value, (path, name)
        assert 'Strict-Transport-Security' not in headers, 'HSTS não deve ser emitido no HTTP local.'
        assert 'Python' not in headers.get('Server', '')
        if path in REDIRECTS:
            assert headers.get('Location') == '/' + REDIRECTS[path], (path, headers.get('Location'))
            continue
        if path.startswith('lang/pt/') and path.endswith('.html'):
            parser = StructuredData()
            parser.feed(body.decode('utf-8'))
            schema = json.loads(parser.content)
            assert schema.get('@context') == 'https://schema.org', path
            graph = schema.get('@graph')
            assert isinstance(graph, list), path
            assert any(node.get('@type') == 'LegalService'
                       or isinstance(node.get('@type'), list) and 'LegalService' in node['@type']
                       for node in graph), path
    for alias, canonical in REDIRECTS.items():
        query = '?origem=teste%20local&via=legado'
        status, headers, body = request(port, '/' + alias + query)
        assert status == 301, (alias, status)
        assert headers.get('Location') == '/' + canonical + query, (alias, headers.get('Location'))
        status, headers, body = request(port, '/' + alias + query, 'HEAD')
        assert status == 301 and body == b'', (alias, status)
        assert headers.get('Location') == '/' + canonical + query, alias
    denied = (
        '/dados.json', '/site-config.json', '/README.md', '/start_server.py',
        '/scripts/build_site.py', '/scripts/site_policy.py', '/.git/config',
        '/.venv/pyvenv.cfg', '/publicacao/barionisociedade-site.zip',
        '/assets/', '/js/', '/css/', '/lang/', '/missing.html',
        '/%2e%2e/README.md', '/assets%5c..%5cdados.json', '/%00.html',
        '/index.html:secret', '/_headers', '/.htaccess',
    )
    for path in denied:
        status, headers, body = request(port, path)
        assert status == 404, (path, status)
        assert headers.get('X-Frame-Options') == 'DENY', path
        assert b'<html' in body, path
    assert request(port, '/')[0] == 200
    assert request(port, '/lang/pt/')[0] == 200
    assert request(port, '/js/contact.js?v=test')[0] == 200
    assert request(port, '/dados.json', 'HEAD')[::2] == (404, b'')
    assert request(port, '/lang/pt/contato.html', 'POST')[0] == 501
    print(f'HTTP: {len(PUBLIC_FILES)} arquivos públicos, {len(REDIRECTS)} redirecionamentos e {len(denied)} caminhos negados verificados.', flush=True)


def check_browser(port):
    base = f'http://127.0.0.1:{port}'
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='msedge', headless=True)
        context = browser.new_context(reduced_motion='reduce')
        external_attempts = []

        def restrict_network(route):
            if route.request.url.startswith(base + '/'):
                route.continue_()
            else:
                external_attempts.append(route.request.url)
                route.abort()

        context.route('**/*', restrict_network)
        context.add_init_script("""window.securityViolations = [];
            document.addEventListener('securitypolicyviolation', event => {
                window.securityViolations.push(event.effectiveDirective);
            });""")
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(base + '/lang/pt/contato.html', wait_until='networkidle')
        assert page.locator('#contactForm').get_attribute('data-contact-ready') == 'true'
        assert page.locator('.navbar').first.get_attribute('data-navigation-ready') == 'true'
        assert not page.evaluate('window.securityViolations'), 'A política bloqueou recursos legítimos.'
        assert not errors, errors

        # O texto do visitante deve permanecer texto, mesmo com sintaxe HTML.
        payload = '<img src=x onerror="window.untrustedMarkupRan=true"> & teste'
        page.evaluate('window.open = (...args) => { window.preparedContact = args; return null; }')
        page.locator('#name').fill(payload)
        page.locator('#phone').fill('(43) 99999-9999')
        page.locator('#subject').select_option(label='Direito Civil')
        page.locator('#message').fill(payload)
        page.locator('button[type="submit"]').click()
        prepared = page.evaluate('window.preparedContact')
        url = urlsplit(prepared[0])
        assert url.scheme == 'https' and url.netloc == 'wa.me'
        assert payload in parse_qs(url.query)['text'][0]
        assert 'noopener' in prepared[2] and 'noreferrer' in prepared[2]
        assert page.evaluate('window.untrustedMarkupRan !== true')

        # Injeções de prova ficam apenas neste navegador descartável.
        page.evaluate("""() => {
            const inline = document.createElement('script');
            inline.textContent = 'window.inlineInjectionRan = true';
            document.body.append(inline);
            const external = document.createElement('script');
            external.src = 'https://csp-test.invalid/payload.js';
            document.body.append(external);
            const frame = document.createElement('iframe');
            frame.src = 'https://csp-test.invalid/frame';
            document.body.append(frame);
            const base = document.createElement('base');
            base.href = 'https://csp-test.invalid/';
            document.head.append(base);
            fetch('/dados.json').catch(() => {});
            const form = document.createElement('form');
            form.method = 'post';
            form.action = '/security-form-probe';
            document.body.append(form);
            form.submit();
        }""")
        page.wait_for_function("""['script-src-elem', 'frame-src', 'base-uri', 'connect-src', 'form-action']
            .every(directive => window.securityViolations.includes(directive))""")
        assert page.evaluate('window.inlineInjectionRan !== true')
        assert page.url == base + '/lang/pt/contato.html'
        assert page.evaluate('document.baseURI') == page.url
        assert not external_attempts, external_attempts

        # Um site de outra origem também não pode colocar o site em um iframe.
        class EmbeddingHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                body = f'<iframe src="{base}/lang/pt/index.html"></iframe>'.encode()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                pass

        # Uma resposta HTTP real evita que a proteção de rede local do Edge
        # bloqueie o teste antes de avaliar o cabeçalho frame-ancestors.
        with preview(EmbeddingHandler) as embedding_port:
            embedding_url = f'http://127.0.0.1:{embedding_port}/'
            context.route(embedding_url, lambda route: route.continue_())
            embed = context.new_page()
            with embed.expect_console_message(predicate=lambda message: 'frame-ancestors' in message.text):
                embed.goto(embedding_url)
            assert not embed.frame_locator('iframe').locator('#conteudo').count()
            embed.close()
        browser.close()
    print('Edge: CSP bloqueou injeções, conexões, formulários e frames; JS autorizado e contato funcionam.', flush=True)


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    with preview() as port:
        check_http(port)
        check_browser(port)
    print('Verificação de segurança concluída. Nenhuma mensagem ou dado enviado a serviços externos.')
