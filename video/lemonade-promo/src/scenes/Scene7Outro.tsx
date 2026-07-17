import React from "react";
import { AbsoluteFill, Audio, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { AMBER, INK, G2, TINT, FONT, DISPLAY_FONT } from "../theme";

const pop = (frame: number, delay: number, fps: number) => {
  const local = frame - delay;
  if (local < 0) return { opacity: 0, translateY: 20 };
  const p = spring({ frame: local, fps, config: { damping: 200 } });
  return { opacity: interpolate(p, [0, 1], [0, 1]), translateY: interpolate(p, [0, 1], [20, 0]) };
};

export const Scene7Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const logo = pop(frame, 9, fps);
  const tag = pop(frame, 30, fps);
  const url = pop(frame, 48, fps);
  const sub = pop(frame, 63, fps);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: TINT,
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 26,
      }}
    >
      <div style={{ fontSize: 150, opacity: logo.opacity, transform: `translateY(${logo.translateY}px) scale(${0.7 + 0.3 * (1 - logo.translateY / 20)})` }}>
        🍋🔒
      </div>
      <div
        style={{
          fontFamily: DISPLAY_FONT,
          fontSize: 56,
          fontWeight: 700,
          color: INK,
          textAlign: "center",
          maxWidth: 1400,
          letterSpacing: -1,
          opacity: tag.opacity,
          transform: `translateY(${tag.translateY}px)`,
        }}
      >
        AI security review that never sees the cloud.
      </div>
      <div
        style={{
          fontFamily: FONT,
          fontSize: 40,
          fontWeight: 700,
          color: AMBER,
          opacity: url.opacity,
          transform: `translateY(${url.translateY}px)`,
        }}
      >
        github.com/SRKRZ23/lemonade-sec
      </div>
      <div
        style={{
          fontFamily: FONT,
          fontSize: 26,
          fontWeight: 700,
          color: G2,
          opacity: sub.opacity,
          transform: `translateY(${sub.translateY}px)`,
        }}
      >
        Built for the AMD Lemonade Developer Challenge
      </div>

      {/* thump lands the brand pop — the final beat */}
      <Sequence from={9} durationInFrames={20}>
        <Audio src={staticFile("sfx/thump.wav")} volume={0.65} />
      </Sequence>
    </AbsoluteFill>
  );
};
