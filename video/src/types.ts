export type WordT = { w: string; startSec: number; endSec: number };
export type BlockT = { startSec: number; endSec: number; words: WordT[] };
export type StatT = { value: string; market: string | null; force: string | null };
export type SegmentT = {
  kind: "hook" | "beat" | "cta";
  text: string;
  startSec: number;
  endSec: number;
  stat: StatT | null;
  blocks: BlockT[];
};
export type TeamT = { name: string; abbr: string; logo: string | null; color: string };
export type SfxEvent = { src: string; atSec: number };
export type Props = {
  matchup: string;
  phase: string;
  title: string;
  teamA: TeamT;
  teamB: TeamT;
  audio: string;
  music?: string | null;
  sfx?: SfxEvent[];
  fps: number;
  durationSec: number;
  source: string;
  segments: SegmentT[];
};
