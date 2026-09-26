# Retenção e limpeza revisável

## O que foi implementado

O comando `manage.py limpar_registros` permite simular a limpeza e, com parâmetros adicionais explícitos, excluir registros do banco ativo. Nenhum prazo foi escolhido como política do projeto e nenhum agendamento foi instalado. A definição do prazo depende da finalidade, das obrigações aplicáveis e da revisão do responsável pela operação.

Há dois tipos:

- `localizacoes`: posições cujo **recebimento pelo servidor** ocorreu antes do limite. O horário de captura não é usado para evitar a remoção imediata de posições antigas que acabaram de chegar.
- `links`: links cuja expiração ocorreu antes do limite. Links ainda válidos são preservados.

O limite é exclusivo: um registro exatamente na data/hora informada permanece. Datas sem fuso ou futuras são rejeitadas. O escopo deve ser um responsável existente ou todos, explicitamente.

## Simular primeiro

Exemplo com identificador e data fictícios; substitua pelos critérios aprovados para sua operação:

```powershell
.\.venv\Scripts\python.exe manage.py limpar_registros --tipo localizacoes --responsavel 123 --antes "2026-01-01T00:00:00-03:00"
```

Sem `--confirmar`, o comando apenas conta os registros elegíveis. Não imprime nomes, coordenadas, identificadores de posições ou segredos de links. Revise os números e confirme que o processo usa o banco correto, principalmente se `RASTREIO_DATA_DIR` estiver configurado.

## Executar somente após revisão

Mantenha **o mesmo tipo, responsável e data absoluta** usados na simulação. Acrescente `--confirmar --esperados N`, onde N é a quantidade revisada. A data absoluta evita que o período aumente silenciosamente entre simulação e execução.

Se a quantidade mudou, a operação é abortada sem exclusão e é necessário simular novamente. O limite padrão é 1000 registros por execução; `--maximo` permite definir um limite explícito entre 1 e 100000. Se o total excede o limite, nenhum lote parcial é apagado. Reduza o escopo ou revise deliberadamente o limite.

`--todos` substitui `--responsavel` e pode afetar registros de todas as contas. Não é o padrão. O comando é administrativo local, executado por quem tem acesso ao servidor e ao banco; não é uma rota pública nem um botão de exclusão no celular.

As exclusões ocorrem em transação. Após a seleção dos IDs, novos registros não entram automaticamente no lote. Em caso de disputa de gravação no SQLite, aguarde e refaça a simulação; não trate erro de bloqueio como confirmação de exclusão.

## Alcance e limites

- Pessoas, dispositivos e contas são preservados.
- Ao excluir uma posição, seu texto/versionamento da autorização também é removido, pois está no mesmo registro. Avalie previamente eventuais necessidades de conservação e restrições de eliminação.
- Links expirados podem ser eliminados independentemente do histórico das posições.
- O comando não remove arquivos de backup, cópias do OneDrive, logs ou dados de fornecedores. Também não promete apagar fisicamente todos os vestígios das páginas internas do arquivo SQLite.
- Não há tratamento automático de exceções legais, pedidos de preservação ou direitos do titular. Esses casos precisam ser avaliados antes de confirmar.
- Não há agendamento, prazo predefinido ou limpeza ao iniciar a aplicação.
- A simulação é o primeiro passo operacional; ela não define se a exclusão é juridicamente adequada.

Nesta entrega, a exclusão foi exercitada somente em bancos temporários de teste. Nenhuma limpeza foi executada no banco real do usuário.
