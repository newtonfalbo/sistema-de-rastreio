# Conexão temporária do celular e segurança

## O que foi entregue

- Link de uso único por dispositivo, válido por 30 minutos, com QR Code gerado localmente.
- Página móvel com confirmação do vínculo e autorização explícita para obter uma posição.
- Segredo aleatório de 256 bits, armazenado apenas como hash no banco; URL usa fragmento removido pelo JavaScript após abertura.
- Link novo revoga o anterior. Revogação manual disponível no painel. Expiração, uso anterior, dispositivo inativo, pessoa sem compartilhamento e responsável inativo impedem envio.
- A atualização que consome o link e a criação da posição ocorrem na mesma transação. Dados inválidos não consomem o link; repetição de link usado não duplica a posição.
- Receptor separado, com configuração sem debug, Waitress em loopback e somente rotas de celular. Não publica login, painel, administração ou API de consulta.
- Proteções de CSRF, limite de corpo de requisição no receptor, política de conteúdo restrita na página móvel, ausência de cache e política de não enviar referer.
- Preparação do cliente oficial Cloudflare para teste HTTPS; o binário fica em `.local/tools`, fora do Git.

## Estado da disponibilização externa

Após solicitação específica, o usuário autorizou expressamente o teste pela Cloudflare. O túnel temporário e o receptor foram ativados. O endereço fica somente em `.local/mobile-origin.txt`, fora do Git.

Validação externa: `/celular/` e `/celular/assets/celular.js` responderam HTTP 200; `/admin/`, `/api/pessoas/` e `/entrar/` responderam HTTP 404. A geração de links foi habilitada no painel. Nenhuma localização física foi coletada na ativação.

O computador, receptor e túnel precisam continuar ligados. `scripts/parar-teste-celular.ps1` encerra os processos registrados após conferir executável e argumentos, mantendo o painel local. Reiniciar o túnel pode alterar o endereço e exigir novos links.

## Segurança e inicialização concluídas nesta rodada

Foram consolidados os ajustes de segurança que já estavam em andamento: chave local aleatória fora do Git; ACL do Windows compatível com o proprietário do projeto; bloqueio de login por usuário/IP após cinco falhas por 15 minutos; sessões e cookies configurados; cabeçalhos no-store e Permissions-Policy; rejeição de configuração de produção com segredo fraco ou hosts indiscriminados.

A queda anterior da página ocorreu com o encerramento do servidor da ferramenta. Ao tentar executá-lo pelo usuário real, uma permissão restritiva criada na pasta `.local` também impediu a leitura da chave. O acesso foi corrigido especificamente para o proprietário do projeto, e o código passou a herdar as ACLs do projeto no Windows. O servidor local foi reiniciado no contexto do usuário do Windows.

Scripts e tarefas do VS Code foram adicionados para inicialização e criação de conta. O sistema não cria senha padrão; a conta de validação solicitada pelo usuário existe apenas no banco local.

## Arquivos principais

- `rastreamento/celular.py`: emissão, revogação, verificação e consumo do link.
- `rastreamento/models.py` e migração `0002_linkdispositivo.py`: armazenamento do hash, validade, revogação e uso.
- `config/mobile_settings.py`, `mobile_root_urls.py`, `mobile_urls.py`: receptor isolado.
- `scripts/servidor-celular.py`: servidor Waitress exclusivo do túnel futuro.
- Templates `celular.html`, `link_dispositivo.html` e seção adicional do painel.
- Estilos e JavaScript em `rastreamento/static/rastreamento/celular.*`.
- `config/local_secret.py`, `rastreamento/security.py`, `config/settings.py`: configuração e segurança.
- `.vscode/tasks.json`, `scripts/iniciar.ps1`, `scripts/criar-conta.ps1`: operação local.
- `tests/test_celular.py`, `tests/celular.test.cjs`, `tests/test_security.py`: novos testes.

## Verificação

- 67 testes Django aprovados, incluindo 17 cenários do link e 14 cenários adicionais de segurança.
- 12 testes JavaScript aprovados, incluindo 6 da página móvel.
- Verificações Django sem problemas e sem migrações pendentes.
- Dependências sem conflitos reportados por pip check.
- check --deploy aprovado para configuração principal e receptor, com segredo temporário e host de teste.
- Configurações de produção com chave curta ou host wildcard rejeitadas.
- Receptor testado quanto à ausência de rotas de painel, API de consulta e administrador.
- Verificados CSRF, origem indevida, uso único, revogação, expiração, ausência de consentimento, envio de coordenadas inválidas e tentativas de alterar o dispositivo do vínculo.

A conexão HTTPS externa foi validada após autorização. A câmera/GPS de um celular real **ainda não foi testada**. Os testes automatizados usam posições simuladas e banco temporário. Não houve coleta de localização física nesta implementação.

## Proteção dos arquivos enviados ao GitHub

`.local/`, `.env`, logs, banco SQLite e `.venv/` ficam excluídos. Isso inclui a chave local, binário do túnel, futuros endereços temporários e credenciais. O código contém somente cenários fictícios de teste, sem a senha da conta de validação. O segredo local também é comparado em memória aos arquivos preparados para commit, sem imprimir seu valor.

A pasta do projeto está no OneDrive: excluir do Git não impede sincronização pelo OneDrive. A definição de uma pasta de dados fora de áreas sincronizadas fica como requisito de operação antes de dados reais em maior escala.

## Limitações e próximos testes

1. Gerar o QR Code no painel e abrir no celular com o túnel autorizado e ativo.
2. Conferir pessoa e dispositivo antes de autorizar; enviar uma posição; atualizar o painel local.
3. Reabrir o mesmo link e confirmar recusa por uso anterior; gerar outro e testar revogação.
4. Validar permissões reais de GPS, ausência de sinal e precisão em aparelhos diferentes.
5. Um link prova posse do segredo, não a identidade física do aparelho nem a autenticidade das coordenadas. O envio é pontual; não há acompanhamento em segundo plano.
6. O mapa externo continua sujeito ao bloqueio do provedor já documentado. O celular não depende dele para enviar a posição.
7. Os links expiram, mas não há limpeza automática de registros antigos nem política final de retenção nesta etapa.
8. Antes de uso permanente: infraestrutura HTTPS definitiva, proteção contra abuso na borda, backups, política de retenção e credenciais próprias por dispositivo.

Referências técnicas: https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/ ; https://docs.pylonsproject.org/projects/waitress/en/stable/usage.html ; https://django-axes.readthedocs.io/en/stable/2_installation.html .

Os requisitos para uso lícito e tratamento de dados estão em [Privacidade e LGPD](PRIVACIDADE-LGPD.md). Autorizar o túnel não substitui definir a base legal do tratamento nem regularizar o uso de fornecedores externos.
