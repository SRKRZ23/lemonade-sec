import React from "react";
import { AbsoluteFill, Audio, Easing, Img, Sequence, interpolate, staticFile, useCurrentFrame } from "remotion";
import { GREEN, INK, FONT, DISPLAY_FONT } from "../theme";

export const Scene4Egress: React.FC = () => {
  const frame = useCurrentFrame();
  const scale = interpolate(frame, [0, 195], [1, 1.16], {
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const bigOpacity = interpolate(frame, [180, 220], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const bigScale = interpolate(frame, [180, 220], [0.9, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.back(1.4)),
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#ffffff" }}>
      <Img
        src={staticFile("chart_egress.png")}
        style={{
          position: "absolute",
          left: "50%",
          top: "46%",
          transform: `translate(-50%, -50%) scale(${scale})`,
          maxWidth: 1500,
          maxHeight: 800,
        }}
      />
      <AbsoluteFill
        style={{
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
          gap: 20,
          background: "rgba(255,255,255,0.94)",
          opacity: bigOpacity,
          transform: `scale(${bigScale})`,
        }}
      >
        <div style={{ fontFamily: DISPLAY_FONT, fontSize: 112, fontWeight: 700, color: GREEN, letterSpacing: -2 }}>
          0 BYTES
        </div>
        <div style={{ fontFamily: FONT, fontSize: 52, fontWeight: 700, color: INK }}>
          leave the machine. Private by design.
        </div>
      </AbsoluteFill>

      {/* thump lands the "0 BYTES" reveal — the ad's core privacy claim */}
      <Sequence from={180} durationInFrames={20}>
        <Audio src={staticFile("sfx/thump.wav")} volume={0.7} />
      </Sequence>
    </AbsoluteFill>
  );
};
