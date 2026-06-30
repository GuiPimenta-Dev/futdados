"""Extração tolerante de JSON da saída de texto de um LLM (stdlib apenas).

Isolado aqui (sem pydantic/anthropic) para poder ser testado offline.
"""

from __future__ import annotations

import json
import re
from typing import Any


def extract_json(text: str) -> Any:
    """Tenta decodificar um objeto JSON de `text`, tolerando cercas de código
    e texto em volta.
    """
    text = text.strip()
    if text.startswith("```"):  # ```json ... ```
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise
