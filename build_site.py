"""Gera as páginas estáticas com cabeçalho, rodapé e metadados compartilhados.

Execute com Python 3. Os dados do escritório ficam em dados.json e o domínio
em site-config.json. O site gerado não depende de Python para funcionar.
"""
from pathlib import Path
from html import escape
from urllib.parse import quote, urlparse
from datetime import date
import json
import hashlib
import re

from site_policy import CSP_META, REDIRECTS
from site_content import (DATA, OFFICE, SERVICES, LAWYERS, YEAR, ADDRESS, LOCALITY, REGION,
                          MAP, HOURS_HTML, HOURS_TEXT, OPENING_HOURS, contact_for, tel)
from prepare_assets import ensure_assets

ROOT = Path(__file__).resolve().parent.parent
ensure_assets()
CONFIG = json.loads((ROOT / 'site-config.json').read_text(encoding='utf-8-sig'))
BASE = CONFIG.get('base_url', '').rstrip('/')
if not re.fullmatch(r'https://(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}', BASE):
    raise ValueError('base_url deve conter apenas https:// e o domínio, sem caminho, porta ou credenciais.')
NAME = OFFICE['nome']
PHONE = OFFICE['telefone']
EMAIL = OFFICE['email']
CURRENT_YEAR = date.today().year
NAV = [('index.html', 'Início'), ('sobre.html', 'Escritório'), ('servicos.html', 'Áreas de atuação'), ('advogados.html', 'Equipe'), ('depoimentos.html', 'Como atendemos'), ('contato.html', 'Contato')]
SLUGS = [service['slug'] for service in SERVICES]
DETAILS = [service['detalhes'] for service in SERVICES]
SERVICE_NAMES = ', '.join(service['titulo'] for service in SERVICES)
PROFILE = {person['id']: (person['pagina'], person['foto'], person['funcao'], person['especialidade']) for person in LAWYERS.values()}
STEPS = [
    ('Conte sua situação', 'Explique o que aconteceu, o que precisa resolver e se há algum prazo ou urgência.'),
    ('Entenda as possibilidades', 'A equipe analisa as informações e orienta sobre documentos, alternativas e próximos passos.'),
    ('Acompanhe cada etapa', 'Com o atendimento definido, você recebe orientação sobre as medidas e o andamento do caso.'),
]
FAQS = [
    ('Como agendar o primeiro atendimento?', 'Entre em contato pelo WhatsApp ou preencha a mensagem na página de contato. A equipe orientará sobre o agendamento e a análise inicial.'),
    ('Quais documentos preciso separar?', 'Comece com um breve resumo do caso. Contratos, mensagens ou decisões podem ser úteis; a equipe indicará os documentos necessários conforme a sua situação.'),
    ('Onde fica o escritório?', escape(f"{ADDRESS}, {OFFICE['bairro']}, {OFFICE['cidade']}, {OFFICE['estado_nome']}. Consulte a página de contato para abrir a localização no mapa.")),
    ('Qual é o horário de atendimento?', escape(HOURS_TEXT)),
    ('O formulário já envia minha mensagem?', 'O formulário prepara o texto e abre o WhatsApp. Você confere a mensagem e confirma o envio no próprio WhatsApp.'),
]
PAGES = []

def e(value):
    return escape(str(value), quote=True)

def json_for_html(value):
    # JSON válido não pode encerrar seu <script> ao receber texto como </script>.
    return json.dumps(value, ensure_ascii=False).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')

def security_meta():
    return f'<meta http-equiv="Content-Security-Policy" content="{e(CSP_META)}"><meta name="referrer" content="no-referrer">'

def asset(path):
    version = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()[:10]
    return f'../../{path}?v={version}'

def wa(text='Olá, gostaria de agendar um atendimento jurídico.', number=None):
    return 'https://wa.me/' + (number or OFFICE['whatsapp']) + '?text=' + quote(text)

def arrow():
    return '<span class="arrow" aria-hidden="true">↗</span>'

def button(label='Agendar pelo WhatsApp', href=None, secondary=False):
    href = href or wa()
    external = ' target="_blank" rel="noopener noreferrer"' if href.startswith('https://') else ''
    return f'<a class="btn {"btn-secondary" if secondary else "btn-primary"}" href="{e(href)}"{external}>{e(label)}{arrow()}</a>'

def portrait(person_id, alt, priority=False, card=False):
    person = LAWYERS[person_id]
    prefix = 'assets/' + person['imagem_base']
    sizes = ('(max-width: 360px) calc(100vw - 40px), (max-width: 640px) calc((100vw - 58px) / 2), '
             '(max-width: 900px) calc((100vw - 88px) / 2), (max-width: 1100px) calc((100vw - 124px) / 4), 278px') if card else (
             '(max-width: 640px) calc(100vw - 52px), (max-width: 900px) 44vw, 458px')
    loading = 'fetchpriority="high"' if priority else 'loading="lazy"'
    return f'<picture><source type="image/webp" srcset="{asset(prefix + "-360.webp")} 360w, {asset(prefix + "-720.webp")} 720w" sizes="{sizes}"><img src="{asset("assets/" + person["foto"])}" alt="{e(alt)}" width="1080" height="1350" {loading} decoding="async"></picture>'

def mobile_contact(person=None):
    number = contact_for(person)['whatsapp'] if person else OFFICE['whatsapp']
    message = 'Olá, gostaria de falar com ' + person['nome'] + '.' if person else 'Olá, gostaria de agendar um atendimento jurídico.'
    return f'''<a class="mobile-contact" href="{e(wa(message, number))}" target="_blank" rel="noopener noreferrer" aria-label="Conversar pelo WhatsApp (abre em nova aba)"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true" focusable="false"><path d="M21 11.5a8.5 8.5 0 0 1-12.6 7.4L3 21l1.5-5.3A8.5 8.5 0 1 1 21 11.5Z"/><path d="M8 7.5c0 4.2 2.8 7 7 7l1-2-2-1-1 1a7 7 0 0 1-3-3l1-1-1-2Z"/></svg><span>Conversar no WhatsApp</span></a>'''

def brand():
    mark = (ROOT / 'assets/brand-mark.svg').read_text(encoding='utf-8').replace('role="img" aria-label="Monograma WB — Willian Barioni"', 'class="brand-mark" width="56" height="56" aria-hidden="true" focusable="false"')
    return f'<a class="navbar-brand" href="index.html" aria-label="{e(NAME)} — Início"><span class="brand-emblem">{mark}</span><span class="brand-copy"><strong>{e(OFFICE['nome_curto'])}</strong><small>{e(OFFICE['subtitulo'])}</small></span></a>'

def header(current):
    active = 'advogados.html' if current in {person['pagina'] for person in LAWYERS.values()} else current
    links = ''.join(f'<li><a class="nav-link{" active" if file == active else ""}" href="{file}"' + (' aria-current="page"' if file == current else ' aria-current="location"' if file == active else '') + f'>{label}</a></li>' for file, label in NAV)
    return f'''<a class="skip-link" href="#conteudo">Pular para o conteúdo</a>
<header class="site-header"><nav class="navbar" aria-label="Navegação principal"><div class="navbar-container">
{brand()}<button class="hamburger" type="button" aria-label="Abrir menu de navegação" aria-expanded="false" aria-controls="navMenu"><span></span><span></span><span></span></button>
<ul class="nav-menu" id="navMenu">{links}</ul></div></nav></header>'''

def footer():
    links = ''.join(f'<li><a href="{file}">{label}</a></li>' for file, label in NAV[1:])
    return f'''<footer class="site-footer"><div class="container footer-grid">
<div class="footer-brand">{brand()}<p>Orientação jurídica com clareza,<br>proximidade e responsabilidade.</p><a class="text-link" href="{e(OFFICE['redes_sociais']['instagram'])}" target="_blank" rel="noopener noreferrer">Instagram {arrow()}</a></div>
<div><h2>Explore</h2><ul>{links}</ul></div>
<div class="footer-contact"><h2>Fale com o escritório</h2><a href="tel:{e(tel(PHONE))}">{e(PHONE)}</a><a href="mailto:{e(EMAIL)}">{e(EMAIL)}</a><address>{e(ADDRESS)}<br>{e(LOCALITY)}</address><p>{HOURS_HTML}</p></div>
</div><div class="container footer-bottom"><p>© <span data-current-year>{CURRENT_YEAR}</span> {e(NAME)}</p><a href="privacidade.html">Privacidade</a><a href="#top">Voltar ao topo ↑</a></div></footer>'''

def cta():
    return f'''<section class="contact-band"><div class="container contact-band-inner"><div><span class="eyebrow">Vamos conversar</span><h2>O primeiro passo é<br>entender o seu caso.</h2><p>Fale com a equipe e agende seu atendimento.</p></div>{button()}</div></section>'''

def page(file, title, description, body, cls='', contact=False, person=None):
    canonical = f'{BASE}/lang/pt/{file}'
    office_id = BASE + '/#escritorio'
    social_path = asset('assets/social-card.png').removeprefix('../../')
    image_url = f'{BASE}/{social_path}'
    business = {
        '@type': 'LegalService', '@id': office_id, 'name': NAME,
        'description': f"{OFFICE['descricao']} Desde {YEAR}.",
        'foundingDate': str(YEAR), 'telephone': tel(PHONE), 'email': EMAIL,
        'url': BASE + '/lang/pt/index.html', 'image': image_url,
        'logo': BASE + '/assets/brand-mark.svg',
        'address': {'@type': 'PostalAddress', 'streetAddress': ADDRESS,
                    'addressLocality': OFFICE['cidade'], 'addressRegion': OFFICE['estado'],
                    'postalCode': OFFICE['cep'], 'addressCountry': 'BR'},
        'areaServed': REGION, 'sameAs': list(OFFICE['redes_sociais'].values()),
        'hasMap': MAP, 'openingHoursSpecification': OPENING_HOURS,
    }
    webpage = {'@type': 'ProfilePage' if person else 'WebPage',
               '@id': canonical + '#pagina', 'url': canonical, 'name': title,
               'description': description, 'inLanguage': 'pt-BR',
               'about': {'@id': office_id}, 'primaryImageOfPage': {
                   '@type': 'ImageObject', 'url': image_url, 'width': 1200, 'height': 630}}
    graph = [business, webpage]
    if person:
        person_id = canonical + '#pessoa'
        person_contact = contact_for(person)
        graph.append({'@type': 'Person', '@id': person_id, 'name': person['nome'],
                      'url': canonical, 'description': person['biografia'],
                      'image': BASE + '/assets/' + person['foto'],
                      'jobTitle': person['funcao'], 'knowsAbout': person['temas'],
                      'worksFor': {'@id': office_id}, 'telephone': tel(person_contact['telefone']),
                      'email': person_contact['email'], 'sameAs': list(person.get('redes_sociais', {}).values())})
        webpage['mainEntity'] = {'@id': person_id}
    if file != 'index.html':
        trail = [('Início', BASE + '/lang/pt/index.html')]
        if person:
            trail.append(('Equipe', BASE + '/lang/pt/advogados.html'))
        trail.append((title, canonical))
        breadcrumb_id = canonical + '#caminho'
        graph.append({'@type': 'BreadcrumbList', '@id': breadcrumb_id,
                      'itemListElement': [{'@type': 'ListItem', 'position': i, 'name': label, 'item': url}
                                          for i, (label, url) in enumerate(trail, 1)]})
        webpage['breadcrumb'] = {'@id': breadcrumb_id}
    schema = {'@context': 'https://schema.org', '@graph': graph}
    floating = mobile_contact(person) if file not in ('contato.html', 'privacidade.html') else ''
    body_class = cls + (' has-mobile-contact' if floating else '')
    doc = f'''<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">{security_meta()}<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} | {e(NAME)}</title><meta name="description" content="{e(description)}"><meta name="theme-color" content="#152831">
<meta property="og:type" content="website"><meta property="og:locale" content="pt_BR"><meta property="og:site_name" content="{e(NAME)}"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(description)}"><meta property="og:image" content="{e(image_url)}"><meta property="og:image:type" content="image/png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{e(NAME)} — Desde {YEAR}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{e(image_url)}"><meta name="twitter:image:alt" content="{e(NAME)} — Desde {YEAR}"><link rel="canonical" href="{e(canonical)}"><meta property="og:url" content="{e(canonical)}">
<link rel="icon" href="../../assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="{asset('css/style.css')}"><link rel="stylesheet" href="{asset('css/page-transitions.css')}">{f'<link rel="stylesheet" href="{asset("css/contact-experience.css")}">' if contact else ''}
<script src="{asset('js/nav-bootstrap.js')}"></script><script type="application/ld+json">{json_for_html(schema)}</script><script src="{asset('js/navbar.js')}" defer></script><script src="{asset('js/main.js')}" defer></script>{f'<script src="{asset("js/contact.js")}" defer></script>' if contact else ''}</head>
<body class="{e(body_class.strip())}" id="top">{header(file)}<main id="conteudo" tabindex="-1">{body}</main>{footer()}{floating}</body></html>'''
    (ROOT / 'lang' / 'pt' / file).write_text(doc, encoding='utf-8')
    PAGES.append(file)

def intro(kicker, title, text):
    return f'<section class="page-intro"><div class="container"><div class="breadcrumb"><a href="index.html">Início</a><span aria-hidden="true">/</span><span>{kicker}</span></div><span class="eyebrow">{kicker}</span><h1>{title}</h1><p class="lead">{text}</p></div></section>'

def steps():
    return '<ol class="steps">' + ''.join(f'<li><span class="step-number" aria-hidden="true">0{i}</span><h3>{title}</h3><p>{text}</p></li>' for i, (title, text) in enumerate(STEPS, 1)) + '</ol>'

def faq():
    return '<div class="faq-list">' + ''.join(f'<details><summary>{q}<span aria-hidden="true">+</span></summary><p>{a}</p></details>' for q, a in FAQS) + '</div>'

def team(heading_level=3):
    cards = []
    for person_id in sorted(LAWYERS, key=lambda key: LAWYERS[key].get('ordem', key)):
        person = LAWYERS[person_id]
        file, photo, role, field = PROFILE[person_id]
        cards.append(f'''<article class="team-card"><a href="{file}" class="portrait-link" tabindex="-1" aria-hidden="true">{portrait(person_id, '', card=True)}</a><div class="team-card-body"><span class="eyebrow">{e(role)}</span><h{heading_level}><a href="{file}">{e(person['nome'])}</a></h{heading_level}><p>{e(field)}</p><a class="text-link" href="{file}" aria-label="Conhecer o perfil de {e(person['nome'])}">Conhecer perfil {arrow()}</a></div></article>''')
    return '<div class="team-grid">' + ''.join(cards) + '</div>'

def home():
    rows = ''.join(f'<a href="servicos.html#{slug}" class="practice-row"><span class="row-number">0{i+1}</span><div><h3>{e(service["titulo"])}</h3><p>{e(service["descricao"])}</p></div>{arrow()}</a>' for i, (service, slug) in enumerate(zip(SERVICES, SLUGS)))
    return f'''<section class="home-hero"><div class="container hero-grid"><div class="hero-copy"><span class="eyebrow"><span class="gold-line"></span>{e(OFFICE['cidade'])}, {e(OFFICE['estado_nome'])} · Desde {YEAR}</span><h1>Clareza para decidir.<br><em>Segurança</em><br>para seguir.</h1><p class="lead">Orientação jurídica próxima e cuidadosa para as decisões que importam na sua vida.</p><div class="hero-actions">{button() }<a class="text-link" href="servicos.html">Nossas áreas {arrow()}</a></div><p class="hero-note">Pessoas, famílias e empresas.<br>Uma atenção diferente para cada história.</p></div><figure class="hero-portrait">{portrait(1, LAWYERS[1]['nome'] + ', ' + LAWYERS[1]['funcao'], priority=True)}<figcaption><div><strong>{e(LAWYERS[1]['nome'])}</strong><span>{e(LAWYERS[1]['funcao'])}</span></div><span class="portrait-seal" aria-hidden="true">WB</span></figcaption></figure></div><div class="container hero-bottom"><span>Escuta atenta</span><span>Análise cuidadosa</span><span>Comunicação clara</span><a href="#areas">Conheça o escritório ↓</a></div></section>
<section class="section paper" id="areas"><div class="container split-section"><div class="section-heading"><span class="eyebrow">01 / Áreas de atuação</span><h2>Em diferentes momentos,<br>o mesmo cuidado.</h2><p>Atendimento consultivo e judicial nas principais questões de pessoas, famílias e empresas.</p><a class="text-link" href="servicos.html">Explore nossas áreas {arrow()}</a></div><div class="practice-list">{rows}</div></div></section>
<section class="section office-band"><div class="container office-layout"><div class="office-year"><span class="eyebrow">Nossa trajetória</span><strong>{YEAR}</strong><span>O início de uma história<br>construída em {e(OFFICE['cidade'])}.</span></div><div><span class="eyebrow">02 / O escritório</span><h2>Antes de cada caso,<br>existe uma pessoa.</h2><p>Na {e(NAME)}, o atendimento começa pela escuta. Entendemos o contexto, organizamos as informações e explicamos os caminhos que podem ser avaliados.</p><a href="sobre.html" class="text-link">Conheça nossa forma de atuar {arrow()}</a></div></div></section>
<section class="section paper"><div class="container"><div class="section-heading heading-row"><div><span class="eyebrow">03 / Nossa equipe</span><h2>Pessoas que cuidam<br>do seu atendimento.</h2></div><a class="text-link" href="advogados.html">Conheça a equipe {arrow()}</a></div>{team()}</div></section>
<section class="section method-section"><div class="container"><div class="section-heading heading-row"><div><span class="eyebrow">04 / Como começamos</span><h2>Um caminho claro,<br>desde a primeira conversa.</h2></div><a class="text-link" href="depoimentos.html">Entenda o atendimento {arrow()}</a></div>{steps()}</div></section>
<section class="section paper"><div class="container split-section"><div class="section-heading"><span class="eyebrow">Antes de conversar</span><h2>Suas primeiras<br>perguntas.</h2><p>Informações práticas para organizar o primeiro contato com o escritório.</p></div>{faq()}</div></section>{cta()}'''

page('index.html', f"Advocacia em {OFFICE['cidade']}", f"{OFFICE['descricao']} Atendimento em {OFFICE['cidade']}, {OFFICE['estado']}. Conheça a {NAME}.", home(), 'home-page')

about = intro('O escritório', 'Proximidade na escuta.<br><em>Responsabilidade</em> na atuação.', f"Desde {YEAR}, a {e(NAME)} atende pessoas, famílias e empresas em {e(REGION)}.")
about += f'''<section class="section paper"><div class="container about-layout"><figure class="about-portrait">{portrait(1, LAWYERS[1]['nome'])}<figcaption>{e(LAWYERS[1]['nome'])} · {e(LAWYERS[1]['funcao'])}</figcaption></figure><div class="prose"><span class="eyebrow">Nossa essência</span><h2>Uma orientação que você consegue compreender.</h2><p>O escritório nasceu em {e(OFFICE['cidade'])} com uma proposta: ouvir com atenção, explicar os caminhos possíveis e conduzir cada demanda com cuidado técnico.</p><p>Atuamos em {e(SERVICE_NAMES)}. A análise considera os documentos, as particularidades do caso e os objetivos de quem busca orientação.</p><p>A comunicação faz parte desse trabalho. Nosso compromisso é explicar os próximos passos de forma objetiva e acompanhar as questões que surgem ao longo do atendimento.</p>{button('Conheça a equipe', 'advogados.html', True)}</div></div></section>
<section class="section method-section"><div class="container"><div class="section-heading"><span class="eyebrow">Princípios do atendimento</span><h2>O que orienta nosso trabalho.</h2></div><div class="principles-grid"><article><span class="step-number">01</span><h3>Atenção individual</h3><p>Cada situação é analisada a partir da sua história, dos documentos e das necessidades envolvidas.</p></article><article><span class="step-number">02</span><h3>Clareza</h3><p>Explicações objetivas sobre alternativas, riscos e providências que podem ser avaliadas.</p></article><article><span class="step-number">03</span><h3>Responsabilidade</h3><p>Estudo técnico e acompanhamento cuidadoso na condução das demandas.</p></article></div></div></section>{cta()}'''
page('sobre.html', 'O escritório', f"Conheça a história e a forma de atuação da {NAME}, em {OFFICE['cidade']} desde {YEAR}.", about)

services = intro('Áreas de atuação', 'Orientação para<br>cada <em>momento.</em>', 'Conheça as frentes de atendimento do escritório e encontre a área relacionada à sua situação.')
services += '<section class="section paper"><div class="container services-layout"><nav class="area-nav" aria-label="Áreas de atuação">' + ''.join(f'<a href="#{slug}">{e(service["titulo"])}</a>' for service, slug in zip(SERVICES, SLUGS)) + '</nav><div class="service-details">'
for i, (service, slug, items) in enumerate(zip(SERVICES, SLUGS, DETAILS), 1):
    services += f'<article class="service-detail" id="{slug}"><span class="eyebrow">Área 0{i}</span><h2>{e(service["titulo"])}</h2><p>{e(service["descricao"])}</p><ul class="check-list">' + ''.join(f'<li>{e(item)}</li>' for item in items) + f'</ul><a class="text-link" href="{e(wa("Olá, gostaria de orientação em " + service["titulo"] + "."))}" target="_blank" rel="noopener noreferrer">Conversar sobre esta área {arrow()}</a> <a class="text-link contact-context-link" href="contato.html?area={slug}#contactForm">Preparar mensagem {arrow()}</a></article>'
services += '</div></div></section>' + cta()
page('servicos.html', 'Áreas de atuação', f"{SERVICE_NAMES} em {OFFICE['cidade']}. Conheça as áreas de atendimento do escritório.", services)

people = intro('Nossa equipe', 'Atuação técnica.<br>Atendimento <em>próximo.</em>', 'Conheça os profissionais e suas áreas de atuação no escritório.')
people += '<section class="section paper"><div class="container">' + team(heading_level=2) + '</div></section>' + cta()
page('advogados.html', 'Equipe jurídica', f"Conheça os profissionais da {NAME} e suas áreas de atuação em {OFFICE['cidade']}.", people)

for person_id, person in LAWYERS.items():
    file, photo, role, field = PROFILE[person_id]
    contact_data = contact_for(person)
    phone, number, email = (contact_data[key] for key in ('telefone', 'whatsapp', 'email'))
    register = f'<p class="registration">{e(person["inscricao_oab"])}</p>' if person.get('inscricao_oab') else ''
    social = ''.join(f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(label)} {arrow()}</a>' for label, url in person.get('redes_sociais', {}).items())
    topics = '<ul class="profile-topics">' + ''.join(f'<li>{e(topic)}</li>' for topic in person['temas']) + '</ul>'
    education = '<h2>Formação</h2><ul class="profile-topics">' + ''.join(f'<li>{e(item)}</li>' for item in person['formacao']) + '</ul>' if person.get('formacao') else ''
    content = f'''<section class="section paper profile-section"><div class="container"><nav class="breadcrumb" aria-label="Caminho da página"><a href="index.html">Início</a><span aria-hidden="true">/</span><a href="advogados.html">Equipe</a></nav><div class="profile-layout"><figure class="profile-portrait">{portrait(person_id, person['nome'], priority=True)}</figure><div class="profile-info"><span class="eyebrow">{e(role)}</span><h1>{e(person['nome'])}</h1>{register}<p class="lead">{e(field)}</p><div class="prose"><h2>Trajetória e atuação</h2><p>{e(person['biografia'])}</p><h2>Como pode ajudar</h2>{topics}{education}</div><div class="profile-contact"><h2>Entre em contato</h2><a href="tel:{e(tel(phone))}">{e(phone)}</a><a href="mailto:{e(email)}">{e(email)}</a>{social}</div>{button('Conversar pelo WhatsApp', wa('Olá, gostaria de falar com ' + person['nome'] + '.', number))}<a class="text-link profile-back" href="advogados.html">← Voltar para a equipe</a></div></div></div></section>'''
    page(file, person['nome'], f'Conheça {person["nome"]}. {field}. Atendimento jurídico em {OFFICE["cidade"]}.', content, 'profile-page', person=person)

method = intro('Como atendemos', 'Você entende<br>os <em>próximos passos.</em>', 'Um atendimento organizado para entender a situação, avaliar possibilidades e acompanhar cada etapa.')
method += '<section class="section paper"><div class="container">' + steps() + '</div></section>'
method += f'''<section class="section method-section"><div class="container split-section"><div class="section-heading"><span class="eyebrow">Prepare o primeiro contato</span><h2>Uma boa conversa<br>começa com contexto.</h2><p>Não é preciso conhecer termos jurídicos para buscar orientação.</p></div><div class="prose"><h3>Conte o que aconteceu</h3><p>Organize os fatos principais, as datas relevantes e o que você gostaria de resolver.</p><h3>Informe prazos e urgências</h3><p>Se recebeu uma notificação, intimação ou outro documento com prazo, mencione isso logo no primeiro contato.</p><h3>Aguarde a orientação sobre documentos</h3><p>A equipe indicará quais informações são necessárias para avaliar seu caso.</p></div></div></section><section class="section paper"><div class="container split-section"><div class="section-heading"><span class="eyebrow">Perguntas frequentes</span><h2>Antes do atendimento.</h2></div>{faq()}</div></section>{cta()}'''
page('depoimentos.html', 'Como atendemos', 'Veja como funciona o primeiro atendimento, quais informações preparar e como entrar em contato com a equipe.', method)

contact_mark = (ROOT / 'assets/brand-mark.svg').read_text(encoding='utf-8').replace(
    'role="img" aria-label="Monograma WB — Willian Barioni"',
    'class="contact-monogram" aria-hidden="true" focusable="false"')
contact_options = ''.join(f'<option data-area="{e(service["slug"])}">{e(service["titulo"])}</option>' for service in SERVICES)
contact = intro('Contato', 'Vamos conversar.<br>Com <em>calma e clareza.</em>', 'Cada situação tem seu contexto. Conte o seu, e a equipe orientará os próximos passos.')
contact += f'''<section class="section contact-experience" aria-label="Canais e mensagem de contato">
<div class="container">
<div class="contact-studio">
<aside class="contact-concierge" aria-labelledby="contact-invitation-title">
    <div class="contact-topline"><span class="eyebrow">Atendimento em {e(OFFICE['cidade'])}</span><span class="contact-reference">Desde {YEAR}</span></div>
    <div class="contact-emblem" aria-hidden="true"><span class="contact-orbit"></span>{contact_mark}</div>
    <h2 id="contact-invitation-title">O primeiro passo<br>pode ser <em>simples.</em></h2>
    <p class="contact-invitation">Você traz a sua história.<br>Nós começamos pela escuta.</p>
    <a class="contact-direct" href="{e(wa())}" target="_blank" rel="noopener noreferrer">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true" focusable="false"><path d="M21 11.5a8.5 8.5 0 0 1-12.6 7.4L3 21l1.5-5.3A8.5 8.5 0 1 1 21 11.5Z"/><path d="M8 7.5c0 4.2 2.8 7 7 7l1-2-2-1-1 1a7 7 0 0 1-3-3l1-1-1-2Z"/></svg>
        <span>Prefere conversar direto?<strong>Abrir WhatsApp</strong></span>{arrow()}
    </a>
    <div class="contact-letter" data-contact-preview hidden aria-label="Prévia da sua mensagem">
        <span class="contact-letter-label">Sua mensagem · prévia</span>
        <p data-preview-greeting>Olá, gostaria de atendimento jurídico.</p>
        <p data-preview-subject></p>
        <p data-preview-message>Seu resumo aparece aqui enquanto você escreve.</p>
        <small>Você confere antes de enviar.</small>
    </div>
</aside>
<form id="contactForm" class="contact-form contact-composer" data-whatsapp="{e(OFFICE['whatsapp'])}" aria-labelledby="contact-form-title">
    <header class="contact-composer-heading"><span class="eyebrow">Escreva do seu jeito</span><h2 id="contact-form-title">O que trouxe<br>você até aqui?</h2><p>Um breve resumo já é um começo. Você revisa a mensagem no WhatsApp.</p><small>Os quatro campos são necessários.</small></header>
    <ol class="contact-progress" hidden aria-label="Preenchimento da mensagem">
        <li data-progress-step="contact"><span>01</span><span>Seu contato</span></li>
        <li data-progress-step="subject"><span>02</span><span>Assunto</span></li>
        <li data-progress-step="message"><span>03</span><span>Mensagem</span></li>
    </ol>
    <div class="form-message" role="status" aria-live="polite"></div>
    <div class="contact-chapter">
        <div class="contact-chapter-title"><span aria-hidden="true">01</span><h3>Seu contato</h3></div>
        <div class="form-row">
            <div class="form-group"><label for="name">Como podemos chamar você?</label><input id="name" name="name" type="text" autocomplete="name" placeholder="Seu nome" maxlength="120" required></div>
            <div class="form-group"><label for="phone">Seu WhatsApp</label><input id="phone" name="phone" type="tel" autocomplete="tel" inputmode="tel" placeholder="DDD + número" maxlength="22" required></div>
        </div>
    </div>
    <div class="contact-chapter">
        <div class="contact-chapter-title"><span aria-hidden="true">02</span><h3>O assunto</h3></div>
        <div class="form-group"><label for="subject">Em qual área você busca orientação?</label><select id="subject" name="subject" required><option value="">Selecione uma área</option>{contact_options}<option>Outra situação / ainda não sei</option></select></div>
        <p id="contact-context" class="form-context" hidden></p>
    </div>
    <div class="contact-chapter">
        <div class="contact-chapter-title"><span aria-hidden="true">03</span><h3>Sua mensagem</h3></div>
        <div class="form-group"><label for="message">O que você gostaria de resolver?</label><textarea id="message" name="message" rows="4" maxlength="2000" placeholder="Conte o que aconteceu. Se houver uma data ou um prazo importante, mencione também." required aria-describedby="message-note"></textarea><div class="contact-message-meta"><span class="field-note" id="message-note">Até 2.000 caracteres. Documentos podem ficar para depois da orientação da equipe.</span><output id="message-count" for="message" aria-live="off">0 / 2.000</output></div></div>
    </div>
    <button type="submit" class="btn btn-primary contact-send" disabled>Revisar no WhatsApp <span aria-hidden="true">↗</span></button>
    <p class="form-note">Ao continuar, o texto é compartilhado com o WhatsApp para preparar a conversa. Você confere e confirma o envio ao escritório no aplicativo. Aguarde a orientação da equipe antes de enviar documentos ou informações sensíveis. <a href="privacidade.html">Saiba sobre privacidade.</a></p>
    <noscript><p>Ative o JavaScript para preparar a mensagem. Você também pode usar o link direto de WhatsApp ou os canais abaixo.</p></noscript>
</form>
</div>
<dl class="contact-list contact-details" aria-label="Informações práticas do escritório">
    <div class="contact-detail"><dt>Outros canais</dt><dd><a href="tel:{e(tel(PHONE))}">{e(PHONE)}</a><a href="mailto:{e(EMAIL)}">{e(EMAIL)}</a></dd></div>
    <div class="contact-detail"><dt>Um endereço para conversar</dt><dd><address>{e(ADDRESS)}<br>{e(LOCALITY)}</address><a href="{e(MAP)}" class="text-link" target="_blank" rel="noopener noreferrer">Ver localização {arrow()}</a></dd></div>
    <div class="contact-detail"><dt>Horário de atendimento</dt><dd>{HOURS_HTML}</dd></div>
</dl>
</div></section>'''
page('contato.html', 'Contato e agendamento', f"Fale com o escritório pelo WhatsApp {PHONE}. Endereço, horário e canais de atendimento em {OFFICE['cidade']}, {OFFICE['estado']}.", contact, 'contact-page', True)

privacy = intro('Privacidade', 'Seus dados<br>no <em>atendimento.</em>', 'Informações sobre os canais de contato e o funcionamento deste site.')
privacy += f'''<section class="section paper"><article class="container prose privacy-content"><h2>Informações fornecidas no contato</h2><p>Ao buscar atendimento, você pode informar nome, telefone, e-mail, assunto e um resumo da situação. A equipe pode orientar sobre documentos necessários à análise.</p><h2>Como funciona o formulário</h2><p>O formulário prepara uma mensagem no seu navegador e abre o WhatsApp. Ao continuar, o texto preenchido é compartilhado com o WhatsApp para preparar a conversa. A mensagem só é enviada ao escritório quando você confirma o envio no WhatsApp. O site não possui banco de dados para armazenar as informações do formulário.</p><h2>Finalidade do contato</h2><p>As informações enviadas ao escritório são utilizadas para responder à solicitação, organizar o atendimento e avaliar a demanda apresentada.</p><h2>Serviços externos</h2><p>Os links para WhatsApp, Google Maps, Instagram e outros canais levam a serviços externos, com suas próprias práticas de privacidade. Este site não utiliza ferramentas de publicidade ou análise de visitantes, e suas fontes são carregadas do próprio dispositivo.</p><h2>Dados técnicos de acesso</h2><p>O site não instala cookies de publicidade nem salva o formulário no armazenamento do navegador. A infraestrutura de hospedagem pode registrar dados técnicos de acesso, como endereço IP, página solicitada e horário, para entregar o site e proteger o serviço.</p><h2>Cuidados com documentos</h2><p>Antes de enviar documentos ou informações sensíveis, aguarde a orientação da equipe sobre o canal e os dados necessários.</p><h2>Contato sobre seus dados</h2><p>Para esclarecer dúvidas ou solicitar informações, correções e atualizações relacionadas aos seus dados, entre em contato: <a href="mailto:{e(EMAIL)}">{e(EMAIL)}</a>.</p><p class="field-note">Atualizado em 15 de setembro de 2026.</p></article></section>'''
page('privacidade.html', 'Privacidade', 'Saiba como funciona o formulário de contato, quais serviços externos são utilizados e como esclarecer dúvidas sobre seus dados.', privacy)

for previous, current in REDIRECTS.items():
    target = Path(current).name
    canonical = BASE + '/' + current
    (ROOT / previous).write_text(f'''<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">{security_meta()}<meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="refresh" content="0; URL={e(target)}"><link rel="canonical" href="{e(canonical)}"><meta name="robots" content="noindex"><title>Perfil atualizado | {e(NAME)}</title><link rel="stylesheet" href="{asset('css/style.css')}"></head><body><main class="section"><div class="container prose"><h1>Perfil atualizado</h1><p>O perfil deste profissional tem um novo endereço.</p><a class="btn btn-primary" href="{e(target)}">Acessar perfil {arrow()}</a></div></main></body></html>''', encoding='utf-8')

robots = 'User-agent: *\nAllow: /\n'
if BASE:
    robots += f'Sitemap: {BASE}/sitemap.xml\n'
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(f'  <url><loc>{e(BASE)}/lang/pt/{file}</loc></url>' for file in PAGES) + '\n</urlset>\n'
    (ROOT / 'sitemap.xml').write_text(xml, encoding='utf-8')
(ROOT / 'robots.txt').write_text(robots, encoding='utf-8')
redirect_canonical = f'<link rel="canonical" href="{e(BASE)}/lang/pt/index.html">' if BASE else ''
(ROOT / 'index.html').write_text(f'''<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">{security_meta()}<meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="refresh" content="0; URL=lang/pt/index.html">{redirect_canonical}<title>{e(NAME)}</title><link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="{asset('css/style.css').removeprefix('../../')}"></head><body><main class="section"><div class="container prose"><span class="eyebrow">Advocacia em {e(OFFICE['cidade'])}</span><h1>{e(OFFICE['nome_curto'])}</h1><p>{e(OFFICE['subtitulo'])}</p><a href="lang/pt/index.html" class="btn btn-primary">Acessar o site <span aria-hidden="true">↗</span></a></div></main></body></html>''', encoding='utf-8')
(ROOT / '404.html').write_text(f'''<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">{security_meta()}<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex"><title>Página não encontrada | {e(NAME)}</title><link rel="icon" href="/assets/favicon.svg"><link rel="stylesheet" href="/{asset('css/style.css').removeprefix('../../')}"></head>
<body><main class="section"><div class="container prose"><span class="eyebrow">Erro 404</span><h1>Este caminho<br>não foi encontrado.</h1><p>A página pode ter mudado de endereço. Acesse o início ou fale com o escritório.</p><a class="btn btn-primary" href="/lang/pt/index.html">Voltar ao início <span aria-hidden="true">↗</span></a> <a class="btn btn-secondary" href="/lang/pt/contato.html">Contato</a></div></main></body></html>''', encoding='utf-8')
print(f'{len(PAGES)} páginas geradas. Domínio: {BASE or "aguardando definição"}.')
