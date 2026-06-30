"""SFX + bed musical SINTÉTICOS (stdlib, sem dependência nem licença).

Gera uma vez em video/public/sfx/ e reusa (cache por existência). São sons de
marca, leves: whoosh na entrada de card, ding/impacto no gancho, e um bed grave
discreto em loop. Trocar por trilha licenciada é só substituir o arquivo.
"""

from __future__ import annotations

import math
import os
import random
import struct
import wave

RATE = 44100
SFX_DIR = os.path.join("video", "public", "sfx")


def _write(path: str, samples: list[float]) -> None:
    peak = max(1e-6, max(abs(s) for s in samples))
    norm = 0.92 / peak if peak > 0.92 else 1.0
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        frames = b"".join(
            struct.pack("<h", int(max(-1.0, min(1.0, s * norm)) * 32767)) for s in samples
        )
        w.writeframes(frames)


def _whoosh(dur: float = 0.32) -> list[float]:
    n = int(RATE * dur)
    rnd = random.Random(7)
    out, prev = [], 0.0
    for i in range(n):
        t = i / n
        env = math.sin(math.pi * t) ** 1.5  # sobe e desce
        # ruído passa-baixa simples (média móvel) = "ar" em vez de chiado
        white = rnd.uniform(-1, 1)
        prev = prev * 0.82 + white * 0.18
        out.append(prev * env * 0.7)
    return out


def _ding(dur: float = 0.5, base: float = 880.0) -> list[float]:
    n = int(RATE * dur)
    out = []
    for i in range(n):
        t = i / RATE
        env = math.exp(-t * 9.0)
        s = math.sin(2 * math.pi * base * t) + 0.5 * math.sin(2 * math.pi * base * 1.5 * t)
        out.append(s * env * 0.55)
    return out


def _impact(dur: float = 0.6) -> list[float]:
    """Gancho: boom grave com sweep pra baixo + ding por cima."""
    n = int(RATE * dur)
    out = []
    ding = _ding(dur=dur, base=660.0)
    for i in range(n):
        t = i / RATE
        f = 120.0 * math.exp(-t * 6.0) + 45.0  # sweep 165->45 Hz
        env = math.exp(-t * 5.0)
        boom = math.sin(2 * math.pi * f * t) * env
        out.append(boom * 0.8 + ding[i] * 0.5)
    return out


def _bed(dur: float = 8.0) -> list[float]:
    """Pad grave discreto, comprimento múltiplo das freqs => loop sem emenda."""
    n = int(RATE * dur)
    out = []
    for i in range(n):
        t = i / RATE
        trem = 0.85 + 0.15 * math.sin(2 * math.pi * 0.25 * t)  # 2 ciclos em 8s
        s = (
            math.sin(2 * math.pi * 110.0 * t)
            + 0.6 * math.sin(2 * math.pi * 165.0 * t)
            + 0.3 * math.sin(2 * math.pi * 220.0 * t)
        )
        out.append(s * trem * 0.18)
    return out


_FILES = {
    "whoosh.wav": _whoosh,
    "ding.wav": _ding,
    "impact.wav": _impact,
    "bed.wav": _bed,
}


def ensure_sfx() -> dict[str, str]:
    """Gera os arquivos se faltarem. Retorna {nome: caminho relativo a public/}."""
    os.makedirs(SFX_DIR, exist_ok=True)
    out = {}
    for name, fn in _FILES.items():
        path = os.path.join(SFX_DIR, name)
        if not os.path.exists(path):
            _write(path, fn())
        out[name] = f"sfx/{name}"  # relativo a video/public (staticFile)
    return out
