import React from "react";
import { Composition, Still } from "remotion";
import { BetVideo } from "./BetVideo";
import { Thumbnail } from "./Thumbnail";
import { Props } from "./types";

const FALLBACK: Props = {
  matchup: "Time A x Time B",
  phase: "Fase",
  title: "",
  teamA: { name: "Time A", abbr: "TMA", logo: null, color: "hsl(140,62%,52%)" },
  teamB: { name: "Time B", abbr: "TMB", logo: null, color: "hsl(35,75%,55%)" },
  audio: "",
  fps: 30,
  durationSec: 55,
  source: "Copa 2026",
  segments: [],
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
    <Composition
      id="BetVideo"
      component={BetVideo}
      durationInFrames={1650}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={FALLBACK}
      calculateMetadata={({ props }) => {
        const fps = props.fps || 30;
        return {
          durationInFrames: Math.max(30, Math.ceil((props.durationSec || 55) * fps)),
          fps,
        };
      }}
    />
    <Still
      id="Thumbnail"
      component={Thumbnail}
      width={1080}
      height={1920}
      defaultProps={FALLBACK}
    />
    </>
  );
};
