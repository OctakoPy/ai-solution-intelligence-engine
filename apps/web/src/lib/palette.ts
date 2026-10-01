/**
 * The colours charts cannot express as Tailwind classes.
 *
 * `stroke` on an SVG circle and the donut's inner mask are attributes, not
 * classes, so they need real colour values. They used to be inline hex in
 * `Overview.tsx`, which is how the app ended up with three unrelated ambers:
 * `#FDB84E` in the Tailwind config and `#F5A623` in a chart, differing only
 * enough to look like a mistake.
 *
 * Every value here mirrors a shade in `tailwind.config.ts`. Chart series use
 * the fill step of each ramp, because a chart segment is a graphic and
 * contrast against the card surface is not the constraint - text contrast is
 * handled by the 600+ shades.
 *
 * `tests/unit`-style drift is guarded by `brand-tokens.test.ts`, which asserts
 * these constants still equal the Tailwind config values.
 */

/** Card surface the donut's inner mask has to match. */
export const SURFACE = "#FFFFFF";

export const CHART = {
  /** Success fill, `green-500`. */
  success: "#35A874",
  /** Danger fill, `red-500`. */
  danger: "#C42B2B",
  /** Brand fill, `blue-600` - NTT Blue. */
  brand: "#0072BC",
  /**
   * Warning fill, `amber-400`. Deliberately the light step rather than
   * `amber-500`, which is now the text shade and reads as brown at segment
   * size. It also keeps review visually distinct from danger: the two hues
   * are only 36 degrees apart, so lightness is doing the separating here.
   */
  warning: "#E8A33A",
} as const;
