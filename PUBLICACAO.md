# Preparação para publicação

O pacote está preparado para **Apache 2.4**, na raiz de `barionisociedade.com.br`. Gerar o pacote mantém o trabalho local; hospedagem, DNS, certificado e envio dos arquivos são etapas no provedor.

## O que já está preparado

- Política de segurança de conteúdo (CSP): permite os scripts, estilos e imagens locais e bloqueia scripts inseridos no HTML, recursos externos, conexões de API, frames e envio tradicional de formulários.
- Proteção contra incorporação do site em páginas de terceiros, identificação incorreta de arquivos e envio do endereço de origem a serviços externos.
- Câmera, microfone, localização e pagamentos desativados no documento.
- Lista explícita de arquivos públicos. Cadastro, scripts Python, documentação e arquivos extras não entram no ZIP e não ficam acessíveis no servidor local.
- Configuração Apache para HTTPS, domínio sem `www`, página 404, compressão de texto e cache. CSS e JavaScript recebem versão pelo conteúdo para atualizar o cache nas mudanças.
- Endereços canônicos atualizados dos profissionais, com redirecionamentos dos três links anteriores. Retratos WebP responsivos e imagem institucional de 1200 × 630 pixels para compartilhamento.
- Política de conteúdo também incluída no HTML como proteção parcial quando o provedor não aplica cabeçalhos. A proteção contra incorporação por outros sites exige o cabeçalho HTTP.
- Formulário sem banco de dados, analytics, cookies de publicidade ou armazenamento local. Ao continuar, o texto é compartilhado com o WhatsApp; o visitante confirma o envio ao escritório no aplicativo.
- Menu sem salto de layout no carregamento, com alternativa funcional se o JavaScript estiver desativado ou falhar.

## Antes de colocar no ar

1. **Escolher a hospedagem.** Para aplicar o pacote atual diretamente, confirmar Apache 2.4, suporte a `.htaccess`, `mod_headers`, `mod_rewrite`, certificado automático e acesso por SFTP ou painel com autenticação em duas etapas. Em outro servidor ou plataforma, adaptar os cabeçalhos de `publicacao/cabecalhos-http.json` e as regras de redirecionamento; enviar o ZIP sozinho não garante que a plataforma interprete `.htaccess`.
2. **Confirmar o domínio.** A configuração usa `barionisociedade.com.br`; isso não confirma que ele foi registrado. Configurar os registros DNS informados pelo provedor para o domínio principal e `www`, sem alterar registros de e-mail existentes.
3. **Emitir o certificado.** Cobrir domínio principal e `www` antes de ativar os redirecionamentos. Quando houver proxy/CDN, manter HTTPS também entre o proxy e a hospedagem. As regras atuais pressupõem TLS na origem; não usar modo de TLS flexível.
4. **Conferir os dados do escritório.** O ano de fundação **2024** já foi confirmado. Endereço, horários, contatos e profissionais são mantidos em `dados.json`; `site-config.json` contém apenas a configuração do domínio. Formação e inscrições de OAB ausentes devem continuar vazias até serem fornecidas pelo escritório. Os contatos específicos de Luiz são preservados; os demais profissionais herdam os contatos do escritório quando os respectivos campos são `null`.
5. **Conferir a privacidade na hospedagem escolhida.** Verificar o que o provedor registra e por quanto tempo. Se futuramente forem adicionados analytics, pixels, chat, login ou um serviço de envio do formulário, revisar a política e a CSP antes de ativá-los.

## Gerar e enviar

Na pasta do projeto:

```powershell
.\.venv\Scripts\python.exe scripts/package_site.py
```

O comando gera as páginas, atualiza as imagens quando necessário, verifica as referências e cria `publicacao/barionisociedade-site.zip`. O pacote atual contém **40 arquivos públicos e `.htaccess`**, totalizando 41 arquivos. A lista inclui 11 páginas canônicas e três páginas para compatibilidade com URLs anteriores.

O ZIP é conferido antes de substituir o pacote anterior. A lista `PUBLIC_FILES`, em `scripts/site_policy.py`, determina o que pode ser servido e publicado. Novos arquivos em `assets/` ou `lang/pt/`, inclusive nomes alterados em `dados.json`, precisam entrar deliberadamente nessa lista.

O build usa `ensure_assets`, de `scripts/prepare_assets.py`, e o cache `scripts/assets-state.json`. Uma foto nova ou uma alteração visual na imagem institucional, como ano ou cidade, exige Playwright e Microsoft Edge no ambiente de desenvolvimento. Com o cache atualizado, o build usa somente a biblioteca padrão do Python.

Extraia o ZIP e envie **seu conteúdo**, incluindo o arquivo oculto `.htaccess`, à pasta pública do domínio (por exemplo, `public_html`). Não envie a pasta inteira do projeto nem a pasta `publicacao`.

`manifesto.json` contém os hashes SHA-256 para conferir a integridade do pacote; não é assinatura digital. `cabecalhos-http.json` é uma referência de configuração para outros servidores. Ambos ficam fora do ZIP público, assim como `previa-390.png`, `previa-1440.png` e `previa-contato.png`. Essas capturas são materiais locais de revisão e não são servidas pelo servidor de prévia.

## Compatibilidade dos endereços

| Endereço anterior em `lang/pt/` | Endereço canônico em `lang/pt/` |
| --- | --- |
| `advogado-maria.html` | `advogada-daniella-souza.html` |
| `advogado-ana.html` | `advogada-fernanda-camargo.html` |
| `advogado-LuizMarconato.html` | `advogado-luiz-marconato.html` |

Apache e servidor local aplicam **HTTP 301**, preservando os parâmetros da URL. O navegador mantém o fragmento de navegação, como `#conteudo`. Em hospedagens estáticas que não interpretem as regras, os HTMLs antigos oferecem redirecionamento por `meta refresh` e um link para o novo perfil. Configure os redirecionamentos HTTP da plataforma para preservar também os parâmetros de consulta nesse cenário.

## Validar no provedor

O servidor Python é apenas uma prévia local. Ele não executa `.htaccess` e não substitui estes testes na hospedagem:

- `https://barionisociedade.com.br` abre o site com certificado válido; HTTP redireciona para HTTPS sem entrar em loop.
- `www` redireciona para o domínio principal e todas as páginas canônicas abrem.
- Os endereços antigos dos profissionais retornam 301 para os perfis corretos, preservando parâmetros; sitemap e links internos usam as URLs canônicas.
- Um endereço inexistente retorna **HTTP 404**, mantendo o visual da página de erro.
- `/dados.json`, `/.git/config`, `/scripts/build_site.py`, `/publicacao/` e listagens de diretórios não ficam acessíveis.
- O navegador recebe `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Permissions-Policy` e `Strict-Transport-Security` no HTTPS.
- O formulário prepara o contato no número correto. Conferir com texto de teste, sem dados reais; o envio ao escritório continua dependendo da confirmação no WhatsApp.
- Menu, animações e fotos continuam funcionando; não há erros de CSP no console durante o uso normal.
- Conferir carregamento em rede móvel, compressão e cache no domínio público; a medição local não representa a velocidade da hospedagem.

Exemplo de inspeção dos cabeçalhos no Windows:

```powershell
curl.exe -I https://barionisociedade.com.br/lang/pt/index.html
curl.exe -I http://barionisociedade.com.br
curl.exe -I https://barionisociedade.com.br/pagina-inexistente
```

## Verificações locais

```powershell
.\.venv\Scripts\python.exe check_html_refs.py
.\.venv\Scripts\python.exe scripts/verify_security.py
.\.venv\Scripts\python.exe scripts/verify_site.py
.\.venv\Scripts\python.exe scripts/verify_contact_context.py
.\.venv\Scripts\python.exe scripts/verify_content.py
```

O teste de segurança cria seu próprio servidor temporário e verifica acessos negados, cabeçalhos, redirecionamentos, bloqueio de scripts e frames e funcionamento do contato. Os testes geral e de contato contextual usam o servidor principal em [localhost:8000](http://localhost:8000), com Playwright e Edge; o WhatsApp é interceptado e nenhuma mensagem é enviada.

O teste de conteúdo trabalha em uma cópia temporária: muda dados, gera páginas e a imagem institucional, e verifica o tratamento de caracteres HTML, os metadados e a herança dos contatos. Ele também precisa de Playwright e Edge para regenerar a imagem de teste. Os dados do projeto permanecem intactos. Veja em [README.md](README.md) os campos editáveis e as referências técnicas dos metadados.

Referências utilizadas: [CSP na MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP), [HSTS na MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Strict-Transport-Security), [cabeçalhos do Apache](https://httpd.apache.org/docs/2.4/mod/mod_headers.html) e [redirecionamentos do Apache](https://httpd.apache.org/docs/2.4/rewrite/remapping.html).
