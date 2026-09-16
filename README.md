# BarioniSociedade

Site da Willian Barioni Sociedade de Advocacia.

Esta é a base principal do projeto. O ano de fundação confirmado do escritório é **2024**.

## Abrir no VS Code

Abra **BarioniSociedade.code-workspace** para carregar o projeto com esse nome, ocultar arquivos temporários e selecionar o Python local. O workspace usa caminhos relativos e acompanha a pasta do projeto.

No menu **Terminal → Executar Tarefa**, estão os comandos para iniciar o site, verificar referências e gerar a publicação. **Ctrl+Shift+B** gera o pacote de publicação. Se o servidor já estiver rodando, acesse `http://localhost:8000`.

## Executar

Dê dois cliques em **INICIAR_SERVIDOR.bat** e acesse **http://localhost:8000**. O iniciador usa o ambiente `.venv` quando disponível. A página `index.html` abre o site em `lang/pt/index.html`.

Pelo PowerShell, na pasta do projeto:

```powershell
.\.venv\Scripts\python.exe start_server.py
```

Mantenha o servidor aberto durante o uso. Pressione **Ctrl+C** para encerrá-lo. Para usar outra porta sem abrir o navegador:

```powershell
.\.venv\Scripts\python.exe start_server.py --port 8001 --no-browser
```

O servidor atende apenas neste computador, desativa cache e bloqueia arquivos internos e listagens de diretórios.

## Recursos atuais

- Identidade em azul-marinho e dourado, com monograma WB e efeito ao passar o mouse.
- Menu serifado e layout adaptado para celular, tablet e computador.
- Equipe: Willian Barioni, Daniella Souza, Luiz Carlos Marconato Junior e Fernanda Camargo.
- Transições de saída (160 ms) e entrada (360 ms), respeitando a preferência por movimento reduzido.
- Formulário que prepara uma mensagem para o WhatsApp; o visitante confere e confirma o envio no aplicativo.
- Contato com painel institucional animado, prévia da mensagem durante o preenchimento, progresso e contador de caracteres.
- Links das áreas de atuação preenchem o assunto do contato; no celular, um botão fixo facilita o acesso ao WhatsApp.
- Retratos responsivos em WebP, imagem institucional de compartilhamento e perfis com endereços atualizados.
- Metadados e mapa do site preparados para **https://barionisociedade.com.br**.

## Estrutura

- `lang/pt/`: 11 páginas canônicas e três páginas de compatibilidade para endereços antigos.
- `assets/`: fotos originais, variantes WebP, imagem de compartilhamento, monograma e ícone.
- `css/style.css`: identidade visual e responsividade.
- `css/page-transitions.css`: animações entre páginas.
- `css/contact-experience.css`: painel de contato, animações e composição do formulário.
- `js/`: navegação, transições e formulário de contato.
- `dados.json`: dados do escritório, profissionais e serviços.
- `site-config.json`: configuração do domínio (`base_url` e `nome_dominio`).
- `scripts/build_site.py`: gera páginas com cabeçalho, rodapé e metadados compartilhados.
- `scripts/site_content.py`: valida e formata os dados compartilhados.
- `scripts/prepare_assets.py`: gera imagens; `scripts/assets-state.json` guarda o cache por hashes.
- `scripts/package_site.py`: gera o pacote para publicação.
- `scripts/site_policy.py`: lista dos arquivos públicos e proteções compartilhadas.
- `scripts/hosting_config.py`: configuração de segurança para Apache.
- `scripts/verify_*.py` e `check_html_refs.py`: verificações de conteúdo, navegação, contato e segurança.

## Atualizar conteúdo

Edite `dados.json` para atualizar o escritório, os profissionais e os serviços. Use `site-config.json` somente para o domínio. A estrutura das páginas e os demais textos ficam em `scripts/build_site.py`.

| Dados | Onde editar em `dados.json` |
| --- | --- |
| Fundação e apresentação | `informacoes_escritorio.ano_fundacao`, `nome`, `nome_curto`, `subtitulo`, `descricao` |
| Localização | `endereco`, `bairro`, `cidade`, `estado`, `estado_nome`, `cep`, dentro de `informacoes_escritorio` |
| Atendimento | `telefone`, `whatsapp`, `email`, `redes_sociais` e `horario_funcionamento`, dentro de `informacoes_escritorio` |
| Perfil profissional | `nome`, `funcao`, `especialidade`, `biografia`, `temas`, `formacao`, `inscricao_oab` e `redes_sociais`, em cada item de `advogados` |
| Ordem, endereço e fotos do perfil | `ordem`, `pagina`, `foto` e `imagem_base`, em cada profissional |
| Áreas de atuação | `titulo`, `descricao`, `slug` e `detalhes`, em cada item de `servicos` |

Os horários usam `HH:MM - HH:MM` ou `Fechado`, nos grupos `segunda`, `terca_sexta`, `sabado` e `domingo`. O WhatsApp deve conter apenas dígitos, incluindo país e DDD.

Nos profissionais, cada campo de contato (`telefone`, `whatsapp` e `email`) com valor `null` herda o dado do escritório. Luiz conserva seus contatos específicos. Deixe `formacao` como `[]` e `inscricao_oab` como `null` enquanto não houver informações fornecidas pelo escritório; esses campos vazios não são exibidos.

`pagina` define o nome canônico do HTML; `foto` identifica o JPEG original em `assets/`; `imagem_base` define o prefixo das variantes WebP. Preserve os identificadores existentes, incluindo `id: 1` para o fundador. Novas páginas ou nomes de arquivos exigem atualização deliberada de `PUBLIC_FILES` em `scripts/site_policy.py`; para trocar uma URL existente, atualize também os redirecionamentos.

Para aplicar as alterações:

```powershell
.\.venv\Scripts\python.exe scripts/build_site.py
```

O gerador chama automaticamente `ensure_assets`, de `scripts/prepare_assets.py`. São produzidos WebP de 360 e 720 pixels de largura e `assets/social-card.png`, de 1200 × 630 pixels. Os JPEGs originais ficam disponíveis como alternativa.

O cache em `scripts/assets-state.json` evita regenerações desnecessárias. Alterações nas fotos ou nos dados visuais da imagem institucional, como ano e cidade, exigem **Playwright para Python e Microsoft Edge** no ambiente de desenvolvimento. Com imagens e cache atualizados, o build usa apenas a biblioteca padrão do Python.

Alterações diretas no HTML gerado são substituídas ao executar o gerador. Os links de CSS e JavaScript recebem uma versão baseada no conteúdo, para evitar cache desatualizado.

## Conferir a prévia

Abra [http://localhost:8000](http://localhost:8000) com o servidor rodando. O [relatório da revisão](publicacao/REVISAO.md) reúne as mudanças e as capturas de [celular](publicacao/previa-390.png), [computador](publicacao/previa-1440.png) e [contato](publicacao/previa-contato.png). Esses arquivos ficam em `publicacao/` para revisão local. As capturas registram a versão conferida e não são atualizadas pelo build, servidas pelo servidor ou incluídas no pacote público.

## Verificar

Execute as verificações na pasta do projeto:

```powershell
.\.venv\Scripts\python.exe check_html_refs.py
.\.venv\Scripts\python.exe scripts/verify_site.py
.\.venv\Scripts\python.exe scripts/verify_contact_context.py
.\.venv\Scripts\python.exe scripts/verify_contact_experience.py
.\.venv\Scripts\python.exe scripts/verify_security.py
.\.venv\Scripts\python.exe scripts/verify_content.py
```

- `check_html_refs.py`: referências locais e âncoras.
- `verify_site.py`: páginas em diferentes larguras, imagens responsivas, metadados, redirecionamentos, menu, teclado e formulário.
- `verify_contact_context.py`: assunto selecionado pela área, mensagens de erro acessíveis e alternativa quando a janela do WhatsApp é bloqueada.
- `verify_security.py`: cria seu próprio servidor temporário e verifica acessos, redirecionamentos, cabeçalhos e CSP.
- `verify_content.py`: gera uma cópia temporária do site e altera dados de teste para conferir textos, metadados, contatos herdados, tratamento de caracteres HTML e atualização da imagem institucional. Não altera os dados do projeto.

Os testes `verify_site.py` e `verify_contact_context.py` usam o servidor em `localhost:8000`; `SITE_TEST_URL` permite escolher outra porta. Os testes de navegador e a regeneração de imagem no teste de conteúdo exigem Playwright e Edge. O WhatsApp é interceptado nos testes, sem envio de mensagens.

## Metadados técnicos

O JSON-LD reúne os dados em `@graph`: o escritório usa [LegalService](https://schema.org/LegalService), os perfis usam [ProfilePage](https://schema.org/ProfilePage) com uma pessoa como entidade principal, e os horários usam [openingHoursSpecification](https://schema.org/openingHoursSpecification). As páginas internas incluem a trilha de navegação. Esses dados acompanham `dados.json` e as URLs canônicas do domínio configurado.

## Publicar

```powershell
.\.venv\Scripts\python.exe scripts/package_site.py
```

O pacote contém somente os arquivos públicos autorizados e `.htaccess` com configuração para Apache 2.4. Antes de enviar, siga [PUBLICACAO.md](PUBLICACAO.md) para configurar domínio, certificado, proteções e validar o resultado no provedor. Em outras plataformas, é necessário adaptar a configuração de hospedagem.

Se mudar o domínio, atualize `site-config.json` e gere as páginas e o pacote novamente.

O site está disponível localmente. Domínio, DNS, HTTPS e hospedagem são configurados no provedor; gerar o pacote não envia o site à internet.
