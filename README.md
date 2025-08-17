# 📍 Sistema de Rastreio

![Status do projeto](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)

O **Sistema de Rastreio** é uma aplicação desenvolvida para auxiliar no monitoramento e localização de pessoas em situações de risco ou vulnerabilidade.  
O objetivo é oferecer uma ferramenta acessível e prática para ajudar a encontrar pessoas que estejam **desaparecidas**, **perdidas** ou **precisem de ajuda urgente**.

---

## 📖 Descrição  

A plataforma permite que usuários cadastrem pessoas para rastreamento, consultem sua localização atual e visualizem o histórico de deslocamentos.  
Ela pode ser utilizada tanto por **usuários comuns** (familiares de crianças, idosos, etc.) quanto por **equipes de resgate e órgãos de segurança pública**.  

### 🎯 Público-alvo  
- Familiares que desejam acompanhar pessoas queridas em tempo real.  
- Órgãos de segurança e equipes de resgate.  
- Instituições de apoio a pessoas desaparecidas.  

### 🚑 Problema que resolve  
Hoje, encontrar pessoas desaparecidas depende de informações fragmentadas e processos demorados.  
Com o **Sistema de Rastreio**, é possível **centralizar informações** e fornecer mais agilidade na busca de pessoas em situação de risco.  

---

## ⚙️ Funcionalidades  

- 👤 Registrar pessoas para rastreamento (dados básicos de identificação).  
- 📍 Consultar localização atual em tempo real.  
- 🕓 Visualizar histórico de deslocamento (datas, horários e locais anteriores).  
- 🔔 Receber notificações automáticas sobre movimentações ou alterações de status.  
- 🌐 API REST para integração com outros sistemas de resgate ou monitoramento.  

---

## 🛠️ Tecnologias  

- **Linguagem principal**: Python 🐍  
- **Framework/backend**: Django 🌐  
- **Banco de dados**: SQLite 💾  
- **Bibliotecas/APIs externas**:  
  - Django REST Framework (DRF) → criação de APIs REST.  
  - Requests → consumo de APIs externas.  
  - Geopy → manipulação de dados de localização (endereços, coordenadas).  
- **Testes**: pytest ✅  
- **Infra/Deploy**: Docker 🐳  

---

## 📂 Estrutura do Projeto  

```text
sistema-de-rastreio/
├── sistema-de-rastreio/   # Pasta de configuração principal do Django
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py              # Ponto de entrada do projeto
├── requirements.txt       # Dependências do projeto
├── Dockerfile             # Configuração para containerização (opcional)
├── README.md              # Documentação
└── LICENSE                # Licença

