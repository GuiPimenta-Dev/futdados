import React from "react";
import {
  AbsoluteFill,
  interpolate,
  Sequence,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { SegmentT, StatT } from "../types";
import { fitSize } from "../fit";

const forceStyle = (force: string | null) => {
  const f = (force || "").toLowerCase();
  if (f.startsWith("fort")) return { label: "● SINAL FORTE", color: "#34d27b" };
  if (f) return { label: "◐ TENDÊNCIA LEVE", color: "#f0b73c" };
  return null;
};

// Gancho (0-3s): SLAM. Número gigante que soca a tela com overshoot + flash
// branco no impacto. É o stop-scroll (decisão Q6).
const HeroSlam: React.FC<{ stat: StatT; accent: string }> = ({ stat, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame, fps, config: { damping: 9, mass: 0.7, stiffness: 180 } });
  const scale = interpolate(pop, [0, 1], [1.5, 1]); // entra grande e assenta
  const flash = interpolate(frame, [0, 6], [0.55, 0], { extrapolateRight: "clamp" });
  const fs = forceStyle(stat.force);
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <AbsoluteFill style={{ background: "#ffffff", opacity: flash }} />
      <div
        style={{
          textAlign: "center",
          width: "92%",
          transform: `scale(${scale})`,
          opacity: pop,
        }}
      >
        <div
          style={{
            fontSize: fitSize(stat.value, 280, 4),
            fontWeight: 900,
            color: "#fff",
            lineHeight: 0.9,
            whiteSpace: "nowrap",
            textShadow: `0 0 60px ${accent}`,
          }}
        >
          {stat.value}
        </div>
        {stat.market ? (
          <div
            style={{
              marginTop: 12,
              fontSize: fitSize(stat.market, 58, 16),
              fontWeight: 900,
              color: accent,
              textTransform: "uppercase",
              letterSpacing: 1,
              lineHeight: 1.05,
            }}
          >
            {stat.market}
          </div>
        ) : null}
        {fs ? (
          <div style={{ marginTop: 18, fontSize: 36, fontWeight: 800, color: fs.color }}>
            {fs.label}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

const Card: React.FC<{ stat: StatT; accent: string }> = ({ stat, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame, fps, config: { damping: 13, mass: 0.5 } });
  const fs = forceStyle(stat.force);
  return (
    <div
      style={{
        position: "absolute",
        top: 760,
        left: 80,
        right: 80,
        transform: `scale(${0.86 + 0.14 * p})`,
        opacity: p,
        background: "rgba(2, 18, 10, 0.72)",
        border: `3px solid ${accent}`,
        borderRadius: 36,
        padding: "44px 40px",
        textAlign: "center",
        boxShadow: "0 18px 60px rgba(0,0,0,0.5)",
      }}
    >
      <div
        style={{
          fontSize: fitSize(stat.value, 132, 7),
          fontWeight: 900,
          color: "#fff",
          lineHeight: 1,
          whiteSpace: "nowrap",
        }}
      >
        {stat.value}
      </div>
      {stat.market ? (
        <div
          style={{
            marginTop: 18,
            fontSize: fitSize(stat.market, 46, 20),
            fontWeight: 800,
            color: "#d6ffe6",
            textTransform: "uppercase",
            letterSpacing: 1,
            lineHeight: 1.05,
          }}
        >
          {stat.market}
        </div>
      ) : null}
      {fs ? (
        <div style={{ marginTop: 22, fontSize: 32, fontWeight: 800, color: fs.color }}>
          {fs.label}
        </div>
      ) : null}
    </div>
  );
};

export const StatCards: React.FC<{ segments: SegmentT[]; accent: string }> = ({
  segments,
  accent,
}) => {
  const { fps } = useVideoConfig();
  return (
    <>
      {segments.map((s, i) => {
        if (!s.stat) return null;
        const from = Math.round(s.startSec * fps);
        const dur = Math.max(1, Math.round((s.endSec - s.startSec) * fps));
        return (
          <Sequence key={i} from={from} durationInFrames={dur}>
            {s.kind === "hook" ? (
              <HeroSlam stat={s.stat} accent={accent} />
            ) : (
              <Card stat={s.stat} accent={accent} />
            )}
          </Sequence>
        );
      })}
    </>
  );
};
