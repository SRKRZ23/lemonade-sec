import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { AMBER, INK, FONT } from "../theme";

const BULLETS = [
  { text: "35 rules", delay: 30 },
  { text: "web2 + web3", delay: 72 },
  { text: "OpenAI-compatible", delay: 114 },
  { text: "MIT open source", delay: 156 },
];

export const Scene6Coverage: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = interpolate(frame, [0, 255], [1, 1.08], {
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const rotate = interpolate(frame, [0, 255], [0, 6], {
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#ffffff" }}>
      <Img
        src={staticFile("chart_coverage.png")}
        style={{
          position: "absolute",
          left: "30%",
          top: "50%",
          transform: `translate(-50%, -50%) scale(${scale}) rotate(${rotate}deg)`,
          maxWidth: 820,
        }}
      />
      <div
        style={{
          position: "absolute",
          right: 150,
          top: "50%",
          transform: "translateY(-50%)",
          display: "flex",
          flexDirection: "column",
          gap: 26,
          width: 640,
        }}
      >
        {BULLETS.map((b) => {
          const local = frame - b.delay;
          const p = local < 0 ? 0 : spring({ frame: local, fps, config: { damping: 200 } });
          return (
            <div
              key={b.text}
              style={{
                opacity: p,
                transform: `translateX(${interpolate(p, [0, 1], [30, 0])}px)`,
                fontFamily: FONT,
                fontSize: 44,
                fontWeight: 700,
                color: INK,
                display: "flex",
                alignItems: "center",
                gap: 18,
              }}
            >
              <span style={{ width: 16, height: 16, borderRadius: 8, background: AMBER, flex: "0 0 auto" }} />
              {b.text}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
