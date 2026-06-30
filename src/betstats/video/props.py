"""Monta o props.json determinístico que o Remotion consome.

Fluxo: roteiro (hook + beats + cta) -> narração única -> TTS com timestamps ->
palavras alinhadas -> fatiadas por segmento -> blocos de legenda + card de stat
por beat (puxado do Fact via ScriptOutput.beat_facts).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil

from ..trace import slugify
from .sfx import ensure_sfx
from .tts import Word, synthesize

VIDEO_DIR = "video"
PUBLIC_DIR = os.path.join(VIDEO_DIR, "public")
FPS = 30
BLOCK_SIZE = 4  # palavras por bloco de legenda (3-5; decisão de tom)
TAIL_SEC = 0.6  # respiro no fim


def _norm(s: str) -> str:
    return " ".join(s.split())


def _abbr(name: str) -> str:
    parts = re.findall(r"[A-Za-zÀ-ÿ]+", name)
    base = parts[-1] if parts else name
    return base[:3].upper()


def _color(name: str) -> str:
    h = int(hashlib.md5(name.encode("utf-8")).hexdigest(), 16) % 360
    return f"hsl({h}, 62%, 52%)"


def _team_props(team) -> dict:
    if team is None:
        return {"name": "?", "abbr": "?", "logo": None, "color": "hsl(140, 60%, 45%)"}
    return {
        "name": team.name,
        "abbr": _abbr(team.name),
        "logo": team.logo,
        "color": _color(team.name),
    }


def _blocks(words: list[Word]) -> list[dict]:
    out = []
    for i in range(0, len(words), BLOCK_SIZE):
        chunk = words[i : i + BLOCK_SIZE]
        out.append(
            {
                "startSec": chunk[0].start,
                "endSec": chunk[-1].end,
                "words": [{"w": w.w, "startSec": w.start, "endSec": w.end} for w in chunk],
            }
        )
    return out


_PCT_PAIR = re.compile(r"^(\d+)%\s*/\s*(\d+)%$")


def _card_value(value: str) -> str:
    """Número LIMPO pro card. Fatos de convergência vêm como 'a%/b%' (duas taxas
    grudadas, ilegível no número gigante) — colapsa pro menor (a condição que se
    sustenta nos dois lados; é o mesmo critério de força do engine)."""
    m = _PCT_PAIR.match((value or "").strip())
    if m:
        return f"{min(int(m.group(1)), int(m.group(2)))}%"
    return value


def _stat_of(f) -> dict:
    return {
        "value": _card_value(f.value),
        "market": f.markets[0] if f.markets else None,
        "force": f.strength or None,
    }


def _stat_for_beat(i: int, script, ranked) -> dict | None:
    bf = getattr(script, "beat_facts", None) or []
    if i < len(bf) and 0 <= bf[i] < len(ranked):
        return _stat_of(ranked[bf[i]].fact)
    return None


def build_props(result) -> dict:
    """Sintetiza o áudio e devolve (props_dict, slug, audio_bytes)."""
    script, ranked = result.script, result.ranked
    if not (script and ranked):
        raise ValueError("build_props exige result.script e result.ranked (rode com LLM).")

    # 1) narração única, na ordem de narração
    kinds = ["hook"] + ["beat"] * len(script.beats) + ["cta"]
    texts = [_norm(t) for t in ([script.hook] + list(script.beats) + [script.cta])]
    narration = " ".join(texts)

    # 2) TTS com timestamps por palavra
    speech = synthesize(narration)
    words = speech.words

    # 3) fatia as palavras por segmento (contagem por palavra do texto escrito;
    #    o alinhamento do EL é sobre o texto de ENTRADA, então as contagens batem)
    written_total = sum(len(t.split()) for t in texts)
    if len(words) != written_total:
        print(
            f"[video] aviso: {len(words)} palavras alinhadas vs {written_total} escritas "
            f"— fatiamento por segmento pode deslizar."
        )

    segments, cursor, beat_i = [], 0, 0
    for kind, text in zip(kinds, texts):
        n = len(text.split())
        seg_words = words[cursor : cursor + n]
        cursor += n
        stat = None
        if kind == "hook" and ranked:
            # frame de abertura = número-choque do fato mais forte (ranked[0])
            stat = _stat_of(ranked[0].fact)
        elif kind == "beat":
            stat = _stat_for_beat(beat_i, script, ranked)
            beat_i += 1
        if not seg_words:
            continue
        segments.append(
            {
                "kind": kind,
                "text": text,
                "startSec": seg_words[0].start,
                "endSec": seg_words[-1].end,
                "stat": stat,
                "blocks": _blocks(seg_words),
            }
        )

    duration = (words[-1].end if words else 0.0) + TAIL_SEC
    slug = slugify(result.matchup)

    # SFX sintéticos: impacto no gancho, whoosh na entrada de cada card de beat.
    sfx_files = ensure_sfx()
    sfx_events = []
    for s in segments:
        if s["kind"] == "hook":
            sfx_events.append({"src": sfx_files["impact.wav"], "atSec": s["startSec"]})
        elif s["kind"] == "beat" and s["stat"]:
            sfx_events.append({"src": sfx_files["whoosh.wav"], "atSec": s["startSec"]})

    props = {
        "matchup": result.matchup,
        "phase": result.phase,
        "title": script.title,
        "thumbHook": getattr(script, "thumb_hook", "") or "",
        "teamA": _team_props(result.team_a),
        "teamB": _team_props(result.team_b),
        "audio": f"{slug}.mp3",  # staticFile em video/public/
        "music": sfx_files["bed.wav"],  # bed grave em loop, baixo
        "sfx": sfx_events,
        "fps": FPS,
        "durationSec": round(duration, 3),
        "source": f"Copa 2026 · {ranked[0].fact.sample} jogos" if ranked else "Copa 2026",
        "segments": segments,
    }
    return props, slug, speech.audio


def write_assets(result, out_dir: str) -> dict:
    """Sintetiza áudio e escreve mp3 (video/public, p/ staticFile) + props.json
    (out/.work/<slug>/). Os artefatos finais do render também vão pro .work até
    serem empacotados na pasta do jogo (ver publish.package_match). Retorna caminhos."""
    from .publish import work_dir

    props, slug, audio = build_props(result)

    os.makedirs(PUBLIC_DIR, exist_ok=True)
    wdir = work_dir(out_dir, slug)
    os.makedirs(wdir, exist_ok=True)

    mp3_path = os.path.join(PUBLIC_DIR, f"{slug}.mp3")
    with open(mp3_path, "wb") as fh:
        fh.write(audio)
    # cópia de arquivo do mp3 no .work (arquivamento; o canônico fica em public)
    shutil.copyfile(mp3_path, os.path.join(wdir, "audio.mp3"))

    props_path = os.path.join(wdir, "props.json")
    with open(props_path, "w", encoding="utf-8") as fh:
        json.dump(props, fh, ensure_ascii=False, indent=2)

    return {
        "props": props_path,
        "mp3": mp3_path,
        "slug": slug,
        "work": wdir,
        "raw": os.path.join(wdir, "video.raw.mp4"),
        "mp4": os.path.join(wdir, "video.mp4"),
        "thumb": os.path.join(wdir, "thumbnail.png"),
        "duration": props["durationSec"],
    }
