import React from "react";
import { Easing, interpolate, useCurrentFrame } from "remotion";

export const CountUp: React.FC<{
  from?: number;
  to: number;
  startFrame: number;
  durationFrames: number;
  decimals?: number;
  suffix?: string;
  style?: React.CSSProperties;
}> = ({ from = 0, to, startFrame, durationFrames, decimals = 0, suffix = "", style }) => {
  const frame = useCurrentFrame();
  const raw = interpolate(frame, [startFrame, startFrame + durationFrames], [from, to], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const text = raw.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  return <span style={style}>{text}{suffix}</span>;
};
