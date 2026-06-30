"""Backend de API (SDK Anthropic). Usa messages.parse() com schema Pydantic."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from .client import make_client, thinking_kwargs

T = TypeVar("T", bound=BaseModel)


def complete_api(
    system: str, user: str, model_cls: type[T], model_id: str, max_tokens: int
) -> T:
    client = make_client()
    resp = client.messages.parse(
        model=model_id,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_format=model_cls,
        **thinking_kwargs(),
    )
    out = resp.parsed_output
    if out is None:
        raise RuntimeError(f"LLM (api) não retornou saída (stop={resp.stop_reason}).")
    return out
