# Sistema de Rastreio

Backend para cadastrar pessoas e dispositivos, receber coordenadas e consultar o histórico de localização. A aplicação entrega painel web, API REST autenticada e administração Django.

**Não localiza celulares por número, IMEI ou número de série.** Um aplicativo ou dispositivo autorizado precisa obter a localização e enviá-la à API. O painel possui mapa e coleta pontual pelo navegador. Aplicativo móvel, coleta em segundo plano e alertas ainda não estão implementados.

## Executar no Windows / VS Code

Requer Python 3.12 ou 3.13. Execute os comandos na raiz do repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Nesta cópia local o ambiente `.venv` já foi preparado. Se `python` não estiver no PATH, utilize diretamente `.\.venv\Scripts\python.exe` nos comandos seguintes. O ambiente virtual depende do Python usado em sua criação; em outro computador, crie-o novamente com uma instalação própria do Python.

- Painel de acompanhamento: http://127.0.0.1:8000/
- API navegável: http://127.0.0.1:8000/api/
- Login de sessão: http://127.0.0.1:8000/api-auth/login/
- Administração: http://127.0.0.1:8000/admin/

No VS Code, instale as extensões Python e Python Debugger recomendadas pelo projeto. O interpretador está configurado para `.venv`. Use F5 e a configuração **Django: servidor local**. Não há senha padrão nem usuários criados automaticamente.

## Primeiro fluxo

1. Crie o superusuário pelo comando acima e entre no painel administrativo.
2. Crie um usuário comum em **Usuários**, sem marcar equipe ou superusuário.
3. Saia do administrador e entre na API com o usuário comum pelo login de sessão.
4. Em `/api/pessoas/`, cadastre uma pessoa. O responsável é o usuário autenticado.
5. Habilite `compartilhamento_ativo` apenas para o compartilhamento autorizado; o padrão é `false`.
6. Em `/api/dispositivos/`, cadastre um dispositivo usando o UUID da pessoa.
7. Envie uma localização em `/api/localizacoes/` e consulte o histórico e a última posição.

O painel administrativo tem acesso global e os dados de rastreamento são exclusivos de superusuários. A API limita todos os usuários, inclusive superusuários, aos seus próprios cadastros. Um responsável pode cadastrar várias pessoas, e cada pessoa pode ter vários dispositivos.

## Autenticação de integrações

Crie um token para um usuário existente no terminal local:

```powershell
.\.venv\Scripts\python.exe manage.py drf_create_token NOME_DO_USUARIO
```

Envie o cabeçalho `Authorization: Token SEU_TOKEN` nas chamadas da API. O token dá acesso aos dados do responsável, não é uma credencial limitada a um dispositivo. Não o inclua no repositório ou em aplicativos distribuídos. Para renovar/revogar o token anterior, use `drf_create_token -r NOME_DO_USUARIO`. Tokens não expiram automaticamente nesta versão. Use HTTPS fora do ambiente local.

Para uso pelo navegador, a sessão exige CSRF nas operações de escrita; os formulários da API navegável já tratam isso. Não existe cadastro público nem endpoint público de emissão de tokens.

## Endpoints

| Método | Caminho | Função |
| --- | --- | --- |
| GET, POST | `/api/pessoas/` | Listar e cadastrar pessoas |
| GET, PUT, PATCH, DELETE | `/api/pessoas/{id}/` | Consultar, alterar ou excluir uma pessoa |
| GET | `/api/pessoas/{id}/ultima-localizacao/` | Última posição conhecida por data de captura |
| GET, POST | `/api/dispositivos/` | Listar e cadastrar dispositivos |
| GET, PUT, PATCH, DELETE | `/api/dispositivos/{id}/` | Consultar, alterar ou excluir dispositivo |
| GET, POST | `/api/localizacoes/` | Consultar histórico ou registrar coordenadas |
| GET | `/api/localizacoes/{id}/` | Consultar uma localização |

Listas paginadas retornam `count`, `next`, `previous` e `results`, com 50 itens por página. O histórico aceita `pessoa`, `dispositivo`, `inicio` e `fim` como parâmetros. IDs são UUIDs, e datas usam ISO 8601; envie o fuso explicitamente (por exemplo `2026-09-25T14:00:00-03:00`). Os limites de período são inclusivos. A ordenação usa a data de captura, e não a ordem de chegada.

Exemplo de corpo JSON para uma localização (substitua o UUID e a data):

```json
{
  "dispositivo": "UUID_DO_DISPOSITIVO",
  "latitude": "-3.7319000",
  "longitude": "-38.5267000",
  "precisao_metros": 12.0,
  "capturado_em": "2026-09-25T14:00:00-03:00"
}
```

Latitude aceita -90 a 90 e longitude -180 a 180, com até sete casas decimais. A precisão é opcional e não negativa. Capturas mais de cinco minutos no futuro são rejeitadas. O servidor registra `recebido_em` separadamente.

Desativar o dispositivo ou o compartilhamento da pessoa bloqueia novas posições; o histórico já armazenado continua acessível ao responsável. A última posição pode ser antiga: sempre confira `capturado_em`. O indicador de compartilhamento é um controle operacional, não um registro completo de consentimento.

**Exclusão:** apagar uma pessoa remove seus dispositivos e suas localizações; apagar um dispositivo remove seu histórico. Não há lixeira. Registros individuais de localização não podem ser alterados ou apagados pela API. Dispositivos não podem ser transferidos entre pessoas; cadastre outro dispositivo.

## Testes e validação

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test tests -v 2
.\.venv\Scripts\python.exe -m pip check
```

O GitHub Actions executa verificações, migrações e testes em Python 3.12 e 3.13 a cada push ou pull request. Os testes usam banco temporário e dados fictícios.

## Configuração e estrutura

- `config/`: configurações Django, rotas, ASGI e WSGI.
- `rastreamento/`: modelos, migração, serializers, API e administração.
- `tests/`: testes de comportamento, validação e isolamento.
- `.vscode/`: configuração de execução local.
- `requirements.txt`: faixas de dependências diretas.
- `requirements.lock`: versões exatas validadas nesta entrega.
- `docs/REVISAO.md`: relatório de alterações e roteiro para revisão.

SQLite atende ao desenvolvimento local. `.venv`, banco, logs, caches e `.env` ficam fora do Git. Não há carregamento automático de `.env`: defina variáveis no ambiente do processo.

| Variável | Padrão local | Observação |
| --- | --- | --- |
| `DJANGO_DEBUG` | `true` | Use `false` fora do desenvolvimento |
| `DJANGO_SECRET_KEY` | chave pública de desenvolvimento | Obrigatória com debug desligado; use um segredo aleatório |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,[::1]` | Hosts separados por vírgula |

Com debug desligado, o sistema exige HTTPS e cookies seguros. `runserver` é somente para desenvolvimento. Antes de publicar, configure servidor de aplicação, arquivos estáticos, banco e backups, segredo, HTTPS e hosts; execute `manage.py check --deploy` no ambiente de produção. O limite de 120 requisições/minuto por usuário usa cache local e não substitui proteção de infraestrutura.

## Próximas etapas

- Cliente de localização com autorização explícita e credenciais limitadas por dispositivo.
- Evoluir o mapa e contratar/configurar um provedor apropriado à implantação.
- Registro de autorização, retenção de histórico e trilha de auditoria.
- Alertas, recuperação de acesso e monitoramento de falhas.
- PostgreSQL, backups e implantação com HTTPS após validação do fluxo.

Referências: [Django 5.2 LTS](https://www.djangoproject.com/download/) e [autenticação do Django REST Framework](https://www.django-rest-framework.org/api-guide/authentication/).


## Painel web e envio pelo navegador (segunda entrega)

Entre em `http://127.0.0.1:8000/` com sua conta. Cadastre pessoas e dispositivos no próprio painel. O compartilhamento começa desativado e exige confirmação para ativação na interface. Selecione a pessoa para consultar última posição, precisão e histórico paginado (20 registros por página).

Para enviar a posição deste navegador, ative o compartilhamento, selecione o dispositivo correto, marque a autorização e clique em **Obter e enviar minha posição**. A coleta ocorre uma única vez, exige permissão do navegador e utiliza a sessão com CSRF. Não há coleta automática em segundo plano. Após o envio, use **Atualizar o painel**. O ambiente precisa ser HTTPS ou localhost; acessar pelo IP da rede sem HTTPS pode impedir a geolocalização.

O mapa é carregado apenas por solicitação. Leaflet vem de unpkg, e a camada padrão é OpenStreetMap, com atribuição. Na revisão desta máquina o provedor bloqueou imagens de ruas; os pontos foram exibidos, mas a camada cartográfica não pôde ser validada. O histórico funciona independentemente do provedor. Configure `RASTREIO_MAP_TILE_URL` (template XYZ) e `RASTREIO_MAP_ATTRIBUTION` para um provedor autorizado adequado à implantação. Essas configurações são públicas no navegador; não use segredos privados nelas. Não houve contratação de serviço externo.

Testes adicionais de JavaScript, sem dependências npm (Node.js 22):

```powershell
node --test tests/painel.test.cjs
```

Veja [o relatório da segunda entrega](docs/REVISAO-PAINEL.md).

Referências da implementação: [Leaflet](https://leafletjs.com/examples/quick-start/) e [Geolocation API](https://developer.mozilla.org/en-US/docs/Web/API/Geolocation/getCurrentPosition).
