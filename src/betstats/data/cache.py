"""Cache em arquivo JSON para respostas da API (economiza rate limit).

Chave = caminho + querystring. Respostas de jogos finalizados não mudam, então
o cache é seguro e agressivo. Apague o diretório .cache/ para forçar refetch.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from .. import config


def _path_for(key: str) -> str:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    return os.path.join(config.CACHE_DIR, f"{digest}.json")


def get(key: str) -> Any | None:
    path = _path_for(key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


def put(key: str, value: Any) -> None:
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    with open(_path_for(key), "w", encoding="utf-8") as fh:
        json.dump(value, fh, ensure_ascii=False)
