#!/usr/bin/env python3
"""CLI do betstats.

Uso:
  python run.py --demo                 # roda no dataset sintético (offline)
  python run.py --fixture <ID>         # roda num jogo real da Copa (precisa de APISPORTS_KEY)
  python run.py --list                 # lista os jogos da Copa
  python run.py --next-round           # lista os próximos jogos ainda não disputados

Os LLMs (ranqueador + roteirista) só rodam se ANTHROPIC_API_KEY estiver no .env.
Use --no-llm para parar na validação (só os fatos candidatos).
"""

from __future__ import annotations

import argparse
import dataclasses
import os
import subprocess
import sys

# Permite `python run.py` sem instalar o pacote.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

try:  # dotenv é opcional — o caminho offline (--demo --no-llm) roda sem deps
    from dotenv import load_dotenv

    load_dotenv()
except ModuleNotFoundError:
    pass

from betstats import config  # noqa: E402
from betstats.config import BRASILEIRAO_A_2026, WORLD_CUP_2026  # noqa: E402
from betstats.output import render_candidates, render_full  # noqa: E402
from betstats.pipeline import PipelineResult, run_fixture, run_matchup  # noqa: E402
from betstats.rules.brasileirao import BrasileiraoRules  # noqa: E402
from betstats.rules.world_cup import WorldCupRules  # noqa: E402
from betstats.trace import slugify, write_trace  # noqa: E402

_COMPS = {"wc": WORLD_CUP_2026, "brasileirao": BRASILEIRAO_A_2026}


def _make_rules(comp, provider):
    """Copa -> WorldCupRules; Brasileirão -> BrasileiraoRules com a tabela."""
    if comp.key == BRASILEIRAO_A_2026.key:
        table = provider.get_standings(comp) if provider else {}
        return BrasileiraoRules(comp, table_position=table or None)
    return WorldCupRules(comp)


def _use_llm(no_llm: bool) -> bool:
    if no_llm:
        return False
    if config.LLM_BACKEND == "api" and not os.getenv("ANTHROPIC_API_KEY"):
        print("[i] backend 'api' sem ANTHROPIC_API_KEY — parando na validação (só candidatos).\n")
        return False
    print(f"[i] LLM backend: {config.LLM_BACKEND}")
    return True


def _remotion(args: list[str]) -> bool:
    from betstats.video.props import VIDEO_DIR

    return subprocess.run(["npx", "remotion", *args], cwd=VIDEO_DIR).returncode == 0


def _make_video(result: PipelineResult, roteiro_md: str) -> None:
    """Gera voz + props, renderiza vídeo (+loudnorm) e thumbnail, e empacota
    tudo em out/<Time A x Time B>/ (video.mp4, thumbnail.png, publicacao.txt, roteiro.md)."""
    if not (result.script and result.ranked):
        print("[video] sem roteiro (rode sem --no-llm) — pulei o vídeo.")
        return
    from betstats.video.props import VIDEO_DIR, write_assets
    from betstats.video.publish import build_hashtags, ensure_brand, package_match

    ensure_brand()  # garante a logo transparente em video/public/
    print("[video] sintetizando voz + montando props.json…")
    paths = write_assets(result, config.OUT_DIR)
    props_abs = os.path.abspath(paths["props"])
    print(f"[video] props: {paths['props']}  |  ~{paths['duration']:.0f}s")

    if not os.path.isdir(os.path.join(VIDEO_DIR, "node_modules")):
        print(f"[video] deps do Remotion ausentes — rode:  (cd {VIDEO_DIR} && npm install) e re-execute.")
        return

    # 1) vídeo (render cru -> loudnorm)
    print("[video] renderizando vídeo…")
    if not _remotion(["render", "BetVideo", os.path.abspath(paths["raw"]), f"--props={props_abs}"]):
        print("[video] render do vídeo falhou.")
        return
    if _loudnorm(paths["raw"], paths["mp4"]):
        os.remove(paths["raw"])
    else:
        os.replace(paths["raw"], paths["mp4"])  # mantém cru se ffmpeg faltar

    # 2) thumbnail (still)
    print("[video] renderizando thumbnail…")
    if not _remotion(["still", "Thumbnail", os.path.abspath(paths["thumb"]), f"--props={props_abs}"]):
        print("[video] thumbnail falhou — sigo sem ela.")

    # 3) empacota a pasta do jogo
    tags = build_hashtags(
        result.team_a.name if result.team_a else "",
        result.team_b.name if result.team_b else "",
        result.script.hashtags,
    )
    folder = package_match(
        result.matchup,
        config.OUT_DIR,
        mp4=paths["mp4"],
        thumbnail=paths["thumb"],
        roteiro_md=roteiro_md,
        caption=result.script.caption,
        hashtags=tags,
    )
    print(f"[ok] Entregável em {folder}/ (video.mp4 · thumbnail.png · publicacao.txt · roteiro.md)")
    print(f"[ok] Hashtags: {' '.join('#' + t for t in tags)}")


def _loudnorm(src: str, dst: str) -> bool:
    """Normaliza loudness pro padrão de plataforma (I=-14 LUFS, TP=-1.5 dBTP).

    Vídeo copiado sem recodificar; só o áudio é reprocessado. Retorna False se
    o ffmpeg faltar ou falhar (o caller mantém o render cru nesse caso).
    """
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error", "-i", src,
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
        "-c:v", "copy",
        "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k",
        "-movflags", "+faststart",
        dst,
    ]
    try:
        return subprocess.run(cmd).returncode == 0
    except FileNotFoundError:
        return False


def _emit(
    result: PipelineResult, meta: dict, trace_enabled: bool = True, make_video: bool = False
) -> None:
    print(f"== {result.matchup} — {result.phase} ==")
    print(f"{len(result.candidates)} fatos candidatos validados:\n")
    for f in result.candidates:
        print(f"  [{f.category}/{f.kind}] {f.text}")
    print()

    os.makedirs(config.OUT_DIR, exist_ok=True)
    if result.script and result.ranked:
        md = render_full(result.matchup, result.phase, result.ranked, result.script)
        print("--- ROTEIRO ---")
        print(f"Gancho: {result.script.hook}")
        for i, b in enumerate(result.script.beats, 1):
            print(f"  {i}. {b}")
        print(f"CTA: {result.script.cta}")
        print(f"Título: {result.script.title}\n")
    else:
        md = render_candidates(result.matchup, result.phase, result.candidates)

    # Com --video, o roteiro vai pra pasta do jogo (roteiro.md). Sem vídeo,
    # mantém o .md solto em out/ (comportamento antigo).
    if not make_video:
        path = os.path.join(config.OUT_DIR, f"{slugify(result.matchup)}.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(md)
        print(f"[ok] Saída salva em {path}")

    if trace_enabled:
        print(f"[trace] Execução registrada em {write_trace(result, meta)}")

    if make_video:
        _make_video(result, md)


def _make_provider():
    """Fonte de dados: ESPN (grátis, padrão) ou API-Football (fallback pago)."""
    if config.DATA_PROVIDER == "api_football":
        from betstats.data.api_football import APIFootballProvider

        return APIFootballProvider()
    from betstats.data.espn import ESPNProvider

    return ESPNProvider()


def main() -> int:
    ap = argparse.ArgumentParser(description="betstats — curiosidades estatísticas (Copa 2026)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--demo", action="store_true", help="roda no dataset sintético (offline)")
    g.add_argument("--fixture", type=int, metavar="ID", help="ID do jogo na API-Football")
    g.add_argument("--list", action="store_true", help="lista os jogos da Copa")
    g.add_argument("--next-round", action="store_true", help="lista jogos ainda não disputados")
    ap.add_argument("--no-llm", action="store_true", help="para na validação (sem LLM)")
    ap.add_argument("--no-trace", action="store_true", help="não grava o JSON de trace da execução")
    ap.add_argument(
        "--video",
        action="store_true",
        help="gera o entregável em vídeo (TTS + props.json + render Remotion .mp4)",
    )
    ap.add_argument(
        "--season",
        type=int,
        default=None,
        help="sobrescreve a temporada (ex.: 2022/2023 p/ testar no plano grátis da API)",
    )
    ap.add_argument(
        "--comp",
        choices=sorted(_COMPS),
        default="wc",
        help="competição: wc (Copa, padrão) ou brasileirao",
    )
    args = ap.parse_args()

    comp = _COMPS[args.comp]
    if args.season is not None:
        comp = dataclasses.replace(comp, season=args.season)

    if args.demo:
        from betstats.data.demo import demo_matchup

        data_a, data_b, matchup, phase = demo_matchup()
        result = run_matchup(
            data_a, data_b, matchup, phase, WorldCupRules(), _use_llm(args.no_llm)
        )
        meta = {"source": "demo", "competition": "wc2026", "llm_backend": config.LLM_BACKEND}
        _emit(result, meta, not args.no_trace, make_video=args.video)
        return 0

    # Modos que dependem da API-Football.
    try:
        provider = _make_provider()
    except Exception as exc:  # APIFootballError e afins
        print(f"[erro] {exc}")
        return 1

    if args.list or args.next_round:
        fixtures = provider.list_fixtures(comp)
        if args.next_round:
            fixtures = [fx for fx in fixtures if not fx.finished]
        for fx in fixtures:
            flag = "✓" if fx.finished else "·"
            print(f"{flag} [{fx.fixture_id}] {fx.round}: {fx.home.name} x {fx.away.name}")
        return 0

    if args.fixture:
        rules = _make_rules(comp, provider)
        result = run_fixture(provider, comp, rules, args.fixture, _use_llm(args.no_llm))
        meta = {
            "source": "fixture",
            "fixture_id": args.fixture,
            "competition": comp.key,
            "season": comp.season,
            "llm_backend": config.LLM_BACKEND,
        }
        _emit(result, meta, not args.no_trace, make_video=args.video)
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
