# ROSITA - Assistente Escolar

Projeto Python com backend Flask e frontend web, com suporte a provedores de IA:
- OpenRouter (API, nuvem) — provedor padrão
- Gateway local (servidor OpenAI-compatible na sua rede)

A ROSITA é um assistente da PEI Rosa Bonfiglioli que responde dúvidas sobre o
regimento e os procedimentos da escola, baseando-se na documentação oficial
carregada em memória (`backend/data/*.txt` e `*.md`, ex.: `regimento_ECIM.txt`;
só `.txt` é editável pela UI).

## Arquitetura

```txt
┌──────────────────────────────┐
│  Frontend (web/) — Nginx     │
│  HTML + CSS + JS (vanilla)   │
│  • Login / sessão            │
│  • Chat com streaming (SSE)  │
│  • Tema claro/escuro         │
│  • Painel admin / status     │
└──────────────┬───────────────┘
               │  REST + SSE  (/api/*, cookie de sessão)
┌──────────────▼───────────────┐
│  Backend (Flask + Gunicorn)  │
│  • Rotas/auth (hash + rate-limit)
│  • RositaAgent (orquestração)│
│  • HistoryStore (SQLite, por usuário)
└──────────────┬───────────────┘
               │
   ┌───────────┼───────────┐
   ▼           ▼
┌──────────┐ ┌──────────┐
│OpenRouter│ │ Gateway  │
│ (nuvem)  │ │ (custom) │
└──────────┘ └──────────┘
```

## Principais recursos

- **Autenticação** com senhas em hash (`werkzeug`), `secret_key` por ambiente e
  rate limiting em login/chat (além do limite global de 240/hora).
- **Histórico por usuário** persistido em SQLite (sobrevive a reinícios). O
  histórico é automático por usuário/sessão; o botão "Histórico" da sidebar
  está desabilitado ("em breve") — ainda não há UI de múltiplas conversas.
- **Chat em streaming** (SSE) com scroll simples para o fim (`scrollTop =
  scrollHeight`), contador de caracteres `0/1000` e mensagens em texto puro
  (`textContent`, sem render Markdown). A entrada é `<input type="text">`
  single-line (`Enter` envia; sem `Shift+Enter`/multilinha, sem botão de parar,
  sem botão de copiar e sem indicador de "digitando"). Os arquivos
  `web/scripts/vendor/marked.min.js` e `purify.min.js` existem no repositório
  mas **não são carregados** por `web/index.html` (só `config.js`,
  `api_client.js` e `main.js`).
- **Botão "Regimento"** na sidebar, que abre o PDF servido por
  `GET /api/regimento/pdf` (arquivo em `backend/data/`).
- **Painel admin** com abas Modelo Ativo, Referências (edição de `.txt` com
  backup `.bak` e toasts de feedback) e Provedor de IA, além de **Status do
  Sistema** (servidor, modelo ativo, CPU, memória, disco, GPU/VRAM).
- **Tema claro/escuro**: a abertura da interface **sempre inicia no tema escuro**
  (não usa `prefers-color-scheme` nem restaura o tema claro salvo). O botão na
  sidebar ainda permite alternar durante a sessão. Tokens CSS em
  `web/styles/main.css`: o escuro fica em `:root`; o claro em
  `html[data-theme="light"]` (degradê suave e glassmorphism). O layout do
  compositor (largura alinhada à área de mensagens) é o mesmo nos dois temas.
- **Múltiplos provedores de IA** alternáveis em runtime pela interface admin.
- **Healthcheck** (`/api/health`) que verifica o provedor de IA.

## Estrutura padronizada

```txt
ROSITA/
├── .env.example
├── agent_cli.py
├── pytest.ini
├── backend/
│   ├── app.py             # entrypoint Flask real (usa app_factory; lê .env, env.admin, env.defaults, backend/.env, .venv/admin_password.env)
│   ├── Dockerfile           # CMD gunicorn app:app direto (compose-entrypoint.sh existe mas NÃO é usado pelo Compose)
│   ├── compose-entrypoint.sh # legado/não referenciado no docker-compose.yml
│   ├── env.admin          # versionado (admin + hash)
│   ├── env.defaults       # versionado (padrões; contém IP interno, ver nota de provedores)
│   ├── .env               # escrito pelo painel admin (PUT /api/credenciais); NÃO está no .gitignore
│   ├── requirements.txt   # flask, flask-cors, flask-limiter, gunicorn, python-dotenv, psutil, requests
│   ├── api/ core/ utils/  # stubs com só __init__.py; código real está em src/rosita/
│   ├── data/
│   │   ├── agent_instructions.txt (+ .bak gerado ao editar pela UI)
│   │   ├── regimento_ECIM.txt
│   │   └── regimento_ECIM.pdf   # servido por GET /api/regimento/pdf (match case-insensitive)
│   └── src/rosita/
│       ├── core/          # agent.py, ai_client.py (OpenRouter, Gateway), prompt_builder.py
│       ├── api/           # routes.py (REST + SSE) + routes/credentials.py (vazio, legado)
│       ├── utils/         # env_manager, file_loader, history_store, system_monitor, validators
│       ├── app_factory.py   # factory real usada por backend/app.py
│       ├── main.py          # factory legada NÃO usada (instancia Settings() sem args, blueprint vazio)
│       ├── bootstrap.py
│       └── settings.py
├── docker-compose.yml
├── docker/
│   └── minios-vfs-daemon.json
├── docs/
│   ├── README.md
│   ├── architecture.md
│   ├── ARQUITETURA.md
│   ├── implementation_plan.md
│   ├── linux_startup.md
│   └── PLANO_MELHORIAS.md
├── frontend/              # rascunhos/guias legados (FRONTEND_ROSITA.md etc.); o frontend oficial é web/
├── requirements-dev.txt
├── scripts/
│   ├── enable-docker-vfs-minios.sh   # lê docker/minios-vfs-daemon.json
│   ├── set_admin_password.py         # gera hash em .venv/admin_password.env
│   ├── win_run_backend.bat
│   └── win_run_web.bat
├── start_system.bat
├── start_system.sh
├── tests/                 # HistoryStore, auth/API, validadores, seleção de modelo/provedor, proxy web, deploy
├── web/
│   ├── Dockerfile
│   ├── index.html
│   ├── nginx.conf           # em Docker faz proxy de /api/* para backend:5000 (SSE com timeout longo)
│   ├── README.md
│   ├── scripts/           # main.js (textContent, input single-line, keypress Enter), api_client.js (fetch/SSE), config.js, dev_server.py, vendor/ (marked, DOMPurify presentes mas NÃO carregados no index.html)
│   └── styles/            # main.css (temas claro/escuro)
└── README.md
```

## Convenções adotadas

- nomes de pastas em minúsculo;
- nomes Python em `snake_case`;
- separação por camadas (core, api, utils, settings);
- instruções do agente fora do código.

## Instruções do agente (editável)

Arquivo: `backend/data/agent_instructions.txt`

Placeholders suportados: `{DOCUMENTACAO}` (atual — usado pelo arquivo em
`backend/data/`) e `{REGIMENTO}` (legado). Ambos são substituídos em
`backend/src/rosita/core/prompt_builder.py`.

## Configuração de provedores de IA

O backend suporta dois provedores (configurados no `.env`):

| Provedor | Variável principal | Uso |
|----------|-------------------|-----|
| **OpenRouter** | `ROSITA_OPENROUTER_API_KEY`, `ROSITA_OPENROUTER_MODEL` | Modelos na nuvem (https://openrouter.ai) — padrão |
| **Gateway** | `ROSITA_GATEWAY_URL`, `ROSITA_GATEWAY_MODEL`, `ROSITA_GATEWAY_API_KEY` | Servidor OpenAI-compatible no seu servidor (vLLM, LocalAI, LM Studio, etc.) |

Provedor ativo por padrão:

```env
ROSITA_AI_PROVIDER=openrouter
```

Valores aceitos: `openrouter` ou `gateway`.

Se mais de um provedor estiver configurado (ex.: OpenRouter + gateway local), o administrador pode alternar entre eles na interface ou via API (`GET /api/provedores`, `POST /api/provedores/trocar`).

Exemplo OpenRouter:

```env
ROSITA_AI_PROVIDER=openrouter
ROSITA_OPENROUTER_API_KEY=sk-or-v1-xxxxx
ROSITA_OPENROUTER_MODEL=openai/gpt-4o-mini
```

Exemplo Gateway (IA local no servidor):

```env
ROSITA_AI_PROVIDER=gateway
ROSITA_GATEWAY_URL=http://127.0.0.1:8000
ROSITA_GATEWAY_MODEL=seu-modelo
# ROSITA_GATEWAY_API_KEY=chave-opcional-do-gateway
```

O gateway deve expor `GET /v1/models` e `POST /v1/chat/completions` (URL base **sem** `/v1` no final).

> Nota: `backend/env.defaults` (versionado) traz `ROSITA_GATEWAY_URL=http://100.75.86.69:3001`
> e `ROSITA_GATEWAY_MODEL=deepseek-chat` — é um IP interno fixo, não um exemplo
> genérico. Se você não usa esse gateway, sobrescreva no `.env` da raiz
> (ou limpe via painel admin) para não exibir um provedor indisponível na UI.

Copie `.env.example` para `.env` e preencha as variáveis do provedor desejado.

## Segurança e autenticação

As credenciais e a chave de sessão vêm do `.env` (veja `.env.example`):

```env
# Gere a chave: python -c "import secrets; print(secrets.token_hex(32))"
ROSITA_SECRET_KEY=

# Nome de usuário dos perfis de acesso.
ROSITA_ADMIN_USERNAME=ADM
ROSITA_USER_USERNAME=usuario

# Gere o hash: python -c "from werkzeug.security import generate_password_hash as g; print(g('SUA_SENHA'))"
ROSITA_ADMIN_PASSWORD_HASH=
ROSITA_USER_PASSWORD_HASH=
```

- As senhas são verificadas por **hash** (`scrypt`/`werkzeug`). Quando o usuário
  não existe, um hash descartável é comparado para equalizar o tempo de
  resposta (proteção contra enumeração por timing attack).
- O **login é restrito ao perfil admin** (comparação case-insensitive); o perfil
  de usuário comum usa o chat sem login (visita anônima com histórico isolado
  por sessão).
- **Ordem de precedência da config** (o último vence). No Docker Compose
  (`docker-compose.yml`): `backend/env.defaults` < `backend/env.admin`
  (ambos versionados) < `.env` da raiz < `backend/.env` (escrito pelo painel
  admin) < variáveis já exportadas no ambiente. No dev local
  (`backend/app.py:23-33`): `.env` da raiz, `env.admin`, `env.defaults`,
  depois `backend/.env` com `override=True`, e por último
  `.venv/admin_password.env` com `override=True` (precedência máxima local).
  O painel admin (`PUT /api/credenciais`, `POST` também aceito) persiste em
  `backend/.env`, não no `.env` da raiz. Atenção: `.gitignore` ignora só o
  `.env` da raiz — `backend/.env` **não** está ignorado; não commite chaves nele.
- Atenção ao Docker Compose: **hashes scrypt contêm `$`**. Use **sempre aspas
  simples** no `.env`/`backend/.env` (ex.: `ROSITA_ADMIN_PASSWORD_HASH='scrypt:...'`),
  senão o Compose expande `$...` e corrompe o hash (veja o aviso no topo do
  `.env.example`).
- O repositório já traz `backend/env.admin` versionado (`admin` + hash). Para
  trocar a senha, gere um hash e defina no `.env` da raiz (ou em
  `backend/.env` pelo painel).
- Se `ROSITA_SECRET_KEY` ficar vazia, uma chave aleatória é gerada a cada início
  (as sessões não persistem entre reinícios) — defina-a em produção.
- Se os `_HASH` ficarem vazios, aceita-se a senha em texto via
  `ROSITA_ADMIN_PASSWORD` / `ROSITA_USER_PASSWORD`; na ausência de ambos, um hash
  temporário é gerado e o login administrativo fica indisponível por padrão —
  **não** use isso em produção.
- Para desenvolvimento local, você também pode definir credenciais em
  `.venv/admin_password.env` (gerado por `scripts/set_admin_password.py`, só
  grava o hash, sem username), que é carregado por `backend/app.py` com
  `override=True` — ou seja, vence `.env` da raiz e `backend/.env` no dev local.
- `POST /api/auth/login` (10/min) e `POST /api/chat` (20/min) têm limite de taxa, além do limite global de 240/hora. Vale quando `flask-limiter` está instalado (está em `backend/requirements.txt`); sem ele, `app_factory.py` usa `_NoopLimiter` e a limitação fica desativada com aviso no log.

## Histórico por usuário

O histórico de conversa é persistido em **SQLite**, isolado por usuário (ou por
visitante anônimo, via ID de sessão), e sobrevive a reinícios do servidor. O
caminho do banco é configurável:

```env
ROSITA_HISTORY_DB=backend/rosita_history.sqlite3
```

No Docker Compose o backend usa `ROSITA_HISTORY_DB=/data/rosita_history.sqlite3`
com volume nomeado `rosita_history` (persistente entre `up`/`down`).

## Ajustes opcionais

Variáveis adicionais disponíveis no `.env` (veja `.env.example`):

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `ROSITA_WEB_PORT` | `18080` | Porta pública da interface web (com `.env`). Sem `.env`, o Compose publica `${ROSITA_WEB_PORT:-18888}:80` no serviço `web`. Atenção: o serviço `backend` usa `${ROSITA_WEB_PORT:-37642}` só para montar o CORS (`docker-compose.yml:33,72`) |
| `ROSITA_API_PORT` | `18500` | Porta pública da API (no container o backend escuta em `5000`; o Compose publica `18500:5000`). No dev local (`scripts/win_run_backend.bat`), default `18500` |
| `ROSITA_BACKEND_URL` | `http://127.0.0.1:18500` | Só para dev local: URL do backend usada por `web/scripts/dev_server.py` (não está no `.env.example`; no Docker o Nginx usa `backend:5000` fixo) |
| `ROSITA_API_HOST` | `0.0.0.0` | Host do Flask/Gunicorn (`settings.py`, `win_run_backend.bat`, Compose força `0.0.0.0:5000` no container) |
| `ROSITA_WEB_HOST` | `127.0.0.1` | Host do `dev_server.py` local (só dev; `scripts/win_run_web.bat`) |
| `ROSITA_DATA_DIR` | `backend/data` | Pasta de dados ativa (editável pela UI). No Compose, edições são **efêmeras** (só `rosita_history` tem volume) |
| `ROSITA_BUNDLED_DATA_DIR` | `src/rosita/default_data` (inexistente) | Fallback de seed; no Compose sobrescrito para `/app/backend/data` (`docker-compose.yml:35`). `backend/Dockerfile:14` também copia para `/app/default-data` (não usado em runtime) |
| `ROSITA_GPU_NAME` | — | Nome de fallback exibido na UI quando há GPU visível (`CUDA_VISIBLE_DEVICES`/`NVIDIA_VISIBLE_DEVICES`) mas sem `nvidia-smi` (`system_monitor.py`) |
| `ROSITA_SESSION_COOKIE_SECURE` | `false` | Marque `true` quando servir por HTTPS (cookies de sessão só por TLS) |
| `ROSITA_MAX_HISTORY` | `5` | Quantidade de mensagens do histórico enviadas ao provedor |
| `ROSITA_MAX_INPUT_CHARS` | `1000` | Limite de caracteres por mensagem |
| `ROSITA_NUM_PREDICT` | `256` | Tamanho máximo da resposta gerada |
| `ROSITA_TEMPERATURE` | `0.75` | Criatividade do modelo |
| `ROSITA_TOP_P` | `0.92` | Amostragem *nucleus sampling* |
| `ROSITA_REPEAT_PENALTY` | `1.08` | Penalidade de repetição |
| `ROSITA_DEBUG` | `false` | Modo de depuração do Flask |

## Testes

```bash
pip install -r requirements-dev.txt
pytest
```

Cobrem o `HistoryStore`, validação de entrada, autenticação/autorização, o núcleo
do agente e a seleção de modelo/provedor (sem depender de um servidor de IA),
o proxy do frontend (`web/scripts/dev_server.py`) e checagens de deploy.

## Execução

### Inicialização automática (recomendado - Windows)

```bat
start_system.bat [--no-start] [--skip-browser]
```

O script:
- verifica Python no computador;
- tenta instalar Python automaticamente via `winget` se não encontrar;
- valida o provedor de IA configurado (Open Router exige `KEY` + `MODEL`; Gateway exige `URL`);
- cria `.venv`;
- instala dependências do backend;
- inicia backend e web em terminais separados;
- usa as portas locais configuradas no `.env`, com padrão `18500` e `18080`;
- abre o navegador automaticamente no frontend local (`--skip-browser` desativa);
- gera logs de inicialização na pasta `logs/` (`--no-start` só valida/instala, sem subir serviços).

### Inicialização automática (recomendado - Linux)

```bash
chmod +x start_system.sh
./start_system.sh [--yes] [--skip-browser] [--no-start]
```

O script Linux foi reforçado para um cenário mais robusto:
- valida a estrutura do projeto antes de iniciar;
- verifica Python 3.8+ e instala dependências de sistema quando necessário;
- cria/usa `.venv` e reinstala pacotes com retry;
- valida o provedor de IA configurado (Open Router exige `KEY` + `MODEL`; Gateway exige `URL`);
- valida backend e web por checagem real de resposta;
- grava logs persistentes na pasta `logs/` (`startup.log`, `backend.log`, `web.log`).

Para ambiente leve, como MiniOS, basta configurar o provedor no `.env`:

```bash
ROSITA_OPENROUTER_API_KEY=sk-or-... ROSITA_OPENROUTER_MODEL=openai/gpt-4o-mini ./start_system.sh --yes
```

Guia detalhado: `docs/linux_startup.md`.

### Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Lê o `.env` da raiz (com fallback para `backend/env.admin` e
`backend/env.defaults`, mais `backend/.env` e `.venv/admin_password.env` com
override — ver Segurança). Em dev local sobe o Flask (`app.run`); no Docker a
mesma `app:app` sobe via Gunicorn pelo `CMD` de `backend/Dockerfile:18`
(`backend/compose-entrypoint.sh` existe mas não é referenciado no
`docker-compose.yml`). Comentários no topo de `backend/Dockerfile:1` e
`web/Dockerfile:1` ainda falam em bind-mount/sem build, mas o Compose atual
faz `build` com código copiado para a imagem. Para repetir o ambiente dos scripts, use o
`.venv` da raiz (`../.venv/Scripts/python.exe` no Windows).

### Web (frontend)

Em produção o frontend é servido pelo Nginx (`web/Dockerfile` + `web/nginx.conf`,
com proxy de `/api/*` para `backend:5000`). Em desenvolvimento
local, `start_system.bat` / `start_system.sh` sobem o proxy em `web/scripts/dev_server.py`
(encaminha `/api` para o backend). O mesmo servidor pode ser iniciado à parte
(requer `flask` + `requests`, já incluídos em `backend/requirements.txt` — use o `.venv`):

```bash
cd web
python scripts/dev_server.py
```

Porta padrão: `18080` (`ROSITA_WEB_PORT`). Backend padrão do proxy:
`http://127.0.0.1:18500` (`ROSITA_BACKEND_URL`). Detalhes: `web/README.md`.

Alternativa sem proxy (`python -m http.server`) não encaminha `/api`; nesse caso
ajuste `window.ROSITA_API_BASE_URL` em `web/scripts/config.js` se a API não
estiver na mesma origem.

Abra `http://127.0.0.1:18080`.

### CLI (opcional)

```bash
python agent_cli.py
```

Reusa o mesmo núcleo da API, mas mantém o histórico só em memória durante a
sessão do terminal (não usa o SQLite). Não chama `load_dotenv` (diferente de
`backend/app.py`), então ignora `.env`/`env.admin`/`env.defaults`/`backend/.env`
em arquivo — usa só variáveis já exportadas no ambiente + defaults hardcoded em
`settings.py`. Na prática, exporte as vars ou rode com o ambiente já carregado.
O fallback `from rosita.config import` em `agent_cli.py:12-14` referencia módulo
inexistente (nunca atingido quando `rosita.settings` existe).

## Deploy com Docker / Coolify

1. copie o arquivo `.env.example` para `.env`;
2. por padrão, o projeto usa **Open Router** como provedor de IA (nuvem); o `docker-compose.yml` não traz servidor de IA interno;
3. para usar OpenRouter, configure `ROSITA_AI_PROVIDER=openrouter`, `ROSITA_OPENROUTER_API_KEY` e `ROSITA_OPENROUTER_MODEL`;
4. para usar um gateway local (IA rodando no seu servidor), configure `ROSITA_AI_PROVIDER=gateway` e `ROSITA_GATEWAY_URL`;
5. suba a stack com o Compose:

```bash
docker compose up -d --build
```

O `docker-compose.yml` padrão não exige GPU no host da ROSITA. Com OpenRouter o
processamento é na nuvem (o desempenho depende da rede e do modelo na nuvem);
com gateway local, o desempenho depende do servidor do gateway.

Se você tiver **placa NVIDIA** e o **NVIDIA Container Toolkit** instalado, crie seu próprio override GPU (não há `docker-compose.gpu.yml` incluído neste repositório).

### MiniOS e erro `overlay` / `invalid argument`

Em MiniOS ou live USB, o driver **overlay** do Docker pode falhar ao **criar** contêineres. Esse problema não é resolvido no `docker-compose.yml`. Para continuar usando **`docker compose`**, habilite o driver **`vfs`** no host com `sudo ./scripts/enable-docker-vfs-minios.sh` (detalhes em **`docs/linux_startup.md`**). Alternativa sem Docker: **`./start_system.sh`**.

Serviços padrão (com `.env` preenchido):
- Web: `http://SEU_SERVIDOR:18080`
- API: `http://SEU_SERVIDOR:18500`

Sem `.env`, o Compose publica a web em `18888:80` (fallback do serviço `web`);
o `37642` que aparece em `docker-compose.yml:33` é só o default usado para
montar o CORS do backend, não a porta pública. O healthcheck do Compose usa
`GET /api/status` (`docker-compose.yml:55`); o `GET /api/health` verifica o
provedor de IA (200 ok / 503 degradado).

Na primeira abertura, se ainda não houver modelo ativo, a própria interface web permite selecionar um modelo disponível no provedor configurado.
Nenhum modelo é baixado, ativado ou trocado automaticamente sem ação do usuário.
Os arquivos `.txt` em `backend/data` também podem ser editados pela interface e salvos no ambiente em execução — no Docker essa edição é **efêmera** (o único volume persistente é `rosita_history` para o SQLite; `backend/data` vem da imagem).

O desempenho depende do modelo escolhido no provedor configurado (Open Router ou gateway).

No Coolify, basta importar o repositório e usar o arquivo `docker-compose.yml` da raiz (CPU). Para GPU no Coolify, adicione um override próprio (ex.: `docker-compose.gpu.yml`) conforme a documentação da plataforma.

No **MiniOS ou máquina sem GPU**, se usar gateway local prefira um modelo leve
(ex.: `Llama-3.2-1B`, `Qwen2.5-0.5B`); se usar OpenRouter, prefira um modelo
leve na nuvem (ex.: `openai/gpt-4o-mini`).

## API

- `GET /` — JSON `{ "mensagem": "API ROSITA online" }`
- `GET /api/health` — healthcheck que verifica o provedor de IA (200 ok / 503 degradado)
- `GET /api/regimento/pdf` — serve o Regimento Escolar ECIM em visualização PDF. Arquivo real `regimento_ECIM.pdf` em `backend/data/`; o match é case-insensitive para `regimento_ecim.pdf`/`regimento.pdf` (`routes.py:286,292`)
- `GET /api/status` (inclui `modelo_atual`, `ocupado`, `provedor_ia`, `gateway_url`, `documentos_contexto`, `contexto_carregado`; `sistema` só para admin. Não há campo `servidor_ia`)
- `POST /api/auth/login` (rate limit 10/min; **apenas admin**), `POST /api/auth/logout`, `GET /api/auth/session`
- `POST /api/chat` (rate limit 20/min; resposta em SSE)
- `GET /api/historico`, `POST /api/limpar` (do usuário logado ou do visitante anônimo da sessão)
- `GET /api/provedores` (admin)
- `POST /api/provedores/trocar` (admin; body: `{ "provedor": "openrouter" | "gateway" }`; limpa o modelo ativo)
- `GET /api/models`, `POST /api/models/select` (admin; o modelo precisa estar na lista do provedor ativo)
- `GET /api/credenciais`, `PUT /api/credenciais` (admin; `POST` também aceito; configuração do provedor de IA, persistida em `backend/.env`)
- `GET /api/config/files` (admin; lista os `.txt` editáveis em `backend/data/` — só `.txt`, embora o contexto carregue `.txt`+`.md`)
- `GET /api/config/files/<nome>` (admin; lê um arquivo de dados)
- `PUT /api/config/files/<nome>` (admin; salva `.txt` até 300KB, com backup `<nome>.txt.bak` do conteúdo anterior (`path.suffix + .bak`), e recarrega o contexto do agente)

O plano de melhorias e correções do projeto está em `docs/PLANO_MELHORIAS.md`.

## Documentação adicional

- `docs/architecture.md` — arquitetura, camadas e provedores de IA
- `docs/ARQUITETURA.md` — decisões de arquitetura do frontend (vanilla JS sem bundler)
- `docs/implementation_plan.md` — plano de implementação frontend-first
- `docs/linux_startup.md` — guia de execução no Linux/MiniOS
- `docs/PLANO_MELHORIAS.md` — plano de melhorias e correções
- `web/README.md` — como servir o frontend localmente (proxy e modo estático)
