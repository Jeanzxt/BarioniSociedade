"""Gera e verifica o pacote público, com configuração de segurança para Apache."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
from zipfile import ZipFile, ZIP_DEFLATED

from hosting_config import apache_config
from site_policy import HSTS, PUBLIC_FILES, SECURITY_HEADERS

root = Path(__file__).resolve().parent.parent
subprocess.run([sys.executable, str(root / 'scripts/build_site.py')], check=True)
subprocess.run([sys.executable, str(root / 'check_html_refs.py')], check=True)
config = json.loads((root / 'site-config.json').read_text(encoding='utf-8-sig'))
payload = {}
for name in PUBLIC_FILES:
    file = root / name
    if not file.resolve().is_relative_to(root.resolve()) or not file.is_file():
        raise RuntimeError(f'Arquivo público ausente ou fora do projeto: {name}')
    payload[name] = file.read_bytes()
payload['.htaccess'] = apache_config(config['base_url'].rstrip('/')).encode('utf-8')
output = root / 'publicacao'
output.mkdir(exist_ok=True)
archive = output / 'barionisociedade-site.zip'
temporary = output / 'barionisociedade-site.zip.tmp'
hashes = {name: hashlib.sha256(content).hexdigest() for name, content in payload.items()}
try:
    with ZipFile(temporary, 'w', ZIP_DEFLATED) as package:
        for name, content in payload.items():
            package.writestr(name, content)
    with ZipFile(temporary) as package:
        if set(package.namelist()) != set(hashes) or package.testzip() is not None:
            raise RuntimeError('Lista ou estrutura de arquivos inválida no pacote.')
        for name, digest in hashes.items():
            if hashlib.sha256(package.read(name)).hexdigest() != digest:
                raise RuntimeError(f'Falha na integridade do arquivo: {name}')
    temporary.replace(archive)
finally:
    temporary.unlink(missing_ok=True)
(output / 'manifesto.json').write_text(json.dumps(hashes, indent=2), encoding='utf-8')
# Referência para provedores que não interpretam .htaccess; não é arquivo público.
(output / 'cabecalhos-http.json').write_text(json.dumps({**SECURITY_HEADERS, 'Strict-Transport-Security': HSTS}, indent=2), encoding='utf-8')
print(f'Pacote verificado: {archive} ({len(payload)} arquivos; {archive.stat().st_size:,} bytes).')
print('Configuração Apache incluída. HTTPS e cabeçalhos devem ser conferidos na hospedagem escolhida. Nenhum arquivo foi publicado na internet.')
