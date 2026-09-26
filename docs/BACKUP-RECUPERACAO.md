# Backup e recuperação do protótipo

## Situação atual

Há cópias privadas anteriores às migrações desta sessão. Dois arquivos passaram na verificação de integridade, referências e presença de tabelas em 26/09/2026. Não foi restaurado nenhum banco real sobre a instalação em uso. Não há agendamento de backup, prazo de retenção definido ou garantia de recuperação completa.

Foi concluído um **ensaio funcional com dados inteiramente fictícios**, em processos e pastas temporárias: migrações, cadastro de duas contas, posição com registro de autorização, backup, restauração em outro banco, invalidação de acessos restaurados, novo login e conferência de isolamento entre contas. A origem e o backup permaneceram byte a byte iguais após a validação da cópia restaurada. Isso não substitui o ensaio privado de recuperação da instalação real, de suas chaves e do ambiente de destino.

Para repetir esse ensaio isolado:

```powershell
.\.venv\Scripts\python.exe manage.py test tests.test_restauracao
```

O teste gera credenciais fictícias temporárias e não abre servidor HTTP ou túnel. Não recebe o caminho de um banco real e não executa suas exclusões de credenciais sobre a instalação em uso.

## O que preservar

- Banco SQLite consistente, incluindo cadastros, hashes de senha, tokens, sessões e histórico. O backup deve receber proteção equivalente à dos dados originais.
- Segredo da instalação, em arquivo privado separado ou no mecanismo usado para `DJANGO_SECRET_KEY`. Não incluir o segredo em manifestos, comandos públicos ou relatórios.
- Referência do commit da aplicação, versões instaladas e estado das migrações. Registrar horário e resultado da cópia, sem listar pessoas ou coordenadas.
- Registro operacional privado das exclusões e revogações posteriores ao backup, para não desfazê-las involuntariamente numa recuperação.

Escolher armazenamento restrito, fora do Git e das pastas sincronizadas/compartilhadas não aprovadas. Avaliar criptografia, permissões e acesso à chave de recuperação. As cópias atuais em `.local/` ainda estão dentro da árvore do projeto no OneDrive; `.gitignore` não controla essa sincronização. Nenhuma configuração de nuvem foi alterada.

## Criar e verificar uma cópia

Use a API de backup do SQLite para obter uma cópia consistente. Uma cópia simples do arquivo enquanto há gravações pode não conter o estado esperado, especialmente com arquivos auxiliares. A API substitui o conteúdo do destino: selecione um arquivo novo, nunca o banco ativo. [Documentação do SQLite](https://www.sqlite.org/backup.html).

O verificador fornecido recebe o caminho de uma cópia existente:

```powershell
.\.venv\Scripts\python.exe scripts/verificar-backup.py 'CAMINHO_PRIVADO_DO_BACKUP.sqlite3'
```

Substitua o exemplo pelo caminho privado. O script abre em modo somente leitura, não cria arquivo ausente, não restaura e não imprime registros. Código de saída zero indica que passaram `integrity_check`, `foreign_key_check` e a presença das tabelas básicas do projeto. Falha retorna código 1 e mensagem genérica. O `foreign_key_check` é necessário porque a verificação de integridade não cobre essas violações. [Referência dos PRAGMAs](https://www.sqlite.org/pragma.html#pragma_integrity_check).

Esse resultado não comprova atualidade do backup, completude de colunas/migrações, validade da chave, autenticidade da origem ou correção dos dados de negócio. Não aceite um arquivo de procedência desconhecida apenas porque passou no teste.

## Ensaiar recuperação sem afetar o ambiente em uso

1. Reservar uma pasta privada separada, inicialmente vazia, e uma cópia de trabalho do backup; manter o original preservado. Preparar a versão compatível do código e dependências.
2. Configurar `RASTREIO_DATA_DIR` somente no processo de ensaio, apontando para essa pasta. Colocar a cópia como `db.sqlite3` e disponibilizar o segredo de forma privada. Não reaproveitar arquivos WAL/SHM de outro banco.
3. Manter túnel e receptor público fora do ensaio. Confirmar os caminhos resolvidos antes de qualquer comando que grave. Executar `manage.py check`, consultar `showmigrations` e revisar `migrate --plan`. Aplicar migrações somente à cópia de ensaio.
4. Antes de disponibilizar a recuperação, invalidar sessões, tokens de API e links temporários restaurados. Um backup antigo pode tornar novamente válidos acessos usados ou revogados depois de sua criação. Definir reemissão segura e reconciliar contas desativadas, revogações, correções e exclusões posteriores.
5. Validar isolamento entre responsáveis, login, cadastros, histórico, versão de autorização e contagens esperadas. Não enviar localizações reais para testar nem reativar compartilhamento automaticamente.
6. Registrar o resultado e o tempo necessário no controle privado. Só planejar a troca do banco ativo quando o ensaio funcional estiver aprovado e as perdas desde o backup estiverem compreendidas.

## Troca do ambiente e limites

Para uma recuperação real, fazer manutenção com interrupção confirmada de todos os processos que acessam o banco, preservar o estado atual e trocar a configuração de painel e receptor em conjunto. Não sobrescrever um banco aberto. Verificar novamente antes de reabrir o acesso externo; se falhar, manter o receptor fechado e preservar ambos os estados para investigação.

A invalidação de acessos e reconciliação descritas acima ainda não têm comando automatizado neste projeto. O verificador é uma ferramenta de inspeção, não um restaurador. Definir periodicidade, perda tolerável, tempo de recuperação e retenção de cópias continua pendente. Recuperar dados também exige considerar exclusões solicitadas e outras decisões que ocorreram após a cópia.
