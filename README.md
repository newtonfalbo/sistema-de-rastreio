# Sistema de Rastreio

![Status do projeto](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)  
*(Opcional: badges de cobertura de testes, linguagem, license, etc.)*

Uma aplicação simples para rastreamento e gerenciamento de objetos/encomendas. Permite consultar status, histórico de movimentação e fornecer notificações futuras de atualização de status.

## ​ Descrição

Explique brevemente:
- O propó.
- O público-alvo: usuários finais.
- Problemas que resolve (ex: acompanhar entregas de forma centralizada).

##  Funcionalidades

- Registrar objetos ou códigos de rastreio
- Consultar status e localização atual
- Visualizar histórico de eventos (datas, localizações anteriores)
- Notificações (por e-mail ou interface) de mudanças de status *(se aplicável)*
- API REST (se existir backend exposto)

##  Tecnologias

- Linguagem principal: Python
- Framework/backend: Django
- Banco de dados: SQLite
- Bibliotecas/parsers/APIs externas:
- Testes: pytest, unittest
- Infra/Deploy (opcional): Docker

##  Estrutura do Projeto

```text
sistema-de-rastreio/
├── src/
│   ├── main.py          # Ponto de entrada (ex: servidor)
│   ├── controllers/     # Rotas ou endpoints
│   ├── models/          # Modelos de dados
│   ├── services/        # Lógica de rastreio e integração
│   └── utils/           # Funções helpers
├── tests/               # Testes automatizados
├── requirements.txt     # Dependências do Python
├── Dockerfile           # Se aplicável
├── README.md            # Este arquivo
└── LICENSE              # Licença do projeto (ex: MIT)
