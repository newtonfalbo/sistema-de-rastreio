# Segunda entrega — painel e envio pontual

25/09/2026. Continuação do commit f379f5c, na sessão solicitada até 16h.

## Alterações

- Painel web na raiz `/`, com login próprio em `/entrar/` e saída via POST em `/sair/`.
- Cards com totais, seleção de pessoa, dispositivos, última posição, data, precisão e aviso de captura com mais de 15 minutos.
- Formulários para cadastrar pessoa/dispositivo. O responsável é sempre o usuário autenticado e vínculos alheios são rejeitados.
- Ativação de compartilhamento com confirmação no formulário; desativação mantém histórico e impede novos envios pela API existente.
- Histórico com paginação de 20 itens, horários de Fortaleza e estados vazios.
- Mapa Leaflet sob demanda, com pontos da página e círculo de precisão. Não são requisitados serviços de mapa ao simplesmente abrir o painel.
- Captura pontual do navegador com autorização, permissão de localização, CSRF, tratamento de erros e bloqueio de cliques simultâneos. Não coleta em segundo plano.
- Interface com CSS responsivo, navegação por teclado, mensagens de estado e conteúdo escapado. JSON do mapa usa json_script.
- Painel privado com cabeçalho no-store. Nenhuma senha padrão persistente criada.
- Configuração de provedor por RASTREIO_MAP_TILE_URL e RASTREIO_MAP_ATTRIBUTION. CDN Leaflet com versão fixa e integridade do script.

## Arquivos

- `rastreamento/painel.py`: consultas privadas e ações dos formulários.
- `rastreamento/forms.py`: formulários validados e vínculos limitados ao responsável.
- `rastreamento/templates/`: base, login e painel.
- `rastreamento/static/rastreamento/`: estilos e JavaScript de mapa/coleta.
- `config/urls.py`, `config/settings.py`: novas rotas, login e configuração do mapa.
- `tests/test_painel.py`: 10 testes adicionais.
- `tests/painel.test.cjs`: 6 testes de comportamento da coleta com API de localização simulada.
- `.github/workflows/tests.yml`: inclui testes JavaScript com Node 22.
- `README.md`: instruções atualizadas.

## Validações e limites

36 testes Django e 6 testes JavaScript aprovados. Cobrem login, isolamento, UUID inválido, cadastro, confirmação de compartilhamento, CSRF, paginação, escape de conteúdo, logout, ausência de coleta automática, contexto seguro, envio com CSRF, permissão negada, erro da API e prevenção de duplicidade por cliques simultâneos.

Login e painel foram inspecionados no navegador usando um banco temporário separado e quatro posições fictícias. A biblioteca do mapa e os pontos carregaram, mas o servidor público OpenStreetMap retornou imagens de bloqueio (403). Portanto, a camada de ruas permanece uma limitação conhecida deste ambiente, explicitada na documentação; não foi contornada a restrição do provedor. Para implantação, configurar provedor apropriado.

A localização física real não foi coletada. O envio foi validado com posições simuladas nos testes; a precisão e permissão reais dependem do dispositivo. O layout possui regras para telas pequenas, mas a inspeção visual desta sessão foi em desktop. O painel não atualiza automaticamente: use atualizar após envios. O indicador de posição antiga reflete o momento de carregamento.

O banco principal e os dados do usuário não receberam registros demonstrativos. A versão permanece voltada à revisão local; não houve publicação na internet.

## Como revisar

1. Crie sua conta com `manage.py createsuperuser`, caso ainda não exista.
2. Execute `.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000`.
3. Abra a raiz do servidor e faça login.
4. Cadastre pessoa e dispositivo no painel; ative o compartilhamento autorizado.
5. Confira o dispositivo selecionado antes de enviar a posição deste navegador.
6. Atualize a página para conferir a última captura e o histórico.
7. Desative o compartilhamento e confira o bloqueio de novos envios.

Próximos passos: resolver/configurar a camada cartográfica no ambiente de destino, credenciais por dispositivo, auditoria da autorização, filtros de período no painel e validação em celular real com HTTPS.
