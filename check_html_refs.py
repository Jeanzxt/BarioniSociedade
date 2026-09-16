"""Verifica arquivos locais e âncoras das páginas publicadas, sem dependências."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import sys

ROOT = Path(__file__).resolve().parent

class Document(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.refs, self.ids, self.duplicates = [], set(), []
        self.feed(path.read_text(encoding='utf-8-sig'))
    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if 'id' in attrs:
            if attrs['id'] in self.ids: self.duplicates.append(attrs['id'])
            self.ids.add(attrs['id'])
        for key in ('href', 'src'):
            if attrs.get(key): self.refs.append(attrs[key])
        if attrs.get('srcset'):
            self.refs.extend(candidate.strip().split()[0] for candidate in attrs['srcset'].split(',') if candidate.strip())

files = sorted((ROOT / 'lang/pt').glob('*.html')) + [ROOT / 'index.html', ROOT / '404.html']
documents = {file.resolve(): Document(file) for file in files}
errors = []
for file, document in documents.items():
    errors.extend(f'{file.name}: ID duplicado {key}' for key in document.duplicates)
    for ref in document.refs:
        parsed = urlsplit(ref)
        if parsed.scheme or parsed.netloc: continue
        path = ((ROOT / unquote(parsed.path).lstrip('/')) if parsed.path.startswith('/') else (file.parent / unquote(parsed.path))) if parsed.path else file
        if path.is_dir(): path /= 'index.html'
        path = path.resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            errors.append(f'{file.name}: arquivo não encontrado: {ref}')
        elif parsed.fragment and path.suffix == '.html':
            target = documents.get(path) or Document(path)
            if unquote(parsed.fragment) not in target.ids:
                errors.append(f'{file.name}: âncora não encontrada: {ref}')
for error in errors: print(error)
print(f'{len(files)} páginas verificadas; {len(errors)} problemas de referência.')
sys.exit(bool(errors))
