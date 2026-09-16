"""Configuração para Apache 2.4, gerada no ZIP de publicação."""
import re
from urllib.parse import urlsplit

from site_policy import HSTS, PUBLIC_FILES, SECURITY_HEADERS, REDIRECTS


def apache_config(base_url):
    host = urlsplit(base_url).hostname
    allowed = '|'.join(re.escape(path) for path in PUBLIC_FILES)
    headers = '\n'.join(f'    Header always set {name} "{value}"' for name, value in SECURITY_HEADERS.items())
    redirects = '\n'.join(f'    RewriteRule ^{re.escape(old)}$ {base_url}/{new} [R=301,L,NE]' for old, new in REDIRECTS.items())
    return f'''# Gerado por scripts/package_site.py. Instalar na raiz pública do domínio.
# Apache 2.4 com AllowOverride e módulos headers/rewrite habilitados.
Options -Indexes -MultiViews
DirectoryIndex index.html
ErrorDocument 404 /404.html
AddDefaultCharset UTF-8

# Os módulos headers e rewrite são obrigatórios: falhar é preferível a publicar
# silenciosamente sem as proteções configuradas.
{headers}
    Header always set Strict-Transport-Security "{HSTS}" "expr=%{{HTTPS}} == 'on'"
    Header set Cache-Control "no-cache"
    <FilesMatch "\\.(css|js)$">
        Header set Cache-Control "public, max-age=31536000, immutable"
    </FilesMatch>
    <FilesMatch "\\.(jpeg|jpg|png|svg|webp|avif|ico)$">
        Header set Cache-Control "public, max-age=86400, must-revalidate"
    </FilesMatch>
    RewriteEngine On
    # Preserva o caminho de validação de certificados do provedor.
    RewriteRule ^\\.well-known/acme-challenge/[A-Za-z0-9_-]+$ - [L]
    # Requer certificado válido e HTTPS no servidor de origem.
    # Com proxy/CDN, usar TLS também na origem (modo estrito), nunca TLS flexível.
    RewriteCond %{{HTTPS}} !=on [OR]
    RewriteCond %{{HTTP_HOST}} !^{re.escape(host)}$ [NC]
    RewriteRule ^ {base_url}%{{REQUEST_URI}} [R=301,L,NE]
    # Verificar depois do HTTPS preserva o caminho solicitado no erro404.
    RewriteRule !^(?:{allowed}|lang/pt/?|)$ - [R=404,L]
{redirects}
    RewriteRule ^$ {base_url}/lang/pt/index.html [R=301,L]

<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/css text/javascript application/javascript application/json application/xml image/svg+xml
</IfModule>
'''
