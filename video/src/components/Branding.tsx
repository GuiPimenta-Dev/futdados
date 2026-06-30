import React from "react";
import { Img, staticFile } from "remotion";

// Sinais de credibilidade (decisão da sessão): selo de fonte+amostra e a LOGO
// Raio X do Jogo como marca d'água. Tudo acima dos 15% de baixo (zona da UI do TikTok).
export const Branding: React.FC<{ source: string; matchup: string }> = ({ source }) => {
  return (
    <>
      {/* selo de fonte + amostra */}
      <div
        style={{
          position: "absolute",
          bottom: 360,
          left: 0,
          right: 0,
          textAlign: "center",
          fontSize: 26,
          fontWeight: 700,
          color: "rgba(255,255,255,0.7)",
        }}
      >
        ⓘ Dados: {source}
      </div>
      {/* logo Raio X do Jogo (marca d'água, horizontal) */}
      <Img
        src={staticFile("logo.png")}
        style={{
          position: "absolute",
          top: 24,
          right: 22,
          width: 240,
          height: 120,
          objectFit: "contain",
          opacity: 0.9,
        }}
      />
    </>
  );
};
