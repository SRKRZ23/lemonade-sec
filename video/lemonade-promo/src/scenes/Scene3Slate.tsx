import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { AMBER, MONO, FONT } from "../theme";

// This scene is an intentional hand-off SLATE, not filler: it marks exactly where
// Sardor's real terminal screen recording (scan → local-AI triage on Lemonade) gets
// composited in his own edit. 14s window = 0:13–0:27 in the final 60s cut.
export const Scene3Slate: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const pulse = 0.5 + 0.5 * Math.sin(frame / 10);

  return (
    <AbsoluteFill style={{ backgroundColor: "#0c0c0c", alignItems: "center", justifyContent: "center", opacity }}>
      <div
        style={{
          border: `3px solid ${AMBER}`,
          borderRadius: 20,
          padding: "56px 90px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 22,
          background: "rgba(245,167,0,0.06)",
        }}
      >
        <div style={{ fontSize: 60 }}>🎬</div>
        <div style={{ fontFamily: FONT, fontSize: 40, fontWeight: 700, color: "#fff", textAlign: "center" }}>
          Live terminal recording
        </div>
        <div style={{ fontFamily: FONT, fontSize: 24, fontWeight: 600, color: "#aaa", textAlign: "center", maxWidth: 760 }}>
          Lemonade-Sec scanning code and running local AI triage
        </div>
        <div
          style={{
            fontFamily: MONO,
            fontSize: 30,
            fontWeight: 700,
            color: AMBER,
            marginTop: 10,
            opacity: 0.55 + 0.45 * pulse,
          }}
        >
          0:13 — 0:27 · 14s
        </div>
      </div>
    </AbsoluteFill>
  );
};
