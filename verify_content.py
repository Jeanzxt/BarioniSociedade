"""Verifica edicoes reais de dados em uma copia temporaria, sem alterar o site.

Execute: python scripts/verify_content.py
As verificacoes usam a biblioteca padrao. O build isolado usa Playwright e Edge
para atualizar a imagem institucional; nenhum servico externo e acessado.
"""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, urlsplit
import json
import os
import re
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


class Document(HTMLParser):
    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=True)
        self.text: list[str] = []
        self.main_text: list[str] = []
        self.links: list[tuple[str, bool]] = []
        self.metas: list[dict] = []
        self.scripts: list[tuple[dict, str]] = []
        self.elements: list[tuple[str, dict]] = []
        self.in_main = False
        self.in_style = False
        self.script_attributes = None
        self.script_text: list[str] = []
        self.feed(source)
        self.close()

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attributes = dict(attrs)
        self.elements.append((tag, attributes))
        if tag == 'main':
            self.in_main = True
        elif tag == 'style':
            self.in_style = True
        elif tag == 'script':
            self.script_attributes = attributes
            self.script_text = []
        elif tag == 'a':
            self.links.append((attributes.get('href', ''), self.in_main))
        elif tag == 'meta':
            self.metas.append(attributes)

    def handle_endtag(self, tag: str) -> None:
        if tag == 'main':
            self.in_main = False
        elif tag == 'style':
            self.in_style = False
        elif tag == 'script' and self.script_attributes is not None:
            self.scripts.append((self.script_attributes, ''.join(self.script_text)))
            self.script_attributes = None
            self.script_text = []

    def handle_data(self, data: str) -> None:
        if self.script_attributes is not None:
            self.script_text.append(data)
        elif not self.in_style:
            self.text.append(data)
            if self.in_main:
                self.main_text.append(data)

    @property
    def visible(self) -> str:
        return ' '.join(self.text)

    @property
    def main_visible(self) -> str:
        return ' '.join(self.main_text)

    def schemas(self) -> list:
        return [json.loads(content) for attrs, content in self.scripts
                if attrs.get('type') == 'application/ld+json']


def objects(value):
    """Percorre JSON-LD simples ou com @graph, sem exigir uma forma especifica."""
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from objects(child)


def is_type(node: dict, expected: str) -> bool:
    types = node.get('@type', [])
    return expected in ([types] if isinstance(types, str) else types)


def build(directory: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(directory / 'scripts' / 'build_site.py')],
        cwd=directory,
        env={**os.environ, 'PYTHONUTF8': '1'},
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=60,
    )
    assert result.returncode == 0, f'Build falhou na copia temporaria:\n{result.stdout}\n{result.stderr}'


def documents(directory: Path, people: list) -> dict[str, Document]:
    names = ['index.html', 'sobre.html', 'servicos.html', 'advogados.html',
             'depoimentos.html', 'contato.html', 'privacidade.html']
    names.extend(person['pagina'] for person in people)
    return {name: Document((directory / 'lang' / 'pt' / name).read_text(encoding='utf-8'))
            for name in names}


def require_link(document: Document, expected: str, label: str, main_only=False) -> None:
    links = [link for link, in_main in document.links if in_main or not main_only]
    assert expected in links, f'{label}: link ausente: {expected}'


def verify(directory: Path) -> int:
    original = json.loads((directory / 'dados.json').read_text(encoding='utf-8-sig'))
    build(directory)
    baseline = documents(directory, original['advogados'])
    for name, document in baseline.items():
        assert document.schemas(), f'{name}: JSON-LD ausente no build inicial.'
    original_social = (directory / 'assets' / 'social-card.png').read_bytes()
    portrait_times = {path.name: path.stat().st_mtime_ns
                      for path in (directory / 'assets').glob('*.webp')}

    changed = json.loads(json.dumps(original))
    office = changed['informacoes_escritorio']
    office.update({
        'ano_fundacao': 2021,
        'cidade': 'Maringá',
        'endereco': 'Alameda de Revisão, 321 & Conjunto "B"',
        'bairro': 'Jardim das Letras',
        'cep': '87010-123',
        'telefone': '(44) 98888-7766',
        'whatsapp': '5544977776655',
        'email': 'revisao@example.com',
        'horario_funcionamento': {
            'segunda': '10:15 - 17:45',
            'terca_sexta': '11:30 - 16:15',
            'sabado': '10:00 - 12:30',
            'domingo': 'Fechado',
        },
    })
    bio = ('Biografia de revisão: "escuta" & contexto. '
           '</script><script data-content-probe="1">window.CONTENT_PROBE = true</script>.')
    inherited = next(person for person in changed['advogados'] if person['id'] == 1)
    inherited['biografia'] = bio
    assert all(inherited.get(key) is None for key in ('telefone', 'whatsapp', 'email')), \
        'O profissional escolhido para o teste precisa herdar os contatos do escritorio.'
    specific = next(person for person in changed['advogados'] if person['id'] == 2)
    assert all(specific.get(key) for key in ('telefone', 'whatsapp', 'email')), \
        'Luiz deve manter seus contatos especificos em dados.json.'
    (directory / 'dados.json').write_text(json.dumps(changed, ensure_ascii=False, indent=2), encoding='utf-8')
    build(directory)
    pages = documents(directory, changed['advogados'])
    assert (directory / 'assets' / 'social-card.png').read_bytes() != original_social, \
        'A imagem de compartilhamento deve acompanhar a mudanca do ano e da cidade.'
    assert portrait_times == {path.name: path.stat().st_mtime_ns
                               for path in (directory / 'assets').glob('*.webp')}, \
        'Editar os dados do escritorio nao deve regenerar retratos sem alteracoes.'

    for name, document in pages.items():
        assert office['cidade'] in document.visible, f'{name}: cidade nao atualizada.'
        assert office['endereco'] in document.visible, f'{name}: endereco nao atualizado ou mal escapado.'
        assert office['bairro'] in document.visible, f'{name}: bairro nao atualizado.'
        assert office['cep'] in document.visible, f'{name}: CEP nao atualizado.'
        assert office['telefone'] in document.visible, f'{name}: telefone do rodape nao atualizado.'
        require_link(document, 'tel:+5544988887766', name)
        require_link(document, 'mailto:' + office['email'], name)
        assert original['informacoes_escritorio']['cidade'] not in document.visible, \
            f'{name}: cidade antiga permanece em texto gerado.'
        for meta in document.metas:
            if meta.get('name') == 'description' or meta.get('property') in ('og:title', 'og:description'):
                assert original['informacoes_escritorio']['cidade'] not in meta.get('content', ''), \
                    f'{name}: cidade antiga permanece nos metadados.'
        assert not any('data-content-probe' in attrs for _, attrs in document.elements), \
            f'{name}: biografia injetou um elemento HTML.'
        schema_nodes = list(objects(document.schemas()))
        legal = [node for node in schema_nodes if is_type(node, 'LegalService')]
        assert legal, f'{name}: dados estruturados do escritorio ausentes.'
        for node in legal:
            assert node['address']['addressLocality'] == office['cidade'], f'{name}: cidade antiga no JSON-LD.'
            assert node['address']['streetAddress'] == office['endereco'], f'{name}: endereco incorreto no JSON-LD.'
            assert node['address']['postalCode'] == office['cep'], f'{name}: CEP incorreto no JSON-LD.'
            assert str(node['foundingDate']).startswith(str(office['ano_fundacao'])), f'{name}: fundacao incorreta no JSON-LD.'

    for name in ('index.html', 'sobre.html'):
        assert '2021' in pages[name].main_visible, f'{name}: ano de fundacao nao atualizado.'
        assert str(original['informacoes_escritorio']['ano_fundacao']) not in pages[name].main_visible, \
            f'{name}: ano de fundacao antigo permanece no conteudo.'

    contact = pages['contato.html']
    for hour in ('10:15', '17:45', '11:30', '16:15', '12:30'):
        pattern = re.escape(hour).replace(':', '(?:h|:)')
        assert re.search(pattern, contact.main_visible), f'Contato: horario {hour} nao atualizado.'
    assert any(attrs.get('data-whatsapp') == office['whatsapp'] for tag, attrs in contact.elements if tag == 'form'), \
        'O formulario precisa usar o novo WhatsApp do escritorio.'
    maps = [parse_qs(urlsplit(link).query).get('query', [''])[0]
            for link, _ in contact.links if urlsplit(link).hostname == 'www.google.com']
    assert any(office['endereco'] in query and office['cidade'] in query for query in maps), \
        'O link do mapa nao acompanha a mudanca do endereco.'
    legal = next(node for node in objects(contact.schemas()) if is_type(node, 'LegalService'))
    monday = next((item for item in legal['openingHoursSpecification']
                   if any(str(day).endswith('Monday') for day in item['dayOfWeek'])), None)
    assert monday and monday['opens'] == '10:15' and monday['closes'] == '17:45', \
        'O horario de segunda-feira deve ser atualizado tambem no JSON-LD.'

    inherited_page = pages[inherited['pagina']]
    assert bio in inherited_page.main_visible, 'A biografia editada precisa aparecer integralmente como texto.'
    require_link(inherited_page, 'tel:+5544988887766', inherited['nome'], main_only=True)
    require_link(inherited_page, 'mailto:' + office['email'], inherited['nome'], main_only=True)
    inherited_wa = [urlsplit(link).path.strip('/') for link, in_main in inherited_page.links
                    if in_main and urlsplit(link).hostname == 'wa.me']
    assert office['whatsapp'] in inherited_wa, 'O profissional sem contato proprio deve herdar o novo WhatsApp.'
    for node in objects(inherited_page.schemas()):
        if is_type(node, 'Person') and node.get('name') == inherited['nome']:
            assert bio in node.get('description', ''), 'O JSON-LD do profissional deve preservar sua biografia como dado.'

    specific_page = pages[specific['pagina']]
    assert specific['telefone'] in specific_page.main_visible, 'O telefone proprio de Luiz foi substituido.'
    require_link(specific_page, 'mailto:' + specific['email'], specific['nome'], main_only=True)
    specific_wa = [urlsplit(link).path.strip('/') for link, in_main in specific_page.links
                   if in_main and urlsplit(link).hostname == 'wa.me']
    assert specific['whatsapp'] in specific_wa, 'O WhatsApp proprio de Luiz foi substituido.'
    specific_phone = re.sub(r'\D', '', specific['telefone'])
    if len(specific_phone) in (10, 11):
        specific_phone = '55' + specific_phone
    require_link(specific_page, 'tel:+' + specific_phone, specific['nome'], main_only=True)
    return len(pages)


def main() -> None:
    with TemporaryDirectory(prefix='barioni-content-') as temporary:
        destination = Path(temporary).resolve()
        assert destination != ROOT and ROOT not in destination.parents, 'O teste deve ficar fora do projeto.'
        for folder in ('scripts', 'assets', 'css', 'js'):
            shutil.copytree(ROOT / folder, destination / folder,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for filename in ('dados.json', 'site-config.json'):
            shutil.copy2(ROOT / filename, destination / filename)
        (destination / 'lang' / 'pt').mkdir(parents=True)
        count = verify(destination)
    print(f'Conteudo validado: {count} paginas, dois builds isolados, dados editaveis e contatos preservados.')


if __name__ == '__main__':
    main()
