"""Trace de execução: grava TODO o estado do pipeline em JSON, um por run.

Captura o que antes era efêmero — a lista COMPLETA de candidatos (pré-ranker),
a decisão do ranqueador (índices/score/justificativa) e o roteiro final — além
de metadados (jogo, temporada, backend, timestamp). Um arquivo por execução em
traces/, para auditoria e para afinar ranker/voz revendo o histórico.
"""

from __future__ import annotations

import dataclasses
import json
import os
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any

from . import config

if TYPE_CHECKING:
    from .pipeline import PipelineResult


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "saida"


def build_payload(result: "PipelineResult", meta: dict | None = None) -> dict[str, Any]:
    """O dicionário do trace (separado da escrita p/ facilitar teste/uso)."""
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        **(meta or {}),
        "matchup": result.matchup,
        "phase": result.phase,
        "n_candidates": len(result.candidates),
        # dados ANTES do ranker — a lista completa:
        "candidates": [dataclasses.asdict(f) for f in result.candidates],
        # decisão do ranker (None se rodou --no-llm):
        "ranked": None
        if result.ranked is None
        else [
            {
                "interest": r.interest,
                "rationale": r.rationale,
                "fact": dataclasses.asdict(r.fact),
            }
            for r in result.ranked
        ],
        # roteiro final (ScriptOutput é Pydantic):
        "script": None if result.script is None else result.script.model_dump(),
    }


def write_trace(
    result: "PipelineResult", meta: dict | None = None, out_dir: str | None = None
) -> str:
    out_dir = out_dir or config.TRACE_DIR
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:-3]
    path = os.path.join(out_dir, f"{slugify(result.matchup)}__{stamp}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(build_payload(result, meta), fh, ensure_ascii=False, indent=2)
    return path
