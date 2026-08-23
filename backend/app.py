"""Entrypoint da API Flask ROSITA."""

import logging
import os
from pathlib import Path
import sys

from dotenv import load_dotenv

# Permite importar o pacote em backend/src sem instalar no ambiente.
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
SRC_DIR = BACKEND_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rosita.app_factory import create_app
from rosita.settings import load_settings

# Precedência: variáveis já exportadas no ambiente > .env da raiz > backend/.env
# > backend/env.defaults. Sem override=True, o primeiro valor definido vence.
load_dotenv(BASE_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(BACKEND_DIR / "env.defaults")

# Logging estruturado centralizado (nível controlado por ROSITA_DEBUG).
_debug = os.getenv("ROSITA_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}
logging.basicConfig(
    level=logging.DEBUG if _debug else logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("rosita")

app = create_app()
settings = load_settings()


if __name__ == "__main__":
    logger.info("Servidor iniciando em %s:%s", settings.api_host, settings.api_port)
    app.run(host=settings.api_host, port=settings.api_port, debug=settings.debug)
