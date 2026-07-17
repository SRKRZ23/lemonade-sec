import React from "react";
import { AbsoluteFill, Audio, Easing, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Caption, CaptionBar } from "../Caption";
import { CountUp } from "../CountUp";
import { AMBER, INK, G2, DISPLAY_FONT, FONT } from "../theme";

const COUNT_START = 40;
const COUNT_DUR = 55;

export const Scene5MI300X: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = interpolate(frame, [0, 315], [1, 1.1], {
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });

  const badgeLocal = frame - COUNT_START;
  const badgeP = badgeLocal < 0 ? 0 : spring({ frame: badgeLocal, fps, config: { damping: 200 } });

  return (
    <AbsoluteFill style={{ backgroundColor: "#ffffff" }}>
      <Img
        src={staticFile("chart_mi300x.png")}
        style={{
          position: "absolute",
          left: "50%",
          top: "44%",
          transform: `translate(-50%, -50%) scale(${scale})`,
          maxWidth: 1600,
          maxHeight: 760,
        }}
      />

      {/* hero-number badge: the single biggest measured claim gets its own reveal */}
      <div
        style={{
          position: "absolute",
          top: 100,
          right: 110,
          opacity: badgeP,
          transform: `translateY(${interpolate(badgeP, [0, 1], [-16, 0])}px) scale(${0.92 + 0.08 * badgeP})`,
          background: "#fff",
          border: `3px solid ${AMBER}`,
          borderRadius: 18,
          padding: "18px 30px",
          textAlign: "center",
          boxShadow: "0 20px 50px rgba(0,0,0,0.12)",
        }}
      >
        <div style={{ fontFamily: DISPLAY_FONT, fontSize: 64, fontWeight: 700, color: INK, letterSpacing: -1 }}>
          <CountUp from={0} to={64.3} decimals={1} startFrame={COUNT_START} durationFrames={COUNT_DUR} />
        </div>
        <div style={{ fontFamily: FONT, fontSize: 20, fontWeight: 600, color: G2, marginTop: 2 }}>tok/s · MI300X</div>
      </div>

      <CaptionBar>
        <Caption appearFrame={6}>Measured on a real AMD Instinct MI300X.</Caption>
      </CaptionBar>

      {/* ding lands exactly when the count-up settles on its final value */}
      <Sequence from={COUNT_START + COUNT_DUR} durationInFrames={15}>
        <Audio src={staticFile("sfx/ding.wav")} volume={0.55} />
      </Sequence>
    </AbsoluteFill>
  );
};
