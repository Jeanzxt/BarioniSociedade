# Melhorias do site — 15 de setembro de 2026

## Resultado

- Ano de fundação mantido em **2024**, com endereço, horários e contatos centralizados em `dados.json`.
- Perfis com temas de atuação, contatos próprios ou herdados e suporte a formação e OAB quando informados.
- URLs atualizadas para Daniella, Fernanda e Luiz; três endereços antigos preservados por redirecionamento.
- Leitura ampliada no celular, enquadramento dos retratos ajustado e botão compacto de WhatsApp.
- Links das áreas abrem o formulário com o assunto selecionado; validação acessível e alternativa quando a janela do WhatsApp é bloqueada.
- Retratos responsivos em WebP e imagem institucional de compartilhamento, atualizados automaticamente pelo gerador.
- Metadados de escritório, horários, profissionais e caminhos das páginas conforme [Schema.org](https://schema.org/LegalService).

## Imagens

| Quatro retratos | Tamanho total | Redução sobre os JPEGs |
| --- | ---: | ---: |
| JPEGs originais, 1080 × 1350 | 578.449 bytes | — |
| WebP, 720 × 900 | 158.074 bytes | 72,7% |
| WebP, 360 × 450 | 61.326 bytes | 89,4% |

O navegador escolhe a versão conforme a tela e sua densidade. Os originais continuam disponíveis como alternativa. Esses números comparam arquivos de imagem; não representam tempo de carregamento em uma hospedagem pública.

## Verificação

- 11 páginas em 7 larguras: **77 combinações**, sem conteúdo ultrapassando a tela ou erros JavaScript.
- Três redirecionamentos preservando parâmetros e fragmentos.
- 39 arquivos públicos e 20 caminhos internos/inexistentes verificados, além dos cabeçalhos e bloqueios de CSP.
- Cinco áreas do formulário, parâmetros inválidos, erros, foco, janela bloqueada e prevenção de abertura duplicada testados com WhatsApp interceptado.
- Dois builds em cópia temporária validaram alteração de dados, herança de contatos, imagem de compartilhamento e tratamento de caracteres especiais.
- Pacote com 40 arquivos, incluindo `.htaccess`, verificado por integridade. Prévia móvel final conferida em 320 e 390 pixels.

## Conferir

- [Site local](http://localhost:8000)
- [Prévia do celular](previa-390.png)
- [Prévia do computador](previa-1440.png)
- [Formulário com área selecionada](previa-contato.png)
- [Pacote de publicação](barionisociedade-site.zip)

Formação, números de OAB ainda ausentes e novos detalhes de trajetória dependem das informações do escritório. Os perfis usam somente os dados disponíveis. Nenhum arquivo foi enviado à hospedagem e nenhuma mensagem foi enviada pelo WhatsApp.
