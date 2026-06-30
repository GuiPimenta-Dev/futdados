"""Backend de CLI: usa a assinatura via `claude -p` (modo print).

Sem messages.parse — pedimos JSON estrito no prompt, extraímos da saída e
validamos com Pydantic. Força a autenticação por assinatura removendo
ANTHROPIC_API_KEY do ambiente do subprocesso (senão o `claude` usaria a API
cobrada em vez da assinatura).
"""

from __future__ import annotations

import json
import os
import subprocess
from typing import TypeVar

from pydantic import BaseModel

from .. import config
from .jsonutil import extract_json

T = TypeVar("T", bound=BaseModel)


def complete_cli(system: str, user: str, model_cls: type[T], max_tokens: int) -> T:
    schema = json.dumps(model_cls.model_json_schema(), ensure_ascii=False)
    prompt = (
        f"{system}\n\n{user}\n\n"
        "Responda SOMENTE com um objeto JSON válido que satisfaça este schema "
        "(sem texto antes ou depois, sem cercas de código):\n"
        f"{schema}"
    )
    cmd = [config.CLAUDE_BIN, "-p", prompt, "--output-format", "json"]
    if config.CLAUDE_CLI_MODEL:
        cmd += ["--model", config.CLAUDE_CLI_MODEL]

    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300, env=env
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"CLI '{config.CLAUDE_BIN}' não encontrado no PATH. Instale o Claude "
            f"Code ou ajuste BETSTATS_CLAUDE_BIN."
        ) from exc
    if proc.returncode != 0:
        raise RuntimeError(
            f"`claude -p` falhou (rc={proc.returncode}): {proc.stderr.strip()[:500]}"
        )

    # Modo print com --output-format json devolve um envelope; o texto do
    # modelo fica em 'result'. Fallback: trata stdout como o texto direto.
    text = proc.stdout
    try:
        envelope = json.loads(proc.stdout)
        if isinstance(envelope, dict):
            if envelope.get("is_error"):
                raise RuntimeError(f"`claude -p` retornou erro: {envelope.get('result')}")
            text = envelope.get("result", proc.stdout)
    except json.JSONDecodeError:
        pass

    return model_cls.model_validate(extract_json(text))
