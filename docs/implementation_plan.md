# Plano de Implementação

Este documento registra as fases que orientaram a implementação da ROSITA.
As entregas descritas refletem o estado atual do projeto.

## Fase 1 — Backend e API

- Configuração por variáveis de ambiente.
- Abstração dos provedores OpenRouter e Gateway.
- Contratos REST e respostas em Server-Sent Events.
- Validação de entrada e limites de requisição.

## Fase 2 — Interface web

- Interface Vanilla JS como camada principal de uso.
- Login administrativo e acesso anônimo ao chat.
- Streaming de mensagens e consulta ao PDF do regimento.
- Temas claro/escuro e layout responsivo.

## Fase 3 — Administração e dados

- Seleção de provedores e modelos em runtime.
- Editor de referências `.txt` com backup.
- Histórico SQLite por usuário/sessão.
- Aviso de privacidade, exportação e exclusão.

## Fase 4 — Implantação

- Scripts automatizados para Windows e Linux.
- Docker Compose com Nginx e Gunicorn.
- Health checks e monitoramento de recursos.
- Execução local via servidor de desenvolvimento.

## Fase 5 — Qualidade

- Suíte Pytest para o backend e integrações.
- Verificação de autenticação, validação, armazenamento e proxy.
- Revisão documental para apresentação acadêmica e implantação.

## Critérios alcançados

- O usuário utiliza a interface web sem executar o CLI.
- A instituição pode configurar o provedor de IA sem alterar o código.
- Referências institucionais podem ser mantidas pela área administrativa.
- Dados da sessão podem ser exportados ou excluídos.
- O projeto pode ser executado localmente ou por contêineres.
