# Próximas fases combinadas

Registro das decisões do usuário em 26/09/2026. Este roteiro separa intenções futuras de funcionalidades já entregues.

## Sessão atual, até 00h de 27/09 (Fortaleza)

Continuar backend, segurança, testes e documentação. Publicar alterações verificadas sem banco, credenciais, dados pessoais ou links privados. Preparar relatório detalhado para revisão.

## Amanhã: frontend

Trabalhar em conjunto na interface e experiência de uso. Pontos para revisão:

- Organização e clareza do painel, cadastros e histórico.
- Apresentação dos estados de compartilhamento e links expirados/revogados.
- Aviso de autorização e consulta da evidência de envio.
- Layout em celulares, navegação por teclado e mensagens de erro.
- Validação visual das mudanças recentes, pendente devido à indisponibilidade da ferramenta de navegador durante a sessão de backend.

## Fase seguinte: aplicativo instalável no celular

**Solicitação registrada:** criar um aplicativo para instalar no celular, chegando à instalação pela leitura de QR Code ou por link.

Antes de implementar, decidir com o usuário:

1. Plataformas iniciais: Android, iPhone ou ambas.
2. Tipo de aplicação e distribuição: avaliar PWA, aplicativo nativo ou multiplataforma conforme os requisitos reais.
3. Finalidade e modalidade de coleta: envio pontual, intervalos ou outra necessidade explicitamente definida. Localização em segundo plano não foi solicitada como requisito nesta decisão.
4. Experiência de instalação, vínculo seguro do dispositivo e recuperação/revogação de acesso.
5. Permissões, aviso de privacidade, autorizações, retenção e controles para interromper a coleta.
6. Testes de precisão, consumo de bateria, conectividade, atualização e desinstalação nos aparelhos escolhidos.

O endereço de instalação/serviço precisa de estratégia estável. Em 26/09, o provedor deixou de reconhecer o túnel temporário de teste e foi necessário gerar outro endereço; QR codes antigos deixaram de servir. Não usar esse endereço efêmero como base de uma distribuição permanente do aplicativo.

O QR Code/link atual serve para abrir uma página de envio pontual; ainda não instala aplicativo. O futuro fluxo de instalação e o vínculo do aparelho deverão ser especificados separadamente dos links temporários de envio existentes. Nenhuma conta de loja, assinatura, certificado de distribuição ou aplicativo foi criado nesta etapa.
