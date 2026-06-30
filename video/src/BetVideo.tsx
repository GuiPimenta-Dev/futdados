import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import { Props } from "./types";
import { Background } from "./components/Background";
import { Crests } from "./components/Crests";
import { Captions } from "./components/Captions";
import { StatCards } from "./components/StatCard";
import { Branding } from "./components/Branding";

export const BetVideo: React.FC<Props> = (props) => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ fontFamily: "Arial, Helvetica, sans-serif" }}>
      <Background />

      {/* trilhas de áudio: VO na frente, bed grave em loop bem baixo, SFX */}
      {props.audio ? <Audio src={staticFile(props.audio)} /> : null}
      {props.music ? <Audio src={staticFile(props.music)} loop volume={0.14} /> : null}
      {(props.sfx ?? []).map((e, i) => (
        <Sequence key={i} from={Math.round(e.atSec * fps)} durationInFrames={Math.round(fps)}>
          <Audio src={staticFile(e.src)} volume={0.5} />
        </Sequence>
      ))}

      <Crests teamA={props.teamA} teamB={props.teamB} phase={props.phase} />
      <StatCards segments={props.segments} accent={props.teamA.color} />
      <Captions segments={props.segments} />
      <Branding source={props.source} matchup={props.matchup} />
    </AbsoluteFill>
  );
};
