import React from "react";
import { AbsoluteFill, Audio, Easing, Sequence, interpolate, staticFile, useCurrentFrame } from "remotion";
import { CameraMotionBlur } from "@remotion/motion-blur";
import { WordCaption, CaptionBar } from "../Caption";
import { RED, MONO } from "../theme";

const EASE = Easing.inOut(Easing.cubic);

export const Scene1Cloud: React.FC = () => {
  const frame = useCurrentFrame();

  // subtle parallax glow drifting slower than the foreground — cheap depth cue
  const glowScale = interpolate(frame, [0, 195], [1, 1.25], { extrapolateRight: "clamp", easing: EASE });
  const glowOpacity = interpolate(frame, [0, 60, 160], [0.15, 0.3, 0.1], { extrapolateRight: "clamp" });

  const flyY = interpolate(frame, [12, 185], [0, -430], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE });
  const flyScale = interpolate(frame, [12, 185], [1, 0.86], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE });
  const flyOpacity = interpolate(frame, [12, 158], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.in(Easing.cubic) });
  const saturate = interpolate(frame, [12, 185], [1, 2.2], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE });
  const hue = interpolate(frame, [12, 185], [0, -40], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE });

  const washOpacity = interpolate(frame, [92, 172], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE });
  const cloudOpacity = interpolate(frame, [98, 152], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const cloudScale = interpolate(frame, [98, 152], [0.7, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.back(1.6)) });
  const barWidth = interpolate(frame, [8, 172], [0, 100], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE });

  return (
    <AbsoluteFill style={{ backgroundColor: "#0c0c0c" }}>
      {/* parallax background glow — slower, deeper layer */}
      <div
        style={{
          position: "absolute",
          inset: -200,
          background: "radial-gradient(circle at 50% 40%, rgba(214,69,69,0.5) 0%, rgba(12,12,12,0) 62%)",
          opacity: glowOpacity,
          transform: `scale(${glowScale})`,
        }}
      />
      <AbsoluteFill
        style={{
          background: "radial-gradient(circle at 50% 35%, rgba(214,69,69,0) 0%, rgba(214,69,69,0.35) 100%)",
          opacity: washOpacity,
        }}
      />
      <div style={{ position: "absolute", top: 90, right: 130, fontSize: 130, opacity: cloudOpacity, transform: `scale(${cloudScale})` }}>
        ☁️
      </div>

      <CameraMotionBlur shutterAngle={110}>
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: "52%",
            transform: `translate(-50%, calc(-50% + ${flyY}px)) scale(${flyScale})`,
            opacity: flyOpacity,
            filter: `saturate(${saturate}) hue-rotate(${hue}deg)`,
            width: 900,
            background: "#111",
            border: "1px solid #333",
            borderRadius: 12,
            padding: "34px 40px",
            fontFamily: MONO,
            fontSize: 26,
            lineHeight: 1.55,
            color: "#7fdb7f",
            boxShadow: "0 30px 80px rgba(0,0,0,0.6)",
          }}
        >
          <div>
            def <span style={{ color: "#666" }}>get_secret</span>():
          </div>
          <div>
            &nbsp;&nbsp;api_key = <span style={{ color: "#666" }}>&quot;sk_live_...&quot;</span>
          </div>
          <div>&nbsp;&nbsp;return db.query(user_input)</div>
          <div style={{ color: "#666" }}># ...entire repository...</div>
          <div style={{ color: "#666" }}># ...uploading to cloud AI...</div>
        </div>
      </CameraMotionBlur>

      <div style={{ position: "absolute", left: 130, right: 130, bottom: 150, height: 16, borderRadius: 8, background: "#222", overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${barWidth}%`, background: `linear-gradient(90deg,#a33,${RED})` }} />
      </div>
      <CaptionBar>
        <WordCaption appearFrame={15} text="Your AI code reviewer just uploaded your codebase to the cloud." />
      </CaptionBar>

      {/* thump lands the "uploaded to the cloud" reveal beat */}
      <Sequence from={140} durationInFrames={20}>
        <Audio src={staticFile("sfx/thump.wav")} volume={0.8} />
      </Sequence>
    </AbsoluteFill>
  );
};
