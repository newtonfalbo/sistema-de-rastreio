# Procedimento inicial de resposta a incidentes

Versão de trabalho: 26/09/2026. Destina-se à preparação operacional do protótipo. Precisa de responsáveis nomeados, contatos privados, validação jurídica e exercício prático antes de uso com terceiros. Não é registro de ocorrência nem declaração de conformidade.

## Responsáveis a definir

| Função | Decisão necessária |
| --- | --- |
| Responsável técnico e substituto | Quem pode interromper o receptor, preservar evidências, corrigir e recuperar a instalação |
| Controlador | Quem decide finalidade, tratamento do incidente e comunicação |
| Encarregado ou representante habilitado | Quem coordena a comunicação e mantém contato com titulares e ANPD |
| Fornecedores envolvidos | Canais de suporte e responsabilidades de hospedagem, túnel, mapas/CDN e sincronização |

Contatos e dados pessoais dos responsáveis devem ficar no controle privado da operação. A conta chamada “responsável” no banco não determina, sozinha, quem exerce o papel jurídico de controlador.

## 1. Registrar e avaliar o sinal recebido

Abrir registro privado com identificador, horário e fuso, origem do relato, fatos confirmados e dúvidas. Separar hipótese de evidência. Exemplos a investigar neste sistema: acesso ao histórico de outra pessoa, chave publicada, link compartilhado indevidamente, perda de banco, alteração inesperada de permissões ou indisponibilidade persistente.

A ANPD distingue vulnerabilidade de incidente confirmado e orienta avaliar se há dados pessoais e risco ou dano relevante aos titulares. A descoberta de uma dependência vulnerável exige correção e investigação adequada, mas não prova, por si só, exploração ou vazamento. [Orientações oficiais](https://www.gov.br/anpd/pt-br/canais_atendimento/agente-de-tratamento/comunicado-de-incidente-de-seguranca-cis).

## 2. Conter conforme o componente afetado

- **Exposição pelo teste móvel:** o operador técnico pode executar `scripts/parar-teste-celular.ps1` para encerrar túnel e receptor identificados. Conferir o resultado e a liberação da porta; o script recusa processos desconhecidos. Não presumir encerramento se houver erro. O painel local continua separado.
- **Link comprometido:** revogar links pendentes do dispositivo pelo painel. Desativar compartilhamento também revoga links. Não enviar outro link pelo mesmo canal comprometido sem revisão.
- **Conta comprometida:** desativar pela administração, a partir de uma conta administrativa confiável. O fluxo normal revoga links, remove token de API e avança a versão das sessões. Reativação exige revisão e credenciais adequadas; não restaura acessos anteriores.
- **Segredo ou arquivo publicado:** restringir a exposição e revogar/rotacionar a credencial apropriada. Remover o arquivo do commit mais recente não apaga histórico, clones ou caches. Avaliar cópias externas e reescrita do histórico conforme o caso, preservando evidência privada necessária.
- **Máquina comprometida:** priorizar isolamento e investigação especializada. Alterar a aplicação no mesmo computador não demonstra recuperação da confiança no equipamento.

Não executar limpeza de retenção, apagar logs ou sobrescrever backups durante a apuração sem decisão registrada. Conter a exposição tem prioridade; preserve as evidências disponíveis sem prolongar um acesso indevido para “observar”.

O formulário de troca de senha da administração também remove o token de API e revoga links móveis pendentes da conta, na mesma transação da alteração. O Django invalida outras sessões pelo hash da senha; a sessão do próprio administrador que troca sua senha pode ser preservada pelo fluxo padrão. Isso não substitui desativar uma conta comprometida durante a investigação. Alterações via shell, `changepassword`, SQL ou outros formulários não passam por essa extensão; exigem revogação explícita. A operação não remove o histórico de posições e não cria automaticamente novo token ou link.

## 3. Preservar e delimitar

Guardar somente o necessário em armazenamento restrito aprovado, fora do repositório público. Considerar que `.local/` fica fora do Git, mas pode continuar sincronizada pelo OneDrive. Registrar quem coletou, quando e como preservou a cópia; usar hashes dos arquivos para conferir alterações posteriores.

Investigar intervalo de exposição, contas/dispositivos envolvidos, tipo e quantidade de dados, ações realizadas e acessos possíveis. Evitar repetir senhas, tokens e coordenadas em relatórios gerais. Logs de login, banco, Git e provedores são fontes distintas: ausência de registro em uma delas não prova ausência de acesso. Separar a coleta técnica da decisão sobre a relevância do dano.

## 4. Decidir e realizar comunicações aplicáveis

Pelo RCIS, o prazo geral de comunicação à ANPD e aos titulares é de três dias úteis a partir do conhecimento pelo controlador de que o incidente afetou dados pessoais, quando presentes os requisitos de comunicação. Há ressalvas e regras específicas, incluindo pequeno porte quando efetivamente aplicável; não presumir esse enquadramento. Informações incompletas podem exigir comunicação preliminar e complementação fundamentada, sem simplesmente aguardar o fim da investigação. Conferir os arts. 6º e 9º no caso concreto. [Resolução CD/ANPD nº 15/2024](https://bibliotecadigital.mj.gov.br/bitstream/1/12879/2/RES_ANPD_2024_15.html).

O controlador, por representante habilitado, deve seguir o canal oficial vigente. A página da ANPD indica peticionamento no SEI e alerta para o nível de acesso dos documentos. Não anexar banco, chave ou dados excessivos em documentos públicos. Comunicação à autoridade e comunicação aos titulares são providências distintas. [Procedimento oficial](https://www.gov.br/anpd/pt-br/canais_atendimento/agente-de-tratamento/comunicado-de-incidente-de-seguranca-cis).

Registrar a decisão, sua fundamentação, responsáveis, prazos e comprovantes. O art. 10 prevê guarda mínima de cinco anos do registro de incidentes, inclusive não comunicados, com ressalvas e possíveis obrigações adicionais. Isso não define o prazo de retenção de todas as posições e backups do sistema. [RCIS, art. 10](https://bibliotecadigital.mj.gov.br/bitstream/1/12879/2/RES_ANPD_2024_15.html).

## 5. Recuperar e revisar antes de reabrir

Corrigir a causa identificada e testar em ambiente isolado. Se houver restauração, seguir [Backup e recuperação](BACKUP-RECUPERACAO.md), incluindo invalidação dos acessos restaurados e reconciliação de exclusões/revogações posteriores. Conferir isolamento entre contas, configuração do receptor, credenciais, testes e disponibilidade antes de autorizar a reabertura.

Registrar o que foi corrigido, a evidência da validação e os riscos ainda pendentes. Revisar o procedimento após o exercício ou incidente. Não prometer que uma correção de código elimina cópias já obtidas por terceiros.

## Campos do registro privado

Identificador; responsáveis; datas de ocorrência e conhecimento; descrição e causa conhecida; dados e titulares afetados; avaliação de riscos; medidas anteriores e posteriores; evidências e controle de acesso; decisão fundamentada de comunicação; prazos e comprovantes; validação da recuperação; ações de prevenção e data de revisão.

Este roteiro ainda não foi exercitado com uma equipe operacional. Não cria alertas automáticos, canal de atendimento, contratos ou comunicação em nome do usuário. Esses itens permanecem pendentes de definição e validação.
