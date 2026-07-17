import React from "react";
import { AbsoluteFill, Audio, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { WordCaption, CaptionBar } from "../Caption";
import { TINT, INK, FONT } from "../theme";

const CARDS = [
  { icon: "🏦", label: "Banks", delay: 6 },
  { icon: "🛡️", label: "Defense", delay: 15 },
  { icon: "🏥", label: "Healthcare", delay: 24 },
  { icon: "🔒", label: "Air-gapped", delay: 33 },
];

export const Scene2Cards: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#ffffff" }}>
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gridTemplateRows: "1fr 1fr",
          gap: 40,
          padding: "170px 260px 220px",
        }}
      >
        {CARDS.map((c) => {
          const local = frame - c.delay;
          const p = local < 0 ? 0 : spring({ frame: local, fps, config: { damping: 12, mass: 0.5 } });
          const scale = 0.85 + 0.15 * p;
          return (
            <div
              key={c.label}
              style={{
                background: TINT,
                border: "2px solid #f2dfae",
                borderRadius: 22,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: 18,
                opacity: p,
                transform: `scale(${scale})`,
              }}
            >
              <div style={{ fontSize: 74 }}>{c.icon}</div>
              <div style={{ fontSize: 38, fontWeight: 700, color: INK, fontFamily: FONT }}>{c.label}</div>
            </div>
          );
        })}
      </div>
      <CaptionBar>
        <WordCaption appearFrame={6} text="For regulated, air-gapped, or confidential code — that's a non-starter." />
      </CaptionBar>

      {/* soft ding marks the 4th/last card landing — rhythm completion, not 4 separate dings */}
      <Sequence from={33} durationInFrames={15}>
        <Audio src={staticFile("sfx/ding.wav")} volume={0.5} />
      </Sequence>
    </AbsoluteFill>
  );
};
