# Repositório GitHub

Este diretório já está organizado para ser a raiz do repositório `Jeanzxt/BarioniSociedade`.

## Estrutura principal

- `assets/` — imagens, ícones e arquivos de marca
- `css/` — folhas de estilo
- `js/` — JavaScript do site
- `lang/pt/` — páginas públicas em português
- `scripts/` — build, empacotamento e verificações
- `publicacao/` — relatório e prévias locais; o ZIP de publicação é gerado sob demanda e ignorado pelo Git
- `index.html`, `404.html`, `robots.txt`, `sitemap.xml` — arquivos da raiz pública

## Antes de enviar

Execute, na raiz do projeto:

```powershell
python check_html_refs.py
python scripts/build_site.py
python check_html_refs.py
```

Para gerar o pacote de hospedagem:

```powershell
python scripts/package_site.py
```

O arquivo `publicacao/barionisociedade-site.zip` não deve ser versionado; ele pode ser regenerado a qualquer momento.
