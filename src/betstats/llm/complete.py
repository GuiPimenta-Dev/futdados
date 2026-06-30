"""Dispatcher: escolhe o backend de LLM (assinatura via CLI ou API) e devolve
uma instância Pydantic validada. Importa o backend escolhido de forma tardia
para que o caminho 'claude_cli' não exija o SDK Anthropic.
"""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from .. import config

T = TypeVar("T", bound=BaseModel)


def structured_complete(
    system: str, user: str, model_cls: type[T], *, model_id: str, max_tokens: int
) -> T:
    if config.LLM_BACKEND == "api":
        from .api_backend import complete_api

        return complete_api(system, user, model_cls, model_id, max_tokens)
    from .cli_backend import complete_cli

    return complete_cli(system, user, model_cls, max_tokens)
