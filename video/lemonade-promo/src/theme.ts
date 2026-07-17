import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadSpaceGrotesk } from "@remotion/google-fonts/SpaceGrotesk";

export const AMBER = "#F5A700";
export const INK = "#0A0A0A";
export const GREEN = "#1a9e5a";
export const RED = "#d64545";
export const TINT = "#fff6e0";
export const PAPER = "#ffffff";
export const G1 = "#3a3a3a";
export const G2 = "#6a6a6a";
export const MONO = "ui-monospace, Menlo, Consolas, monospace";

// Professional typography: Inter for UI/body (workhorse legibility), Space Grotesk
// for hero numbers/headlines (a little more character, still clean/geometric).
const inter = loadInter("normal", { weights: ["500", "600", "700"] });
const spaceGrotesk = loadSpaceGrotesk("normal", { weights: ["500", "700"] });

export const FONT = inter.fontFamily;
export const DISPLAY_FONT = spaceGrotesk.fontFamily;
