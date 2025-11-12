"""Configurações para o pipeline de ETL.

Este módulo centraliza a configuração do logging da aplicação e o
carregamento de variáveis de ambiente a partir de arquivos ``.env``.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

ENV_FILE = os.getenv("GUAXINDIBA_ENV_FILE", ".env")
LOG_LEVEL_ENV = "GUAXINDIBA_LOG_LEVEL"
LOG_FORMAT_ENV = "GUAXINDIBA_LOG_FORMAT"
_DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def load_environment(path: os.PathLike[str] | str = ENV_FILE, *, override: bool = False) -> dict[str, str]:
    """Carrega variáveis de ambiente a partir de um arquivo ``.env``.

    Cada linha deve seguir o formato ``CHAVE=valor``. Linhas vazias e
    comentários iniciados com ``#`` são ignorados.

    Args:
        path: Caminho para o arquivo ``.env``.
        override: Se ``True`` substitui variáveis já definidas em
            ``os.environ``.

    Returns:
        Um dicionário com as variáveis carregadas.
    """

    env_path = Path(path)
    if not env_path.exists():
        return {}

    loaded: dict[str, str] = {}

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")

        if not key:
            continue

        if override or key not in os.environ:
            os.environ[key] = value

        loaded[key] = value

    return loaded


def _resolve_log_level(level: str | int) -> int:
    if isinstance(level, int):
        return level

    level_name = level.upper()
    return getattr(logging, level_name, logging.INFO)


def configure_logging(level: str | int | None = None, fmt: str | None = None) -> None:
    """Configura o logging da aplicação.

    Args:
        level: Nível de logging (``INFO``, ``DEBUG``, etc.). Caso ``None``
            utiliza o valor definido em variáveis de ambiente ou o padrão
            ``INFO``.
        fmt: Formato da mensagem de log. Caso ``None`` usa o formato
            definido em ``GUAXINDIBA_LOG_FORMAT`` ou o padrão.
    """

    level_value = _resolve_log_level(level or os.getenv(LOG_LEVEL_ENV, "INFO"))
    fmt_value = fmt or os.getenv(LOG_FORMAT_ENV, _DEFAULT_LOG_FORMAT)

    root_logger = logging.getLogger()

    if root_logger.handlers:
        root_logger.setLevel(level_value)
        for handler in root_logger.handlers:
            handler.setLevel(level_value)
            handler.setFormatter(logging.Formatter(fmt_value))
        return

    logging.basicConfig(level=level_value, format=fmt_value)


ENV_VARS = load_environment()
configure_logging()

__all__ = [
    "ENV_VARS",
    "ENV_FILE",
    "configure_logging",
    "load_environment",
]
