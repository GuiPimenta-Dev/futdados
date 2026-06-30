import React from "react";
import { Sequence, useCurrentFrame, useVideoConfig } from "remotion";
import { BlockT, SegmentT } from "../types";

// Bloco de frase com a palavra ativa acesa (decisão de tom). O número fica
// legível o bloco inteiro; a palavra falada cresce + muda de cor.
const CaptionBlock: React.FC<{ block: BlockT }> = ({ block }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = block.startSec + frame / fps; // tempo absoluto aproximado
  return (
    <div
      style={{
        position: "absolute",
        bottom: 470,
        left: 70,
        right: 70,
        textAlign: "center",
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        gap: "14px 18px",
      }}
    >
      {block.words.map((word, i) => {
        const active = t >= word.startSec - 0.02 && t <= word.endSec + 0.06;
        return (
          <span
            key={i}
            style={{
              fontSize: 70,
              fontWeight: 900,
              lineHeight: 1.1,
              color: active ? "#16140a" : "#ffffff",
              background: active ? "#34d27b" : "transparent",
              padding: active ? "2px 16px" : "2px 4px",
              borderRadius: 14,
              transform: active ? "scale(1.06)" : "scale(1)",
              transition: "transform 0.05s",
              textShadow: active ? "none" : "0 4px 18px rgba(0,0,0,0.6)",
              textTransform: "uppercase",
            }}
          >
            {word.w}
          </span>
        );
      })}
    </div>
  );
};

export const Captions: React.FC<{ segments: SegmentT[] }> = ({ segments }) => {
  const { fps } = useVideoConfig();
  const blocks = segments.flatMap((s) => s.blocks);
  return (
    <>
      {blocks.map((b, i) => {
        const from = Math.round(b.startSec * fps);
        const dur = Math.max(1, Math.round((b.endSec - b.startSec) * fps) + 4);
        return (
          <Sequence key={i} from={from} durationInFrames={dur}>
            <CaptionBlock block={b} />
          </Sequence>
        );
      })}
    </>
  );
};
