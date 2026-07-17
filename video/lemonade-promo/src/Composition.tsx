import { Composition } from "remotion";
import { LemonadePromo } from "./LemonadePromo";

export const MyComposition = () => {
  return (
    <Composition
      id="LemonadeSecPromo"
      component={LemonadePromo}
      durationInFrames={1800}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
