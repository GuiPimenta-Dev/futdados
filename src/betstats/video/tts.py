"""Síntese de voz com timestamps por palavra (ElevenLabs).

Uma chamada devolve o áudio E o alinhamento por caractere; agrupamos os
caracteres em palavras (start/end de cada palavra) pra legenda animada do vídeo.
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass


@dataclass
class Word:
    w: str
    start: float  # segundos
    end: float


@dataclass
class Speech:
    audio: bytes  # mp3
    words: list[Word]

    @property
    def duration(self) -> float:
        return self.words[-1].end if self.words else 0.0


# Voz travada na sessão de tom: Daniel (masc., autoritária), casa com "analista".
VOICE_ID = os.getenv("BETSTATS_VOICE_ID", "onwK4e9ZLuTAKqWW03F9")
MODEL_ID = os.getenv("BETSTATS_TTS_MODEL", "eleven_multilingual_v2")


def _chars_to_words(chars: list[str], starts: list[float], ends: list[float]) -> list[Word]:
    """Agrupa o alinhamento por caractere em palavras (corta em espaço)."""
    words: list[Word] = []
    cur = ""
    cur_start: float | None = None
    cur_end = 0.0
    for ch, st, en in zip(chars, starts, ends):
        if ch.isspace():
            if cur:
                words.append(Word(cur, cur_start or 0.0, cur_end))
                cur, cur_start = "", None
            continue
        if cur_start is None:
            cur_start = st
        cur += ch
        cur_end = en
    if cur:
        words.append(Word(cur, cur_start or 0.0, cur_end))
    return words


def synthesize(text: str) -> Speech:
    """Sintetiza `text` e devolve áudio mp3 + timing por palavra."""
    from elevenlabs import ElevenLabs, VoiceSettings

    client = ElevenLabs()  # ELEVENLABS_API_KEY do ambiente
    resp = client.text_to_speech.convert_with_timestamps(
        voice_id=VOICE_ID,
        text=text,
        model_id=MODEL_ID,
        language_code="pt",
        apply_text_normalization="on",
        output_format="mp3_44100_128",
        voice_settings=VoiceSettings(
            stability=0.45,
            similarity_boost=0.8,
            style=0.25,
            speed=1.06,
            use_speaker_boost=True,
        ),
    )
    audio = base64.b64decode(resp.audio_base_64)
    a = resp.alignment
    words = _chars_to_words(
        a.characters,
        a.character_start_times_seconds,
        a.character_end_times_seconds,
    )
    return Speech(audio=audio, words=words)
