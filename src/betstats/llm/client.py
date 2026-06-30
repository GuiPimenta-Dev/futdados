"""Fábrica do cliente Claude e kwargs comuns (pensamento adaptativo)."""

from __future__ import annotations

import os

import anthropic

from .. import config


class MissingAnthropicKey(RuntimeError):
    pass


def make_client() -> anthropic.Anthropic:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise MissingAnthropicKey(
            "ANTHROPIC_API_KEY ausente. Preencha o .env (ver .env.example)."
        )
    return anthropic.Anthropic()


def thinking_kwargs() -> dict:
    """Pensamento adaptativo (recomendado p/ tarefas de julgamento e escrita)."""
    return {"thinking": {"type": "adaptive"}} if config.USE_ADAPTIVE_THINKING else {}
