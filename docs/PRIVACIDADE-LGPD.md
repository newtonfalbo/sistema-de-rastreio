# Privacidade e LGPD — requisitos do projeto

Este documento registra requisitos de produto e pontos para revisão jurídica. Não é parecer jurídico, certificação de conformidade ou garantia de ausência de responsabilidade. A aplicabilidade e as obrigações dependem de quem opera o sistema, da finalidade e do contexto real.

## Escopo da validação atual

- Usar dados fictícios ou os próprios dados de adultos participantes voluntários.
- Não utilizar o protótipo para monitoramento oculto, perseguição, coleta sem ciência da pessoa ou para contornar permissões do aparelho.
- O consentimento para abrir o túnel Cloudflare é uma autorização operacional dada pelo desenvolvedor. Não substitui a base legal para tratar dados dos titulares, a transparência ou a regularização de fornecedores.
- Não iniciar uso com terceiros em produção, crianças, empregados ou pessoas em condição de vulnerabilidade sem avaliação específica do contexto e dos requisitos aplicáveis.

## Requisitos antes de disponibilização para terceiros

| Tema | Requisito e situação |
| --- | --- |
| Finalidade e base legal | Documentar finalidade específica, necessidade, dados coletados e hipótese legal adequada a cada operação. Consentimento é uma das bases legais; não é solução automática para todo uso. Pendente de definição do caso de uso e revisão jurídica. |
| Responsáveis | Identificar controlador, operadores, contatos e responsabilidades. O responsável cadastrado de uma pessoa no código não equivale automaticamente ao controlador definido pela LGPD. Pendente. |
| Transparência | Publicar aviso claro com identificação do controlador, finalidade, dados, duração, destinatários e canal de atendimento. Há explicação pontual na tela de envio, mas ainda não há aviso completo de privacidade. |
| Consentimento, quando aplicável | Garantir manifestação livre, informada, específica e demonstrável; registrar versão do aviso, finalidade, manifestação e possibilidade de revogação. O checkbox atual e a permissão do navegador não constituem, sozinhos, implementação completa desse requisito. |
| Minimização | Limitar nome/identificação, dispositivo, coordenadas, precisão e datas ao necessário; evitar CPF, documentos, dados de saúde e localização contínua sem necessidade demonstrada. A coleta atual é pontual. |
| Direitos do titular | Disponibilizar canal e procedimentos de confirmação, acesso, correção, informações sobre compartilhamento, revogação e eliminação nas condições legais. A exclusão pelo responsável na API não substitui um fluxo de direitos do titular. Pendente. |
| Retenção | Definir prazos para posições, tokens, tentativas de login, logs e backups; implementar limpeza e registrar exceções legais. A validade do link não apaga automaticamente o histórico. Pendente. |
| Segurança | Manter controle de acesso, HTTPS, isolamento, segredos fora do código, atualizações, backups e monitoramento. Existem controles técnicos; faltam validação de infraestrutura e procedimentos operacionais completos. |
| Fornecedores e transferência internacional | Avaliar Cloudflare, mapas/CDN, hospedagem e sincronização OneDrive: contratos, papéis, acesso e eventual transferência internacional, com mecanismo jurídico aplicável. HTTPS não elimina essa obrigação. Pendente de revisão. |
| Incidentes | Preparar detecção, contenção, análise de risco, registro e comunicação quando exigida. Ainda não existe plano operacional de incidentes. |
| Crianças e adolescentes | Avaliar melhor interesse e requisitos específicos antes de implementar esse uso. Não inferir que um cadastro feito por familiar autoriza todo rastreamento. Fora da validação inicial. |
| Avaliação de impacto | Avaliar necessidade de relatório de impacto e riscos de exposição de rotinas, locais frequentados e relacionamentos, antes de ampliação de escopo. |

Localização vinculada a uma pessoa é dado pessoal. Não é automaticamente classificada como dado pessoal sensível apenas por ser coordenada, mas seu contexto e combinação podem revelar informações especialmente protegidas e produzir riscos elevados. Essa distinção não reduz a necessidade de proteção.

## Controles já presentes

Autenticação; isolamento por responsável; compartilhamento desativado por padrão; envio pontual com ação e permissão do navegador; links de uso único de 30 minutos; hash do segredo; revogação; receptor público sem painel/histórico; CSRF; no-store; proteção contra tentativas repetidas de login; segredos e banco excluídos do Git.

## Limites conhecidos

- Possuir o link não comprova a identidade do aparelho ou da pessoa. Coordenadas podem ser falsificadas pelo cliente.
- Ainda não há trilha completa de autorização com versão de aviso e finalidade, política automatizada de retenção, canal para direitos ou plano de incidentes.
- O banco e arquivos privados ficam fora do Git, mas a pasta local está em área do OneDrive. A configuração de sincronização precisa ser avaliada; não foi modificada nesta etapa.
- O teste HTTPS temporário não equivale a uma implantação regularizada nem a auditoria de segurança.

## Fontes oficiais consultadas

- [LGPD — Lei nº 13.709/2018, texto compilado](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm): princípios, bases legais, transparência, direitos, tratamento de crianças/adolescentes, transferências e segurança.
- [ANPD — Direitos dos titulares](https://www.gov.br/anpd/pt-br/assuntos/titular-de-dados-1/direito-dos-titulares).
- [ANPD — Guia de agentes de tratamento](https://www.gov.br/anpd/pt-br/assuntos/noticias/nova-versao-do-guia-dos-agentes-de-tratamento).
- [ANPD — Materiais educativos e publicações](https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes), incluindo o guia de segurança da informação.

As definições jurídicas e os documentos finais devem ser revisados por profissional habilitado conforme o público e a operação escolhidos. Não apresentar o produto como “100% conforme à LGPD” com base somente nesses controles.
