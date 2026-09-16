"""Verifica contexto e acessibilidade do contato no Edge, sem enviar mensagens.

Com servidor local: .venv/Scripts/python.exe scripts/verify_contact_context.py
SITE_TEST_URL permite escolher outro servidor local.
"""
import os
from urllib.parse import parse_qs, quote, urlparse

from playwright.sync_api import expect, sync_playwright


BASE = os.environ.get('SITE_TEST_URL', 'http://127.0.0.1:8000').rstrip('/')
AREAS = {
    'civil': 'Direito Civil',
    'previdenciario': 'Direito Previdenciário',
    'trabalhista': 'Direito Trabalhista',
    'familia': 'Direito de Família',
    'criminal': 'Direito Criminal',
}


def descriptions(field):
    return (field.get_attribute('aria-describedby') or '').split()


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel='msedge', headless=True)
    context = browser.new_context(reduced_motion='reduce')
    context.route('**/*', lambda route: route.continue_()
                  if route.request.url.startswith(BASE + '/') else route.abort())
    context.add_init_script('''window.testOpenings = [];
        window.open = (...args) => {
            window.testOpenings.push(args);
            throw new Error('Popup bloqueado para teste');
        };''')
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))

    for slug, title in AREAS.items():
        page.goto(BASE + '/lang/pt/contato.html?area=' + slug)
        assert page.locator('#subject').input_value() == title, slug
        note = page.locator('#contact-context')
        assert note.is_visible(), slug
        assert note.inner_text() == f'Você escolheu {title}. Conte brevemente como podemos ajudar.'
        assert 'contact-context' in descriptions(page.locator('#subject'))
        assert note.get_attribute('aria-live') == 'polite'
        assert not page.evaluate('window.testOpenings'), 'A seleção não deve abrir o WhatsApp.'

    payload = '<img src=x onerror="window.untrustedContextRan=true">'
    for invalid in ('', 'desconhecida', 'CIVIL', 'Direito Civil', payload):
        page.goto(BASE + '/lang/pt/contato.html?area=' + quote(invalid, safe=''))
        assert page.locator('#subject').input_value() == '', invalid
        assert page.locator('#contact-context').is_hidden(), invalid
        assert 'contact-context' not in descriptions(page.locator('#subject'))
        assert page.locator('#contact-context img').count() == 0
        assert page.evaluate('window.untrustedContextRan !== true')

    subject = page.locator('#subject')
    subject.select_option(label=AREAS['familia'])
    assert AREAS['familia'] in page.locator('#contact-context').inner_text()
    subject.select_option(label='Outra situação / ainda não sei')
    assert page.locator('#contact-context').is_hidden()
    assert 'contact-context' not in descriptions(subject)
    subject.select_option(label=AREAS['civil'])

    submit = page.locator('button[type="submit"]')
    name = page.locator('#name')
    phone = page.locator('#phone')
    message = page.locator('#message')
    feedback = page.locator('.form-message')
    submit.click()
    assert name.get_attribute('aria-invalid') == 'true'
    assert name.evaluate('(field) => field === document.activeElement')
    feedback_id = feedback.get_attribute('id')
    assert feedback_id in descriptions(name)

    # Alterar um campo diferente deve manter a explicação do erro existente.
    phone.fill('abc')
    assert feedback.is_visible()
    assert name.get_attribute('aria-invalid') == 'true'
    assert feedback_id in descriptions(name)
    name.fill('Teste de contato')
    assert feedback.is_hidden()
    assert name.get_attribute('aria-invalid') is None
    assert feedback_id not in descriptions(name)
    message.fill('Resumo de teste')
    submit.click()
    assert phone.get_attribute('aria-invalid') == 'true'
    assert phone.evaluate('(field) => field === document.activeElement')
    phone.fill('+55 (43) 99999-9999')
    assert feedback.is_hidden()
    assert feedback_id not in descriptions(phone)
    message.fill('')
    submit.click()
    assert message.get_attribute('aria-invalid') == 'true'
    assert 'message-note' in descriptions(message)
    assert feedback_id in descriptions(message)
    message.fill(payload + ' & teste sem envio real.')
    assert 'message-note' in descriptions(message)
    assert feedback_id not in descriptions(message)

    # Configuração ausente ou inválida não pode enviar a um número antigo.
    form = page.locator('#contactForm')
    office_number = form.get_attribute('data-whatsapp')
    for invalid_number in ('', '123', 'https://wa.me/5543999999999'):
        form.evaluate('(form, value) => form.dataset.whatsapp = value', invalid_number)
        submit.click()
        assert not page.evaluate('window.testOpenings')
        assert feedback.get_attribute('role') == 'alert'
        assert 'telefone ou e-mail' in feedback.inner_text()
        assert feedback.evaluate('(note) => note === document.activeElement')
        assert feedback.locator('a').count() == 0
        assert submit.is_enabled()
    form.evaluate('(form, value) => form.dataset.whatsapp = value', office_number)
    submit.click()

    # Mesmo se window.open falhar, o link visível conserva o texto codificado.
    openings = page.evaluate('window.testOpenings')
    assert len(openings) == 1
    prepared_url = urlparse(openings[0][0])
    assert prepared_url.scheme == 'https' and prepared_url.netloc == 'wa.me'
    assert prepared_url.path == '/' + office_number
    prepared_text = parse_qs(prepared_url.query)['text'][0]
    assert payload in prepared_text
    assert 'Assunto: Direito Civil' in prepared_text
    assert 'noopener' in openings[0][2] and 'noreferrer' in openings[0][2]
    assert feedback.locator('a').get_attribute('href') == openings[0][0]
    assert feedback.locator('a').is_visible()
    assert feedback.locator('img').count() == 0
    page.locator('#contactForm').evaluate('(form) => form.requestSubmit()')
    assert len(page.evaluate('window.testOpenings')) == 1
    message.fill('Resumo atualizado')
    assert feedback.is_hidden(), 'Uma alteração precisa remover o link com texto antigo.'
    assert feedback.locator('a').count() == 0
    expect(submit).to_be_enabled()
    assert submit.locator('span').count() == 1

    page.locator('#contactForm').evaluate('(form) => form.reset()')
    expect(page.locator('#contact-context')).to_be_hidden()
    assert subject.input_value() == ''
    assert page.locator('[aria-invalid="true"]').count() == 0
    assert all(feedback_id not in descriptions(page.locator('#' + field))
               for field in ('name', 'phone', 'subject', 'message'))
    assert not errors, errors
    browser.close()

print('OK: 5 áreas, parâmetros inválidos, troca de assunto, erros acessíveis, '
      'configuração inválida, restauração e alternativa ao popup bloqueado. '
      'WhatsApp interceptado; sem envio.')
