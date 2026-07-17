import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { TransitionSeries, linearTiming, springTiming } from "@remotion/transitions";
import { slide } from "@remotion/transitions/slide";
import { fade } from "@remotion/transitions/fade";
import { Scene1Cloud } from "./scenes/Scene1Cloud";
import { Scene2Cards } from "./scenes/Scene2Cards";
import { Scene3Slate } from "./scenes/Scene3Slate";
import { Scene4Egress } from "./scenes/Scene4Egress";
import { Scene5MI300X } from "./scenes/Scene5MI300X";
import { Scene6Coverage } from "./scenes/Scene6Coverage";
import { Scene7Outro } from "./scenes/Scene7Outro";
import { AMBER } from "./theme";

// 30fps · 1800 frames = exactly 60s.
// Each transition "eats" 15 frames of overlap from its two neighbors, so every
// scene's coded duration below is padded +15 per adjacent transition it touches —
// the math is precise (not eyeballed) so the FINAL cut still lands on exactly 60s:
//   195 + 225 + 435 + 285 + 315 + 255 + 180 = 1890, minus 6 transitions × 15 = 1800. ✓
const T = 15;
const SLIDE = springTiming({ durationInFrames: T, config: { damping: 200 } });
const FADE = linearTiming({ durationInFrames: T });

// Transition-cut whooshes, at the exact global frame each transition begins (audio
// leads the visual cut by 5 frames — anticipation). Speed matches transition energy:
// fast/sharp for snappy slides, slow/broad for the gentler fades — per sound-design
// principle "match whoosh speed to transition timing and narrative intent."
const CUTS: { frame: number; fast: boolean }[] = [
  { frame: 180, fast: true }, // 1→2 slide
  { frame: 390, fast: false }, // 2→3 fade
  { frame: 810, fast: false }, // 3→4 fade
  { frame: 1080, fast: true }, // 4→5 slide
  { frame: 1380, fast: true }, // 5→6 slide
  { frame: 1620, fast: false }, // 6→7 fade
];

export const LemonadePromo: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const progress = (frame / durationInFrames) * 100;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={195} name="1. Cloud upload">
          <Scene1Cloud />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition presentation={slide({ direction: "from-right" })} timing={SLIDE} />

        <TransitionSeries.Sequence durationInFrames={225} name="2. Who can't use cloud AI">
          <Scene2Cards />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition presentation={fade()} timing={FADE} />

        <TransitionSeries.Sequence durationInFrames={435} name="3. SLATE — terminal recording goes here">
          <Scene3Slate />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition presentation={fade()} timing={FADE} />

        <TransitionSeries.Sequence durationInFrames={285} name="4. Zero-egress">
          <Scene4Egress />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition presentation={slide({ direction: "from-right" })} timing={SLIDE} />

        <TransitionSeries.Sequence durationInFrames={315} name="5. MI300X measured">
          <Scene5MI300X />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition presentation={slide({ direction: "from-right" })} timing={SLIDE} />

        <TransitionSeries.Sequence durationInFrames={255} name="6. Coverage">
          <Scene6Coverage />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition presentation={fade()} timing={FADE} />

        <TransitionSeries.Sequence durationInFrames={180} name="7. Outro">
          <Scene7Outro />
        </TransitionSeries.Sequence>
      </TransitionSeries>

      <div style={{ position: "absolute", left: 0, bottom: 0, height: 8, width: `${progress}%`, background: AMBER, zIndex: 200 }} />

      {CUTS.map((c) => (
        <Sequence key={c.frame} from={Math.max(0, c.frame - 5)} durationInFrames={30}>
          <Audio src={staticFile(c.fast ? "sfx/whoosh_fast.wav" : "sfx/whoosh_slow.wav")} volume={c.fast ? 0.8 : 1.1} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
