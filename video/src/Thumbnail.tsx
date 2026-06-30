import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { Props, TeamT } from "./types";
import { Background } from "./components/Background";

// Escudo cru (sem moldura), grande, com sombra + leve glow na cor do time.
// Fallback para a sigla quando não há logo.
const BigCrest: React.FC<{ team: TeamT }> = ({ team }) => (
  <div
    style={{
      width: 360,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: 24,
    }}
  >
    <div
      style={{
        width: 360,
        height: 360,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {team.logo ? (
        <Img
          src={team.logo}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "contain",
            filter: `drop-shadow(0 14px 44px rgba(0,0,0,0.6)) drop-shadow(0 0 38px ${team.color}66)`,
          }}
        />
      ) : (
        <span
          style={{
            fontSize: 150,
            fontWeight: 900,
            color: "#fff",
            letterSpacing: 2,
            textShadow: `0 14px 44px rgba(0,0,0,0.6), 0 0 38px ${team.color}`,
          }}
        >
          {team.abbr}
        </span>
      )}
    </div>
    <div
      style={{
        fontSize: 44,
        fontWeight: 800,
        color: "#fff",
        textAlign: "center",
        lineHeight: 1.05,
        textShadow: "0 4px 18px rgba(0,0,0,0.55)",
      }}
    >
      {team.name}
    </div>
  </div>
);

// Capa estática 1080x1920, conteúdo centralizado (a grade do TikTok corta o
// centro). Escudos crus e grandes no centro, fase no topo, frase-soco como CTA.
export const Thumbnail: React.FC<Props> = (props) => {
  return (
    <AbsoluteFill style={{ fontFamily: "Arial, Helvetica, sans-serif" }}>
      <Background />

      {/* fase / competição — header no topo */}
      <div
        style={{
          position: "absolute",
          top: 120,
          left: 0,
          right: 0,
          textAlign: "center",
          fontSize: 40,
          fontWeight: 700,
          color: "#9fe7bd",
          textTransform: "uppercase",
          letterSpacing: 6,
        }}
      >
        {props.phase}
      </div>

      {/* confronto — escudos crus, grandes, centralizados */}
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          transform: "translateY(-60px)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 48 }}>
          <BigCrest team={props.teamA} />
          <span
            style={{
              fontSize: 110,
              fontWeight: 900,
              color: "rgba(255,255,255,0.85)",
              letterSpacing: 2,
              textShadow: "0 8px 30px rgba(0,0,0,0.6)",
              marginTop: -40,
            }}
          >
            VS
          </span>
          <BigCrest team={props.teamB} />
        </div>
      </AbsoluteFill>

      {/* frase-soco — CTA dinâmico */}
      {props.thumbHook ? (
        <div
          style={{
            position: "absolute",
            bottom: 470,
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

      {/* logo Raio X do Jogo (horizontal) */}
      <Img
        src={staticFile("logo.png")}
        style={{
          position: "absolute",
          bottom: 80,
          left: "50%",
          transform: "translateX(-50%)",
          width: 640,
          height: 330,
          objectFit: "contain",
        }}
      />
    </AbsoluteFill>
  );
};
