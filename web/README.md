# Frontend Web da ROSITA

O frontend é uma interface em HTML, CSS e JavaScript Vanilla. Ele é servido pelo
Nginx no Docker ou por um servidor de desenvolvimento local com proxy para o Flask.

## Recursos da interface

- Chat com respostas em streaming via Server-Sent Events.
- Login administrativo e acesso anônimo ao chat.
- Histórico da sessão, limpeza e exportação/exclusão de dados.
- Visualização do PDF oficial do Regimento Escolar ECIM.
- Temas claro e escuro.
- Painéis administrativos de provedor, modelo, credenciais e referências.
- Status de servidor, CPU, memória, disco e GPU quando disponível.
- Layout responsivo para desktop, tablet e celular.

## Arquivos principais

```text
web/
├── index.html
├── nginx.conf
├── scripts/
│   ├── api_client.js
│   ├── config.js
│   ├── dev_server.py
│   └── main.js
└── styles/
    └── main.css
```

## Execução local com proxy

Na raiz do projeto:

```bash
cd web
python scripts/dev_server.py
```

Padrões:

- Interface: `http://127.0.0.1:18080`
- Backend: `http://127.0.0.1:18500`

As portas podem ser alteradas:

```bash
ROSITA_WEB_PORT=18081 ROSITA_BACKEND_URL=http://127.0.0.1:18501 python scripts/dev_server.py
```

O servidor local encaminha `/api/*` ao backend. `ROSITA_WEB_HOST` define a
interface de rede do servidor e `ROSITA_WEB_PORT` define a porta.

## Execução somente estática

É possível servir os arquivos com um servidor HTTP simples:

```bash
cd web
python -m http.server 18080
```

Nesse modo, o navegador não possui proxy automático para o backend. Configure
`window.ROSITA_API_BASE_URL` em `scripts/config.js` apenas quando o backend
não estiver disponível na mesma origem.

## Docker e produção

O `Dockerfile` do frontend usa Nginx. O arquivo `nginx.conf` recebe requisições
HTTP em `/` e encaminha `/api/*` para `backend:5000`.

Em produção, o conjunto web/backend deve ficar atrás de HTTPS. O proxy reverso
deve encaminhar `X-Forwarded-Proto: https` para que o backend aceite as
requisições e configure os cookies seguros conforme a configuração do projeto.

Porta padrão do Compose:

- Com `ROSITA_WEB_PORT=18080`: `http://127.0.0.1:18080`
- Sem a variável: fallback `18888`

## Temas e responsividade

Cada abertura da interface inicia no tema escuro. O botão da barra lateral
permite alternar o tema durante a sessão. Os breakpoints principais são:

- Acima de 1100 px: barra lateral completa.
- Entre 701 px e 1100 px: barra lateral compacta.
- Até 700 px: navegação superior.

## Consistência documental

Para arquitetura, instalação, segurança e referência de API, consulte:

- [README principal](../README.md)
- [Arquitetura do frontend](../docs/arquitetura-frontend.md)
- [Arquitetura do backend](../docs/arquitetura-backend.md)
- [Execução no Linux e MiniOS](../docs/linux_startup.md)
