# Relatório consolidado para revisão e estudo

Data: 25/09/2026. Este documento descreve o estado atual do protótipo e reúne as entregas anteriores. Não contém credenciais, identificadores pessoais, coordenadas reais ou endereços temporários de acesso.

## 1. O que o sistema faz atualmente

Um usuário autenticado cadastra pessoas e seus dispositivos, habilita o compartilhamento e consulta as posições que foram enviadas com autorização. O painel mostra a última captura, precisão, histórico e mapa. O celular pode enviar uma posição por um link temporário com QR Code.

O cadastro de um dispositivo, sozinho, não localiza o aparelho. É necessário abrir o link naquele celular, conferir o vínculo, autorizar e permitir a localização no navegador. O fluxo atual é pontual: não é um aplicativo de rastreamento contínuo, não funciona silenciosamente em segundo plano e não comprova a identidade física do aparelho.

## 2. Etapas entregues

| Etapa | Resultado | Referência |
| --- | --- | --- |
| Backend inicial | Projeto Django executável, banco, API, autenticação, isolamento e 26 testes | Commit `f379f5c`; [relatório inicial](REVISAO.md) |
| Painel web | Cadastro, acompanhamento, histórico, mapa sob demanda e envio pelo navegador | Commit `bbcae52`; [relatório do painel](REVISAO-PAINEL.md) |
| Segurança e celular | Links temporários, QR Code, receptor separado, proteção de login e scripts locais | Commit `cd5da22`; [revisão de celular](REVISAO-CELULAR-SEGURANCA.md) |
| Teste HTTPS e requisitos | Ativação autorizada do túnel, script de encerramento e requisitos de privacidade | Commit `c175bbd`; [privacidade e LGPD](PRIVACIDADE-LGPD.md) |
| Ajuste do mapa | Política de referência das imagens corrigida, versão do JavaScript atualizada e ruas verificadas no navegador | Alterações registradas junto deste relatório |

Os relatórios anteriores descrevem o momento de cada entrega. Por exemplo, a ausência de teste físico de celular e o bloqueio das ruas citados anteriormente tiveram evolução nesta rodada, detalhada na seção 8.

## 3. Dados, regras e API

| Componente | Responsabilidade | Arquivos para estudo |
| --- | --- | --- |
| Pessoa | Pertence a um responsável autenticado; compartilhamento começa desativado | `rastreamento/models.py` |
| Dispositivo | Pertence a uma pessoa; pode estar ativo ou inativo; transferência de vínculo é impedida | `rastreamento/models.py`, `serializers.py` |
| Localização | Guarda latitude, longitude, precisão e horários de captura e recebimento | `rastreamento/models.py` |
| Link temporário | Guarda hash do segredo, validade, revogação e consumo | `rastreamento/models.py`, migração `0002_linkdispositivo.py` |
| Validação | Limites geográficos, precisão válida, horário e propriedade dos vínculos | `rastreamento/serializers.py` |
| API | Cadastro e consulta autenticados; filtros, paginação e última posição | `rastreamento/views.py`, `config/urls.py` |
| Administração | Operação administrativa global restrita a superusuários | `rastreamento/admin.py` |

As consultas da API filtram o responsável, inclusive para contas administrativas. UUID não substitui autorização: o servidor também verifica a propriedade. A data de captura determina a posição mais recente, para que um envio atrasado não substitua uma captura posterior.

As posições não podem ser editadas ou excluídas individualmente pela API atual. Excluir uma pessoa ou dispositivo elimina seus registros dependentes em cascata, sem lixeira. Essa operação exige cuidado e deve ser revista junto da política de retenção e dos direitos do titular.

## 4. Painel web

- Login próprio, saída por POST e páginas privadas.
- Totais de pessoas, dispositivos e posições da pessoa selecionada.
- Cadastro de pessoa e vínculo de dispositivo com validação no servidor.
- Ativação e desativação de compartilhamento; desativar impede novos envios, preservando o histórico.
- Última posição, horário e precisão; indicação de captura antiga.
- Histórico com até 20 registros por página e horários de Fortaleza.
- Mapa carregado por ação do usuário, com aviso sobre o serviço externo.
- Pontos da página, destaque da captura mais recente e círculo de precisão.
- Envio pontual pelo navegador, com permissão, CSRF e mensagens para falhas.
- Bloqueio de cliques simultâneos durante o envio.

Arquivos: `rastreamento/painel.py`, `forms.py`, `templates/rastreamento/painel.html`, `static/rastreamento/painel.js` e `painel.css`.

O painel precisa ser atualizado depois de um envio pelo celular. Não há atualização automática nem rastreamento contínuo nesta versão. O círculo representa a precisão informada pelo navegador, não uma garantia de exatidão.

## 5. Fluxo do celular e QR Code

1. O responsável seleciona pessoa e dispositivo e habilita o compartilhamento.
2. O painel gera um segredo aleatório de 256 bits e um QR Code localmente.
3. O link vale por 30 minutos e permite um envio. Gerar outro revoga o anterior; há revogação manual.
4. O segredo fica no fragmento da URL e é removido da barra pelo JavaScript após leitura. O banco armazena somente seu hash.
5. A página móvel verifica o link e apresenta o vínculo para conferência.
6. A pessoa autoriza explicitamente e concede a permissão de localização do navegador.
7. O servidor valida o vínculo, a situação do compartilhamento e as coordenadas.
8. O consumo do link e a gravação da posição ocorrem na mesma transação. Dados inválidos não consomem o link; reutilização não duplica o registro.
9. O responsável atualiza o painel para consultar a captura.

Arquivos: `rastreamento/celular.py`, templates `celular.html` e `link_dispositivo.html`, arquivos estáticos `celular.js` e `celular.css`.

Possuir o link permite exercer a autorização temporária associada a ele. Por isso, ele deve ser tratado como segredo e entregue somente ao participante correto. A localização enviada pelo cliente pode ser adulterada; o mecanismo não é prova forense de presença.

## 6. Execução local, VS Code e acesso externo

| Parte | Como funciona |
| --- | --- |
| Painel local | Django em `127.0.0.1:8000`; acesso de revisão no computador |
| Receptor móvel | Waitress em `127.0.0.1:8001`, com configuração separada e debug desligado |
| HTTPS temporário | Túnel Cloudflare autorizado, direcionado somente ao receptor móvel |
| Rotas públicas | Página móvel, verificação, envio e recursos estáticos permitidos; sem painel, login, administração ou API de consulta |
| Inicialização | `scripts/iniciar.ps1` verifica o projeto, prepara migrações e inicia o painel |
| Conta | `scripts/criar-conta.ps1`; não há senha padrão publicada |
| Encerramento do teste | `scripts/parar-teste-celular.ps1` confere os processos antes de encerrar receptor e túnel |
| VS Code | `.vscode/` contém configuração do interpretador, depuração e tarefas |

O computador e os processos precisam continuar ligados. O túnel é temporário e seu endereço pode mudar. Não há instalação de serviço de inicialização automática. O servidor de desenvolvimento do painel não é a implantação definitiva de produção.

## 7. Controles de segurança e proteção do repositório

- Isolamento de registros por usuário, autenticação e validação dos vínculos.
- Proteção CSRF nos fluxos de sessão e no receptor móvel.
- Bloqueio de login após cinco falhas por usuário/IP por 15 minutos.
- Cookies de sessão protegidos e configuração de HTTPS em produção.
- Segredo local aleatório; produção rejeita segredo inadequado e hosts indiscriminados.
- Páginas dinâmicas sem cache; permissões de câmera e microfone restringidas.
- Receptor móvel isolado, corpo de requisição limitado e política de conteúdo restrita.
- Links com expiração, revogação, hash e consumo único.
- `.gitignore` exclui `.local/`, `.env`, banco SQLite, logs e ambiente virtual.
- Senha da conta de validação não faz parte do código; o banco guarda o hash de autenticação.

Arquivos de referência: `config/settings.py`, `config/local_secret.py`, `rastreamento/security.py`, `config/mobile_settings.py`, `config/mobile_root_urls.py`, `config/mobile_urls.py` e `.gitignore`.

Excluir do Git não impede sincronização pelo OneDrive. O armazenamento de dados privados fora de pastas sincronizadas continua pendente de definição. Esses controles não substituem auditoria, operação segura ou análise jurídica.

## 8. Diagnóstico e correção do mapa nesta rodada

O usuário relatou que o QR Code não resultava em localização no mapa. A verificação encontrou uma posição registrada e um link consumido: o fluxo de envio do celular havia funcionado. O problema visível era a camada de imagens de ruas, que mostrava uma mensagem de bloqueio do OpenStreetMap.

A política global `same-origin` não enviava referência nas requisições externas das imagens. A política dos servidores públicos do OpenStreetMap exige identificação adequada da origem em aplicações web. Foi aplicada a opção Leaflet `referrerPolicy: "origin"` somente à camada de imagens. Ela envia a origem do painel, sem caminho, parâmetros ou identificador da pessoa no cabeçalho Referer. O provedor continua recebendo IP e região visualizada, conforme aviso no painel.

Também foi versionado o endereço do JavaScript do painel e reiniciado o servidor local, pois a página ainda utilizava o código anterior. Não foram alterados links do celular, dados de localização ou a política restritiva do receptor móvel.

Resultado observado: imagens das ruas e marcador da posição carregaram no navegador após a correção; os elementos de imagem apresentaram a política `origin`. A disponibilidade futura depende do provedor e do cumprimento de sua política. Não foi implementado mecanismo para contornar bloqueios.

Arquivos alterados nesta correção: `rastreamento/static/rastreamento/painel.js` e `rastreamento/templates/rastreamento/painel.html`.

O projeto já permite configurar `RASTREIO_MAP_TILE_URL` e `RASTREIO_MAP_ATTRIBUTION`. MapTiler e Mapbox são alternativas com credenciais e condições próprias. Não foi criada conta, contratada assinatura ou feita migração. Uma troca exige avaliar compatibilidade, atribuição, limites, custos e privacidade. Chaves destinadas ao navegador são visíveis ao cliente e devem ter restrições de origem e escopo; segredos de servidor nunca devem ir ao frontend.

Fontes: [política de imagens do OpenStreetMap](https://operations.osmfoundation.org/policies/tiles/), [referência Leaflet](https://leafletjs.com/reference.html#tilelayer-referrerpolicy), [chaves MapTiler](https://docs.maptiler.com/guides/credentials/api-key/) e [tokens Mapbox](https://docs.mapbox.com/accounts/guides/tokens/).

## 9. Testes e evidências

| Verificação | Resultado e alcance |
| --- | --- |
| Suíte Django na entrega anterior | 67 testes aprovados: API, painel, segurança e fluxo móvel |
| Suíte JavaScript na entrega anterior | 12 testes aprovados, com geolocalização simulada |
| Verificações anteriores de configuração | Django, migrações, dependências e configuração de produção verificados conforme relatório de celular |
| Rotas externas anteriores | Página e script móvel com HTTP 200; login, administração e API privada com HTTP 404 |
| Teste realizado pelo usuário | Uma posição recebida e um link utilizado confirmados no banco, sem exportar as coordenadas |
| Correção atual | 12 testes JavaScript reexecutados e aprovados (painel e celular); verificação visual das ruas e marcador no navegador |

Não se deve interpretar testes simulados como validação de todos os celulares. Permanecem necessários testes de precisão, permissão negada, sinal ruim e compatibilidade em aparelhos reais distintos. A suíte Python não foi reexecutada nesta alteração de JavaScript/template/documentação; os totais anteriores são evidência histórica, não uma nova execução.

## 10. Pendências e prioridades de revisão

| Prioridade | Próximo trabalho | Critério para considerar concluído |
| --- | --- | --- |
| Alta, antes de terceiros | Finalidade, base legal, responsáveis e aviso de privacidade | Documentos adequados ao caso de uso e revisados por profissional habilitado |
| Alta | Registro da autorização e versão do aviso | Evidência demonstrável da manifestação e finalidade, além do checkbox atual |
| Alta | Retenção e direitos do titular | Prazos definidos, limpeza implementada e canal/procedimentos de atendimento |
| Alta, antes de produção | Hospedagem HTTPS definitiva e proteção operacional | Backups testados, monitoramento, limites contra abuso e plano de incidentes |
| Alta | Armazenamento privado | Decisão sobre OneDrive, localização do banco e acesso aos backups |
| Média | Testes móveis adicionais | Validar outros aparelhos, expiração, revogação, permissão negada e precisão |
| Média | Qualidade do painel | Corrigir textos com acentuação danificada observados na seção de links; melhorar filtros e atualização |
| Média | Provedor cartográfico definitivo | Escolha baseada em volume previsto, disponibilidade, custo e termos |
| Futura | Credenciais duradouras por dispositivo ou app | Projeto específico de segurança, autorização e consumo de bateria; não incluído no protótipo atual |

O documento [Privacidade e LGPD](PRIVACIDADE-LGPD.md) detalha as pendências legais. O sistema não deve ser apresentado como certificado ou integralmente conforme à LGPD com base somente nos controles implementados.

## 11. Roteiro sugerido para estudar e revisar

1. Leia este relatório e o `README.md` para entender o fluxo completo.
2. Estude os modelos, depois serializers e views: dados, regras e autorização.
3. Revise o painel e seu JavaScript, distinguindo obtenção de coordenadas de carregamento do mapa.
4. Acompanhe o fluxo móvel em `celular.py` e `celular.js`, especialmente expiração, revogação e consumo.
5. Leia os testes correspondentes antes de modificar regras.
6. Faça testes apenas com dados fictícios ou próprios dados autorizados; confira o vínculo antes de enviar.
7. Compare os resultados com as pendências acima e registre as decisões de produto.

Para repetir os testes: `.\.venv\Scripts\python.exe manage.py test` e `node --test tests/*.test.cjs`, com Node disponível no PATH. Os testes automatizados usam dados de teste; não é necessário divulgar o banco local para revisar o código.
