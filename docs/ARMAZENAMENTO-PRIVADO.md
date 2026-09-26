# Armazenamento privado e revisão antes da publicação

## Configuração opcional do banco e da chave

`RASTREIO_DATA_DIR` define uma pasta absoluta existente para `db.sqlite3` e `.local/django-secret.key`. Sem essa variável, o sistema mantém os caminhos antigos na raiz do projeto. Caminhos relativos, vazios ou inexistentes são rejeitados, sem criação ou mudança automática de destino.

Essa configuração não move dados, não desativa OneDrive e não muda permissões do Windows. Escolha uma pasta que efetivamente esteja fora de sincronização e compartilhamento. Avalie também backups e permissões de acesso. A chave configurada por `DJANGO_SECRET_KEY`, quando presente, continua tendo precedência sobre o arquivo local.

O painel e o receptor móvel devem receber a **mesma configuração**. Caso contrário, podem acessar bancos diferentes. O receptor agora respeita `DJANGO_SECRET_KEY`, sem sobrescrevê-la com o arquivo local.

## Migração de uma instalação existente

Consulte também [Backup e recuperação](BACKUP-RECUPERACAO.md), incluindo verificação somente em leitura e cuidados para não restaurar acessos já revogados.

A migração dos dados reais ainda não foi executada. Para fazê-la em uma janela de manutenção:

1. Encerre o painel, receptor e túnel para evitar gravações durante a cópia.
2. Faça um backup consistente do banco e da chave em local privado. Preserve eventuais arquivos auxiliares SQLite enquanto os serviços estiverem ativos; prefira a API de backup SQLite se houver leitores ou escritores.
3. Crie a pasta de destino e restrinja o acesso ao usuário responsável. Não use pastas públicas ou compartilhadas.
4. Copie o banco para `db.sqlite3` no destino e preserve a chave em `.local/django-secret.key` no destino. Nunca publique esses arquivos.
5. Defina `RASTREIO_DATA_DIR` com o caminho absoluto para todos os processos da aplicação. Não coloque caminhos pessoais ou segredos em configurações versionadas.
6. Execute `manage.py check` e verifique as migrações. Inicie painel e receptor com a mesma variável. Confirme seus cadastros e contagens sem exportar dados.
7. Só após validar a cópia, decida a retenção ou eliminação segura do banco antigo e de suas cópias no serviço de sincronização. Excluir o arquivo local não garante a remoção de versões e backups na nuvem.

Apontar a variável para uma pasta vazia representa uma instalação nova: as migrações criarão um banco vazio. Não interprete a ausência dos cadastros nesse caso como perda do banco antigo. Não altere a variável de um processo em execução esperando que ele recarregue o banco automaticamente.

O endereço temporário, PIDs, binário do túnel e logs de operação continuam em `.local/` do projeto nesta etapa. Continuam ignorados pelo Git, mas devem ser considerados na revisão do OneDrive. Esta configuração separa banco e chave; ainda não migra todo artefato operacional.

## Verificação do conteúdo preparado para commit

Depois de preparar os arquivos desejados com `git add`, execute:

```powershell
.\.venv\Scripts\python.exe scripts/verificar-publicacao.py
```

O verificador lê os objetos do **índice Git**, incluindo arquivos já versionados. Ele bloqueia nomes de arquivos privados, bancos SQLite mesmo renomeados, alguns formatos conhecidos de credenciais, chaves privadas e URLs temporárias de túnel. Mostra apenas nomes e categorias dos problemas; não imprime o conteúdo suspeito. Arquivos de exemplo `.env.example` e `.env.sample` são permitidos, mas também passam pela inspeção de conteúdo.

Código de saída zero indica aprovação apenas pelas regras implementadas; 1 indica achado e 2 falha de execução Git. A revisão humana continua necessária para senhas arbitrárias, coordenadas, nomes, documentos, imagens e demais dados pessoais. Não há garantia de detecção completa nem inspeção automática de todo o histórico Git.

O GitHub Actions também executa a verificação. **Esse passo remoto ocorre depois do envio e não impede a exposição inicial.** A verificação local antes de commit/push é indispensável.

## Proteção antes do commit

O hook `.githooks/pre-commit` foi habilitado nesta instalação em 26/09. Ele executa o verificador antes de criar o commit, incluindo commits feitos pelo Git do VS Code. Usa o Python do ambiente virtual; em outros ambientes, pode usar `python3`, `python` ou o executável indicado por `RASTREIO_PYTHON`. Não envia conteúdo para serviços externos.

Em uma nova cópia, após revisar o script e conferir se já existem hooks que precisam ser preservados:

```powershell
git config --local core.hooksPath .githooks
```

Essa configuração é local ao repositório, não é propagada automaticamente pelo clone e não modifica os hooks globais. Não substitua uma configuração existente sem integrar suas verificações. `.gitattributes` mantém o script de hook com fim de linha LF.

Além dos padrões gerais, a verificação compara os arquivos preparados com a chave local conhecida, a chave fornecida pelo ambiente quando aplicável e o endereço privado do celular. As comparações ficam em memória e os valores não aparecem nas mensagens. Se um arquivo privado existente não puder ser lido, a verificação falha em vez de declarar aprovação incompleta.

Também consulta, em modo somente leitura, tokens da API existentes no banco local configurado. Um token copiado para texto ou nome de arquivo é bloqueado quando corresponde ao valor conhecido. Banco ausente ou sem tabela de tokens não fornece valores adicionais; banco inválido ou inacessível torna a verificação inconclusiva. Tokens antigos, codificados ou de outra instalação podem não ser reconhecidos. O banco nunca é enviado ao GitHub para essa comparação.

Hooks locais podem ser desativados ou contornados pelo próprio usuário e não detectam qualquer dado pessoal arbitrário. A proteção deve ser combinada com revisão manual e controles de acesso. Referência: [documentação de hooks do Git](https://git-scm.com/docs/githooks).

Se algum segredo já tiver sido publicado, removê-lo no commit seguinte não o apaga do histórico. É necessário avaliar revogação/rotação e saneamento do histórico conforme o incidente; não foi constatado um incidente nesta implementação.
