"""Testa a prévia do contato, teclado e movimento reduzido, sem enviar mensagens.

Execute com o servidor local: .venv/Scripts/python.exe scripts/verify_contact_experience.py
"""
import os
import re
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import expect, sync_playwright


BASE = os.environ.get('SITE_TEST_URL', 'http://127.0.0.1:8000').rstrip('/')
PREPARED = re.compile(r'\bis-prepared\b')
VISIBLE = re.compile(r'\bis-visible\b')
COMPLETE = re.compile(r'\bis-complete\b')
CURRENT = re.compile(r'\bis-current\b')


def browser_context(browser, motion, width):
    context = browser.new_context(reduced_motion=motion, viewport={'width': width, 'height': 900})
    context.route('**/*', lambda route: route.continue_()
                  if route.request.url.startswith(BASE + '/') else route.abort())
    context.add_init_script('''window.testOpenings = [];
        window.open = (...args) => { window.testOpenings.push(args); return null; };''')
    return context


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel='msedge', headless=True)
    context = browser_context(browser, 'no-preference', 1440)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(BASE + '/lang/pt/contato.html?area=familia#contactForm')
    experience = page.locator('.contact-experience')
    studio = page.locator('.contact-studio')
    form = page.locator('#contactForm')
    preview = page.locator('[data-contact-preview]')
    progress = form.locator('.contact-progress')
    counter = page.locator('#message-count')
    contact_step = progress.locator('[data-progress-step="contact"]')
    subject_step = progress.locator('[data-progress-step="subject"]')
    message_step = progress.locator('[data-progress-step="message"]')
    experience.scroll_into_view_if_needed()
    expect(experience).to_have_class(VISIBLE)
    expect(preview).to_be_visible()
    expect(progress).to_be_visible()
    assert progress.get_attribute('aria-hidden') == 'true'
    assert preview.get_attribute('aria-live') == 'off'
    assert counter.get_attribute('aria-live') == 'off'
    assert counter.inner_text() == '0 / 2.000'
    expect(contact_step).to_have_class(CURRENT)
    expect(subject_step).to_have_class(COMPLETE)
    assert preview.locator('[data-preview-subject]').inner_text() == 'Gostaria de orientação em Direito de Família.'
    assert not page.evaluate('window.testOpenings')

    name = page.locator('#name')
    phone = page.locator('#phone')
    subject = page.locator('#subject')
    message = page.locator('#message')
    payload = '<img src=x onerror="window.previewInjected=true">'
    name.focus()
    expect(studio).to_have_attribute('data-active-field', 'name')
    name.fill(payload)
    assert preview.locator('[data-preview-greeting]').inner_text() == 'Olá, sou ' + payload + '.'
    assert preview.locator('[data-preview-greeting] img').count() == 0
    page.keyboard.press('Tab')
    expect(phone).to_be_focused()
    expect(studio).to_have_attribute('data-active-field', 'phone')
    phone.fill('abc')
    expect(contact_step).to_have_class(CURRENT)
    expect(contact_step).not_to_have_class(COMPLETE)
    phone.fill('(43) 99999-9999')
    expect(contact_step).to_have_class(COMPLETE)
    expect(message_step).to_have_class(CURRENT)
    page.keyboard.press('Tab')
    expect(subject).to_be_focused()
    expect(studio).to_have_attribute('data-active-field', 'subject')
    subject.select_option(label='Direito Civil')
    page.keyboard.press('Tab')
    expect(message).to_be_focused()
    expect(studio).to_have_attribute('data-active-field', 'message')

    full_message = payload + ' ' + 'Informações importantes sobre a situação. ' * 20 + 'FINAL_DA_MENSAGEM'
    message.fill(full_message)
    expected_count = f'{len(full_message):,}'.replace(',', '.') + ' / 2.000'
    assert counter.inner_text() == expected_count
    excerpt = preview.locator('[data-preview-message]').inner_text()
    assert len(excerpt) <= 180 and excerpt.endswith('…')
    assert 'FINAL_DA_MENSAGEM' not in excerpt
    assert message.input_value() == full_message
    assert preview.locator('[data-preview-message] img').count() == 0
    assert page.evaluate('window.previewInjected !== true')
    assert progress.locator('.is-complete').count() == 3
    assert progress.locator('.is-current').count() == 0
    page.keyboard.press('Tab')
    submit = form.locator('button[type="submit"]')
    expect(submit).to_be_focused()
    assert studio.get_attribute('data-active-field') is None
    submit.press('Enter')
    expect(form).to_have_class(PREPARED)
    openings = page.evaluate('window.testOpenings')
    assert len(openings) == 1
    prepared_message = parse_qs(urlparse(openings[0][0]).query)['text'][0]
    assert prepared_message.endswith('Mensagem: ' + full_message)
    assert 'Assunto: Direito Civil' in prepared_message
    assert 'Revise e envie no WhatsApp' in page.locator('.form-message').inner_text()
    expect(submit).to_be_enabled()

    message.fill('Novo resumo')
    expect(form).not_to_have_class(PREPARED)
    assert page.locator('.form-message a').count() == 0
    page.locator('.contact-info a').first.focus()
    assert studio.get_attribute('data-active-field') is None
    form.evaluate('(element) => element.reset()')
    expect(counter).to_have_text('0 / 2.000')
    expect(contact_step).to_have_class(CURRENT)
    assert progress.locator('.is-complete').count() == 0
    assert subject.input_value() == ''
    assert payload not in preview.inner_text()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    context.close()

    # Com movimento reduzido, a experiência aparece sem animação prolongada.
    reduced = browser_context(browser, 'reduce', 390)
    mobile = reduced.new_page()
    mobile.on('pageerror', lambda error: errors.append(str(error)))
    mobile.goto(BASE + '/lang/pt/contato.html?area=civil')
    expect(mobile.locator('.contact-experience')).to_have_class(VISIBLE)
    mobile.locator('#name').fill('Teste no celular')
    mobile.locator('#phone').fill('(43) 99999-9999')
    mobile.locator('#message').fill('Teste com movimento reduzido.')
    mobile.locator('button[type="submit"]').click()
    expect(mobile.locator('#contactForm')).to_have_class(PREPARED)
    assert mobile.evaluate('''() => document.querySelector('.contact-experience')
        .getAnimations({subtree: true}).filter(animation => animation.playState === 'running'
            && Number(animation.effect.getTiming().duration) > 10).length''') == 0
    assert mobile.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert len(mobile.evaluate('window.testOpenings')) == 1
    reduced.close()

    fallback = browser_context(browser, 'no-preference', 390)
    fallback.add_init_script('window.IntersectionObserver = undefined;')
    fallback_page = fallback.new_page()
    fallback_page.on('pageerror', lambda error: errors.append(str(error)))
    fallback_page.goto(BASE + '/lang/pt/contato.html')
    expect(fallback_page.locator('.contact-experience')).to_have_class(VISIBLE)
    expect(fallback_page.locator('[data-contact-preview]')).to_be_visible()
    expect(fallback_page.locator('button[type="submit"]')).to_be_enabled()
    fallback.close()

    no_js = browser.new_context(java_script_enabled=False, viewport={'width': 390, 'height': 900})
    plain = no_js.new_page()
    plain.goto(BASE + '/lang/pt/contato.html')
    expect(plain.locator('[data-contact-preview]')).to_be_hidden()
    expect(plain.locator('.contact-progress')).to_be_hidden()
    expect(plain.locator('button[type="submit"]')).to_be_disabled()
    expect(plain.locator('#name')).to_be_visible()
    expect(plain.locator('.contact-info a[href^="https://wa.me/"]').first).to_be_visible()
    no_js.close()
    browser.close()
    assert not errors, errors

print('OK: prévia segura, contador, progresso, teclado, envio integral, reset, '
      'movimento reduzido e alternativas sem observador/JavaScript. Sem envio real.')
