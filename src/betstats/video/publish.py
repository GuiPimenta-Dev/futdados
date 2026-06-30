"""Empacotamento final por jogo: pasta 'Time A x Time B/' com vídeo, thumbnail,
publicacao.txt (legenda + hashtags) e roteiro.md. Intermediários vão pra .work/.

Hashtags = camada de ALCANCE fixa (config.BASE_HASHTAGS) + times derivados +
tags de mercado do LLM → dedupe preservando ordem → corte em MAX_HASHTAGS.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import unicodedata

from .. import config

# Logo de marca: o fonte (logo.png na raiz) tem fundo preto; o vídeo precisa de
# uma versão TRANSPARENTE. Geramos uma vez em video/public/logo.png por
# luminance-key (alpha = brilho), preservando a arte branca+verde com borda limpa.
LOGO_SRC = "logo.png"
LOGO_DST = os.path.join("video", "public", "logo.png")
_LOGO_KEY = (
    "format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
    "a='min(255,1.6*max(max(r(X,Y),g(X,Y)),b(X,Y)))'"
)


def ensure_brand() -> bool:
    """Garante video/public/logo.png (transparente). Retorna True se disponível."""
    if os.path.exists(LOGO_DST):
        return True
    if not os.path.exists(LOGO_SRC):
        print(f"[video] logo ausente ({LOGO_SRC}) — vídeo sai sem marca d'água.")
        return False
    os.makedirs(os.path.dirname(LOGO_DST), exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", LOGO_SRC, "-vf", _LOGO_KEY, LOGO_DST]
    try:
        return subprocess.run(cmd).returncode == 0
    except FileNotFoundError:
        return False


def _tag(text: str) -> str:
    """Nome → hashtag: sem acento, sem espaço, minúsculo. 'Coreia do Sul'→'coreiadosul'."""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_ = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", ascii_.lower())


def build_hashtags(team_a_name: str, team_b_name: str, llm_tags: list[str]) -> list[str]:
    ordered = (
        list(config.BASE_HASHTAGS)
        + [_tag(team_a_name), _tag(team_b_name)]
        + [_tag(t) for t in llm_tags]
    )
    seen, out = set(), []
    for t in ordered:
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out[: config.MAX_HASHTAGS]


def _safe_dir(name: str) -> str:
    return name.replace("/", "-").replace(os.sep, "-").strip()


def work_dir(out_dir: str, slug: str) -> str:
    return os.path.join(out_dir, ".work", slug)


def publicacao_text(caption: str, hashtags: list[str]) -> str:
    tags = " ".join(f"#{h}" for h in hashtags)
    return f"{caption.strip()}\n\n{tags}\n"


def package_match(
    matchup: str,
    out_dir: str,
    *,
    mp4: str,
    thumbnail: str,
    roteiro_md: str,
    caption: str,
    hashtags: list[str],
) -> str:
    """Monta out/<Time A x Time B>/ com os 4 entregáveis. Retorna o caminho da pasta."""
    folder = os.path.join(out_dir, _safe_dir(matchup))
    os.makedirs(folder, exist_ok=True)

    shutil.move(mp4, os.path.join(folder, "video.mp4"))
    if thumbnail and os.path.exists(thumbnail):
        shutil.move(thumbnail, os.path.join(folder, "thumbnail.png"))
    with open(os.path.join(folder, "publicacao.txt"), "w", encoding="utf-8") as fh:
        fh.write(publicacao_text(caption, hashtags))
    with open(os.path.join(folder, "roteiro.md"), "w", encoding="utf-8") as fh:
        fh.write(roteiro_md)
    return folder
