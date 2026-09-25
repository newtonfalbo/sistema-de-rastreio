# Relatório de revisão — primeira versão funcional

Data: 25/09/2026. Ponto de partida: commit `98dae64` (`Criar rastreador.py`).

## Resultado entregue

O esqueleto inicial foi substituído por um backend Django executável, com API REST autenticada, banco SQLite, administração e testes. O objetivo desta etapa é permitir cadastrar pessoas e dispositivos, receber localizações de uma fonte externa autorizada e consultar histórico e última posição conhecida.

A interface entregue é o painel administrativo e a API navegável do Django REST Framework. Não foi criado um aplicativo móvel nem um painel com mapa. Não há rastreamento automático real sem um cliente enviando coordenadas.

## Situação anterior e alterações

| Antes | Agora | Motivo |
| --- | --- | --- |
| README descrevia um projeto Django inexistente | `manage.py` e pacote `config/` com configuração, rotas, ASGI e WSGI | Permitir inicialização real |
| Dependências Flask, requests, geopy e pandas sem uso no fluxo | Django 5.2.17 e DRF 3.16.1, com arquivo de versões exatas | Alinhar dependências ao código e reproduzir a instalação |
| `Pessoa` e `Localizacao` repetidos em três arquivos | Modelos únicos em `rastreamento/models.py` | Evitar divergência e conflitos de registro |
| Vínculo de uma única pessoa por usuário | Um responsável pode cadastrar várias pessoas e dispositivos | Atender ao uso por familiares/responsáveis |
| Rastreador aleatório com erro `sel` | Remoção da simulação; endpoint para receber coordenadas explícitas | Não apresentar coordenadas inventadas como rastreamento |
| Sem banco configurado e sem migrações | SQLite local e migração inicial versionada | Persistir cadastros e histórico |
| Sem autenticação ou isolamento | Sessão com CSRF, token e consultas restritas ao responsável | Impedir acesso cruzado entre usuários |
| Documentação conflitante em duas pastas | README central com instalação, API, regras e limitações | Tornar a revisão reproduzível |
| Sem verificação automatizada | 26 testes e workflow GitHub Actions | Detectar regressões |

A pasta antiga `sistema-de-rastreio/src/` e seus arquivos de exemplo foram removidos do código atual. Eles continuam preservados no histórico Git. Os comandos passam a ser executados na raiz do repositório.

## Arquivos para revisar

| Arquivo/pasta | Responsabilidade |
| --- | --- |
| `manage.py`, `config/settings.py` | Inicialização, banco, autenticação, paginação e configuração por ambiente |
| `config/urls.py` | Rotas da API, login, administração e redirecionamento inicial |
| `config/asgi.py`, `config/wsgi.py` | Entradas para servidores Django |
| `rastreamento/models.py` | Pessoa, dispositivo, localização, relações e restrições de coordenadas |
| `rastreamento/migrations/0001_initial.py` | Criação das tabelas, índice do histórico e restrições no banco |
| `rastreamento/serializers.py` | Validação de payloads, propriedade dos vínculos e filtros |
| `rastreamento/views.py` | Operações da API, isolamento e consulta da última posição |
| `rastreamento/admin.py` | Painel global limitado a superusuários |
| `tests/test_api.py` | Testes de comportamento e segurança de acesso |
| `.github/workflows/tests.yml` | Verificação em Python 3.12 e 3.13 no GitHub |
| `.vscode/` | Interpretador local, extensões recomendadas e depurador Django |
| `.gitignore` | Exclusão de ambiente, banco, caches, logs e arquivos locais do Git |
| `requirements.txt`, `requirements.lock` | Faixas suportadas e versões exatas instaladas |
| `README.md` | Guia de instalação, uso, configuração e próximos passos |

## Regras implementadas

- Cada cadastro pertence ao usuário autenticado. O cliente não escolhe outro responsável pela API.
- IDs usam UUID. A proteção de acesso também filtra o proprietário; não depende de esconder os IDs.
- Relações com pessoas e dispositivos de outros usuários são rejeitadas.
- Um dispositivo não pode ser transferido para outra pessoa, preservando a associação histórica.
- O compartilhamento de uma nova pessoa começa desativado. O responsável precisa habilitá-lo antes de registrar posições.
- Compartilhamento desativado ou dispositivo inativo bloqueia novas posições. O histórico permanece consultável.
- Latitude e longitude têm limites geográficos e até sete casas decimais; precisão precisa ser finita e não negativa.
- Data de captura é obrigatória. Datas mais de cinco minutos no futuro são rejeitadas.
- A data de recebimento é registrada pelo servidor. Posições enviadas com atraso não substituem uma captura mais recente na consulta de última posição.
- Histórico tem filtros por pessoa, dispositivo e período, com paginação de 50 itens.
- A API não permite editar ou excluir individualmente posições. Exclusão de pessoa/dispositivo remove os dados dependentes em cascata; isso está documentado, sem lixeira nesta etapa.
- A API limita inclusive superusuários aos próprios cadastros. A administração global dos dados de rastreamento é exclusiva de superusuários.
- Em desenvolvimento, os hosts padrão são locais. Com debug desligado, a chave secreta é obrigatória e HTTPS/cookies seguros são habilitados.

## Validações executadas nesta máquina

Ambiente: Windows, Python 3.12.14, Django 5.2.17 e Django REST Framework 3.16.1.

| Verificação | Resultado |
| --- | --- |
| `manage.py check` | Nenhum problema identificado |
| `manage.py makemigrations --check --dry-run` | Nenhuma migração pendente |
| `manage.py migrate --noinput` | Migrações aplicadas ao SQLite local |
| `manage.py test tests -v 2` | 26 testes aprovados |
| `python -m pip check` | Nenhuma incompatibilidade de dependências |
| Servidor real via HTTP: login | HTTP 200 com campo CSRF |
| Servidor real via HTTP: API anônima | HTTP 401 |
| Servidor real via HTTP: administração anônima | Redirecionamento para login |
| `manage.py check --deploy --fail-level WARNING` com debug desligado e segredo temporário | Nenhum problema identificado |
| Inicialização com debug desligado e sem segredo | Rejeitada corretamente |

O teste de configuração de produção não representa uma implantação ou auditoria de infraestrutura. O servidor utilizado no teste HTTP foi encerrado ao final. Nenhum serviço ficou publicado na internet.

### Cobertura dos 26 testes

Autenticação ausente, token válido/inválido, usuário inativo, CSRF, atribuição automática do responsável, fluxo completo, isolamento de listas, bloqueio de consulta/alteração/exclusão alheia, vínculos alheios, detalhe de localização alheia, proibição de transferência de dispositivo, coordenadas inválidas, limites geográficos, precisão inválida, data futura/ausente, compartilhamento desativado, dispositivo inativo, ordenação por captura, ausência de localização, filtros válidos, filtros inválidos, imutabilidade individual do histórico, exclusão em cascata, paginação, restrição administrativa e restrição de latitude diretamente no banco.

O workflow foi preparado para executar no GitHub. A confirmação da execução remota deve ser consultada na aba Actions; o resultado local acima está confirmado, e não depende da execução remota.

## Estado local e dados

- Ambiente virtual `.venv` criado usando o Python disponível nesta máquina.
- Banco local inicializado e fora do versionamento.
- Nenhum usuário/senha padrão ou pessoa real foi cadastrado. Os dados fictícios dos testes usam banco temporário, destruído ao final.
- Nenhum token real, banco ou ambiente virtual deve ser enviado ao GitHub.
- O VS Code foi associado à pasta do repositório; a nova configuração aponta para o ambiente virtual.

## Roteiro para revisão amanhã

1. Leia o README e este relatório; revise especialmente as regras de acesso e exclusão.
2. No terminal do VS Code, execute `.\.venv\Scripts\python.exe manage.py test tests -v 2`.
3. Crie sua conta administrativa: `.\.venv\Scripts\python.exe manage.py createsuperuser`.
4. Inicie o servidor: `.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000`.
5. Acesse `http://127.0.0.1:8000/admin/` e crie um usuário comum.
6. Entre com o usuário comum em `http://127.0.0.1:8000/api-auth/login/`.
7. Cadastre uma pessoa com compartilhamento ativo, depois um dispositivo e uma localização usando os formulários da API.
8. Consulte o histórico e `/api/pessoas/{id}/ultima-localizacao/`.
9. Desative o compartilhamento e confirme que uma nova localização é rejeitada.
10. Se quiser validar o isolamento manualmente, use um segundo usuário e confirme que os cadastros do primeiro não aparecem.

## Limitações e decisões para a próxima etapa

1. **Origem da localização:** escolher aplicativo móvel, navegador ou dispositivo GPS. A API recebe dados, mas não comprova que as coordenadas são autênticas.
2. **Credenciais de dispositivos:** o token atual pertence ao responsável e acessa todos os seus cadastros. Criar credenciais específicas, com escopo, expiração e revogação, antes de distribuir um cliente.
3. **Experiência visual:** criar mapa, indicadores de posição antiga e precisão, além de uma interface para familiares.
4. **Autorização e retenção:** o booleano de compartilhamento não substitui o registro de autorização. Definir trilha de auditoria, prazos de retenção e comportamento de exclusão.
5. **Eventos e repetição:** ainda não há deduplicação/idempotência de posições, fila, geocercas ou alertas.
6. **Operação:** SQLite e cache local são adequados à revisão inicial. Avaliar PostgreSQL, cache compartilhado, backups, servidor de aplicação e monitoramento para disponibilização externa.
7. **Validação adicional:** o hardware, permissões de GPS, coleta em segundo plano e desempenho sob carga ainda não foram testados.

A próxima entrega recomendada é um cliente de coleta com autorização explícita, acompanhado de um mapa que mostre claramente quando a posição foi capturada.
