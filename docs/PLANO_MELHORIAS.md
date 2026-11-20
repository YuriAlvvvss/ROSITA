# Plano de Correções e Melhorias — ROSITA

Este documento organiza pendências técnicas e evolução recomendada da aplicação.
Os itens concluídos registram funcionalidades já implementadas no estado atual.

## Concluído

| Área | Entrega |
|---|---|
| Segurança | Hash de senhas, mitigação de timing attack, chaves por ambiente e limite de taxa |
| Autenticação | Sessões administrativas, acesso anônimo ao chat e controle por perfil |
| Chat | Streaming SSE, validação de entrada, histórico, histórico e privacidade por sessão |
| Frontend | Tema claro/escuro, responsividade, PDF do regimento e painel administrativo |
| Administração | Troca de provedor/modelo e edição de referências com backup `.bak` |
| Observabilidade | `/api/health`, `/api/status` e monitoramento de recursos |
| Persistência | SQLite com retenção configurável, exportação e exclusão de dados |
| Implantação | Docker Compose, Nginx, scripts locais Windows/Linux e Gunicorn |
| Qualidade | Suíte Pytest para backend, validação, histórico, proxy web e configuração |

## Pendências conhecidas

| Prioridade | Item | Justificativa |
|---|---|---|
| Média | Modularizar o frontend em módulos específicos | `main.js` concentra navegação, autenticação, chat, privacidade e administração |
| Média | Adicionar testes unitários e E2E no frontend | Atualmente a cobertura principal está no backend e no proxy web |
| Média | Adicionar pipeline de build opcional | Um empacotador pode gerar assets versionados e facilitar cache em produção |
| Média | Configurar URL da API em tempo de execução | `config.js` permanece como ponto de configuração no frontend |
| Média | Introduzir múltiplas conversas independentes | O histórico atual representa mensagens da sessão atual, não uma lista de conversas |
| Baixa | Avaliar armazenamento persistente dos dados editáveis no Docker | O volume atual persiste o SQLite; a imagem fornece os arquivos de `backend/data` |
| Baixa | Documentar procedimentos LGPD de toda a instituição | O sistema implementa mecanismos técnicos, mas não define política jurídica interna |

## Trabalho futuro para escala

- Separar os responsáveis do frontend em módulos de autenticação, chat,
  administração e status.
- Avaliar Vitest/Jest e Playwright para testes automatizados da interface.
- Centralizar configuração de runtime sem acoplamento ao código.
- Definir estratégia de backups e recuperação para o SQLite e os arquivos de referências.
- Revisar limites de taxa e logs conforme a carga real da instituição.
- Consolidar uma política institucional de retenção, encarregado, base legal
  e atendimento a solicitações de titulares.
