"""Dados e formatação compartilhados; nenhuma página é escrita ao importar."""
from datetime import date
from html import escape
from pathlib import Path
from urllib.parse import quote, urlsplit
import json
import re

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / 'dados.json').read_text(encoding='utf-8-sig'))
OFFICE = DATA['informacoes_escritorio']
SERVICES = DATA['servicos']
LAWYERS = {person['id']: person for person in DATA['advogados']}
if len(LAWYERS) != len(DATA['advogados']):
    raise ValueError('Os identificadores dos profissionais devem ser únicos.')
if 1 not in LAWYERS:
    raise ValueError('Mantenha o profissional fundador com id 1, usado na apresentação do escritório.')
YEAR = OFFICE['ano_fundacao']
if type(YEAR) is not int or not 1800 <= YEAR <= date.today().year:
    raise ValueError('ano_fundacao deve ser um ano válido, sem data futura.')


def validate_contact(number, email):
    if not re.fullmatch(r'[0-9]{10,15}', number):
        raise ValueError('WhatsApp: use de 10 a 15 dígitos, com país e DDD.')
    if not re.fullmatch(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', email):
        raise ValueError('Informe um e-mail válido.')


def contact_for(person):
    return {key: person.get(key) or OFFICE[key] for key in ('telefone', 'whatsapp', 'email')}


def tel(value):
    digits = re.sub(r'\D', '', value)
    if len(digits) in (10, 11):
        digits = '55' + digits
    if not 12 <= len(digits) <= 15:
        raise ValueError('Telefone: informe DDD ou código internacional.')
    return '+' + digits


def secure_url(value):
    url = urlsplit(value)
    if url.scheme != 'https' or not url.hostname or url.username or url.password:
        raise ValueError('As redes sociais devem usar URLs HTTPS sem credenciais.')
    return value


validate_contact(OFFICE['whatsapp'], OFFICE['email'])
tel(OFFICE['telefone'])
for value in OFFICE['redes_sociais'].values():
    secure_url(value)
for person in LAWYERS.values():
    contact = contact_for(person)
    validate_contact(contact['whatsapp'], contact['email'])
    tel(contact['telefone'])
    for key, pattern in (('pagina', r'advogad[oa]-[a-z0-9-]+\.html'),
                         ('foto', r'[a-z0-9-]+\.jpeg'), ('imagem_base', r'[a-z0-9-]+')):
        if not re.fullmatch(pattern, person[key]):
            raise ValueError(f'Nome de arquivo inválido: {key} de {person["nome"]}.')
    for value in person.get('redes_sociais', {}).values():
        secure_url(value)
if len({person['pagina'] for person in LAWYERS.values()}) != len(LAWYERS):
    raise ValueError('As páginas dos profissionais devem ser únicas.')
if len({s['slug'] for s in SERVICES}) != len(SERVICES):
    raise ValueError('Os identificadores das áreas devem ser únicos.')
for service in SERVICES:
    if not re.fullmatch(r'[a-z0-9-]+', service['slug']):
        raise ValueError('Identificador inválido para uma área de atuação.')

ADDRESS = OFFICE['endereco']
LOCALITY = f"{OFFICE['bairro']} · {OFFICE['cidade']}, {OFFICE['estado']} · {OFFICE['cep']}"
REGION = f"{OFFICE['cidade']} e região"
MAP = 'https://www.google.com/maps/search/?api=1&query=' + quote(
    f"{ADDRESS}, {OFFICE['bairro']}, {OFFICE['cidade']} {OFFICE['estado']}, {OFFICE['cep']}"
)
DAY_GROUPS = (
    ('segunda', 'Segunda-feira', ['Monday']),
    ('terca_sexta', 'Terça a sexta-feira', ['Tuesday', 'Wednesday', 'Thursday', 'Friday']),
    ('sabado', 'Sábado', ['Saturday']),
    ('domingo', 'Domingo', ['Sunday']),
)


def hours_range(value):
    if value.casefold() == 'fechado':
        return None
    match = re.fullmatch(r'([0-2][0-9]:[0-5][0-9])\s*-\s*([0-2][0-9]:[0-5][0-9])', value)
    if not match or any(int(t[:2]) > 23 for t in match.groups()) or match[1] >= match[2]:
        raise ValueError('Horários: use HH:MM - HH:MM, com fechamento após abertura, ou Fechado.')
    return match.groups()


def hour_label(value):
    hour, minute = value.split(':')
    return hour + 'h' + (minute if minute != '00' else '')


HOURS_LINES = []
OPENING_HOURS = []
for key, label, days in DAY_GROUPS:
    interval = hours_range(OFFICE['horario_funcionamento'][key])
    text = 'fechado' if interval is None else ' às '.join(map(hour_label, interval))
    HOURS_LINES.append(f'{label}: {text}')
    OPENING_HOURS.append({'@type': 'OpeningHoursSpecification',
                          'dayOfWeek': ['https://schema.org/' + day for day in days],
                          'opens': interval[0] if interval else '00:00',
                          'closes': interval[1] if interval else '00:00'})
HOURS_HTML = '<br>'.join(escape(line) for line in HOURS_LINES)
HOURS_TEXT = '. '.join(HOURS_LINES) + '.'
