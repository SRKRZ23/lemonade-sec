import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { AMBER, INK, FONT } from "./theme";

export const Caption: React.FC<{
  appearFrame: number;
  children: React.ReactNode;
  sub?: boolean;
}> = ({ appearFrame, children, sub }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const local = frame - appearFrame;
  if (local < 0) return null;
  const p = spring({ frame: local, fps, config: { damping: 200, mass: 0.6 } });
  const translateY = interpolate(p, [0, 1], [18, 0]);
  const opacity = interpolate(p, [0, 1], [0, 1]);
  return (
    <div
      style={{
        opacity,
        transform: `translateY(${translateY}px)`,
        display: "inline-block",
        background: sub ? AMBER : "rgba(10,10,10,0.86)",
        color: sub ? INK : "#fff",
        fontFamily: FONT,
        fontSize: sub ? 30 : 44,
        fontWeight: 700,
        lineHeight: 1.3,
        padding: "14px 34px",
        borderRadius: 14,
        marginTop: sub ? 12 : 0,
      }}
    >
      {children}
    </div>
  );
};

// Karaoke-style word-by-word reveal — used on the hook scenes (1,2) where grabbing
// attention matters most; data/CTA scenes keep the calmer single-block Caption above
// so proof-point text stays settled and easy to read rather than busy.
export const WordCaption: React.FC<{
  appearFrame: number;
  text: string;
  wordFrames?: number; // frames between each word popping in
}> = ({ appearFrame, text, wordFrames = 4 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = text.split(" ");
  const local = frame - appearFrame;
  if (local < 0) return null;
  return (
    <div
      style={{
        display: "inline-block",
        background: "rgba(10,10,10,0.86)",
        color: "#fff",
        fontFamily: FONT,
        fontSize: 44,
        fontWeight: 700,
        lineHeight: 1.3,
        padding: "14px 34px",
        borderRadius: 14,
      }}
    >
      {words.map((w, i) => {
        const wLocal = local - i * wordFrames;
        if (wLocal < 0) return null;
        const p = spring({ frame: wLocal, fps, config: { damping: 14, mass: 0.4 } });
        const translateY = interpolate(p, [0, 1], [10, 0]);
        const opacity = interpolate(p, [0, 1], [0, 1]);
        return (
          <span
            key={i}
            style={{ display: "inline-block", opacity, transform: `translateY(${translateY}px)`, marginRight: 12 }}
          >
            {w}
          </span>
        );
      })}
    </div>
  );
};

export const CaptionBar: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div
    style={{
      position: "absolute",
      left: 0,
      right: 0,
      bottom: 70,
      textAlign: "center",
      padding: "0 120px",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      zIndex: 50,
    }}
  >
    {children}
  </div>
);
