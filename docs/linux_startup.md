# Execução no Linux e MiniOS

## Requisitos

- Linux com Bash.
- Python 3.8 ou superior recomendado.
- Bash e permissões de execução.
- Conexão com OpenRouter ou um Gateway OpenAI-compatible.

## Inicialização automatizada

Na raiz do projeto:

```bash
chmod +x start_system.sh
./start_system.sh
```

O script valida a estrutura do projeto, cria ou reutiliza `.venv`, instala
dependências e inicia o backend e o frontend local. Ele também grava logs em
`logs/startup.log`, `logs/backend.log` e `logs/web.log`.

Opções disponíveis:

```text
--yes           Aprovar instalações necessárias automaticamente
--skip-browser  Não abrir o navegador
--no-start      Instalar e validar sem iniciar os serviços
```

Portas padrão:

- Backend: `http://127.0.0.1:18500`
- Web: `http://127.0.0.1:18080`

## Docker

Para uma implantação com Docker Compose:

```bash
cp .env.example .env
docker compose up -d --build
```

Configure o provedor no `.env` antes de iniciar. Em produção, use HTTPS por
meio de um proxy reverso e encaminhe `X-Forwarded-Proto: https`.

O backend não publica uma porta diretamente no host; o Nginx recebe o tráfego
da porta pública configurada por `ROSITA_WEB_PORT`.

## Driver de armazenamento no MiniOS

Em MiniOS, live USB ou sistemas de arquivos pouco compatíveis, o Docker pode
apresentar erro de montagem com o driver `overlay`. A alternativa mais simples
é executar o projeto nativamente com `./start_system.sh`.

Para tentar corrigir o Docker, habilite o driver `vfs` no host:

```bash
sudo ./scripts/enable-docker-vfs-minios.sh
```

O script usa `docker/minios-vfs-daemon.json` e pode criar uma cópia de segurança
do `daemon.json` existente. Reinicie o Docker e execute novamente:

```bash
docker compose up -d --build
```

O modo `vfs` utiliza mais espaço em disco e pode ser mais lento.

## Ajuste de portas

```bash
ROSITA_API_PORT=18501 ROSITA_WEB_PORT=18081 ./start_system.sh --yes
```
