import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";

// Fundo verde brandado: gradiente escuro->verde + brilho radial sutil que
// respira de leve. Sem footage (zero direitos), identidade consistente.
export const Background: React.FC = () => {
  const frame = useCurrentFrame();
  const pulse = 0.32 + 0.06 * Math.sin(frame / 40);
  return (
    <AbsoluteFill
      style={{
        background:
          "linear-gradient(160deg, #04130a 0%, #0a2a17 45%, #0f3d22 100%)",
      }}
    >
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 26%, rgba(34,160,84,${pulse}), transparent 56%)`,
        }}
      />
      {/* linhas sutis de gramado */}
      <AbsoluteFill
        style={{
          opacity: 0.06,
          backgroundImage:
            "repeating-linear-gradient(180deg, #ffffff 0 2px, transparent 2px 140px)",
        }}
      />
    </AbsoluteFill>
  );
};
