import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { Props } from "./types";
import { fitSize } from "./fit";
import { Background } from "./components/Background";
import { Crests } from "./components/Crests";

const forceColor = (force: string | null | undefined) => {
  const f = (force || "").toLowerCase();
  if (f.startsWith("fort")) return "#34d27b";
  if (f) return "#f0b73c";
  return "#34d27b";
};

// Capa estática 1080x1920, conteúdo centralizado (a grade do TikTok corta o
// centro). Reusa fundo + escudos (congelados) e crava o número-herói + punch.
export const Thumbnail: React.FC<Props> = (props) => {
  const hero = props.segments.find((s) => s.kind === "hook")?.stat ?? null;
  const accent = props.teamA.color;
  return (
    <AbsoluteFill style={{ fontFamily: "Arial, Helvetica, sans-serif" }}>
      <Background />
      <Crests teamA={props.teamA} teamB={props.teamB} phase={props.phase} frozen top={150} />

      {/* número-herói */}
      {hero ? (
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
          <div style={{ textAlign: "center", width: "92%" }}>
            <div
              style={{
                fontSize: fitSize(hero.value, 300, 4),
                fontWeight: 900,
                color: "#fff",
                lineHeight: 0.9,
                whiteSpace: "nowrap",
                textShadow: `0 0 70px ${accent}`,
              }}
            >
              {hero.value}
            </div>
            {hero.market ? (
              <div
                style={{
                  marginTop: 14,
                  fontSize: fitSize(hero.market, 64, 16),
                  fontWeight: 900,
                  color: forceColor(hero.force),
                  textTransform: "uppercase",
                  letterSpacing: 1,
                  lineHeight: 1.05,
                }}
              >
                {hero.market}
              </div>
            ) : null}
          </div>
        </AbsoluteFill>
      ) : null}

      {/* frase-soco */}
      {props.thumbHook ? (
        <div
          style={{
            position: "absolute",
            bottom: 360,
            left: 60,
            right: 60,
            textAlign: "center",
          }}
        >
          <span
            style={{
              display: "inline-block",
              background: "#34d27b",
              color: "#06150c",
              fontSize: 82,
              fontWeight: 900,
              textTransform: "uppercase",
              letterSpacing: 1,
              padding: "14px 38px",
              borderRadius: 22,
              transform: "rotate(-2deg)",
              boxShadow: "0 14px 44px rgba(0,0,0,0.5)",
            }}
          >
            {props.thumbHook}
          </span>
        </div>
      ) : null}

      {/* logo FutDados */}
      <Img
        src={staticFile("logo.png")}
        style={{
          position: "absolute",
          bottom: 70,
          left: "50%",
          transform: "translateX(-50%)",
          width: 300,
          height: 300,
          objectFit: "contain",
        }}
      />
    </AbsoluteFill>
  );
};
