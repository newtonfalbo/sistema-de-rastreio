# Sistema de Rastreio

![Status do projeto](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)  

## ​ Descrição

Sistema de Rastreio é uma aplicação desenvolvida para auxiliar no monitoramento e localização de pessoas em situações de risco ou vulnerabilidade.
A plataforma tem como objetivo oferecer um recurso acessível para:

Rastrear pessoas que estejam desaparecidas ou perdidas;

Auxiliar equipes de resgate em ambientes urbanos ou de difícil acesso;

Acompanhar a movimentação de pessoas em situação de emergência;

Fornecer informações rápidas e centralizadas sobre localização e histórico de deslocamento.

🎯 Público-alvo

Usuários comuns que desejam acompanhar pessoas queridas em tempo real (ex: crianças, idosos, familiares em viagens);

Órgãos de segurança pública e equipes de resgate;

Instituições de apoio a pessoas desaparecidas.

🚑 Problema que resolve

Atualmente, encontrar uma pessoa desaparecida ou perdida depende de informações fragmentadas e processos demorados.
Com o Sistema de Rastreio, é possível centralizar informações, registrar movimentações e oferecer mais agilidade na busca por pessoas que necessitam de ajuda.

##  Funcionalidades

•	Registrar pessoas para rastreamento (com informações básicas de identificação);

•	Consultar localização atual em tempo real;

•	Visualizar histórico de deslocamento (datas, horários e locais anteriores);

•	Receber notificações automáticas (por e-mail ou interface) em caso de movimentações suspeitas ou mudanças de status;

•	Disponibilizar API REST para integração com outros sistemas de resgate ou monitoramento.

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
