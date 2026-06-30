import React from "react";
import { Img, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { TeamT } from "../types";

const Badge: React.FC<{ team: TeamT; delay: number; frozen?: boolean }> = ({
  team,
  delay,
  frozen,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = frozen ? 1 : spring({ frame: frame - delay, fps, config: { damping: 14, mass: 0.6 } });
  const size = 190;
  return (
    <div style={{ textAlign: "center", transform: `scale(${p})`, opacity: p }}>
      <div
        style={{
          width: size,
          height: size,
          borderRadius: "50%",
          background: "rgba(255,255,255,0.08)",
          border: `4px solid ${team.color}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          overflow: "hidden",
          boxShadow: "0 12px 40px rgba(0,0,0,0.45)",
        }}
      >
        {team.logo ? (
          <Img src={team.logo} style={{ width: "78%", height: "78%", objectFit: "contain" }} />
        ) : (
          <span style={{ fontSize: 64, fontWeight: 900, color: "#fff", letterSpacing: 1 }}>
            {team.abbr}
          </span>
        )}
      </div>
      <div style={{ marginTop: 16, fontSize: 34, fontWeight: 800, color: "#fff" }}>
        {team.name}
      </div>
    </div>
  );
};

export const Crests: React.FC<{
  teamA: TeamT;
  teamB: TeamT;
  phase: string;
  frozen?: boolean;
  top?: number;
}> = ({ teamA, teamB, phase, frozen, top = 120 }) => {
  return (
    <div
      style={{
        position: "absolute",
        top,
        left: 0,
        right: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 18,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 56 }}>
        <Badge team={teamA} delay={0} frozen={frozen} />
        <span style={{ fontSize: 56, fontWeight: 900, color: "rgba(255,255,255,0.65)" }}>×</span>
        <Badge team={teamB} delay={6} frozen={frozen} />
      </div>
      <div
        style={{
          marginTop: 6,
          fontSize: 28,
          fontWeight: 700,
          color: "#9fe7bd",
          textTransform: "uppercase",
          letterSpacing: 3,
        }}
      >
        {phase}
      </div>
    </div>
  );
};
