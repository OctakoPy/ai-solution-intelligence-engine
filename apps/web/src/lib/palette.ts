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
 * `brand-tokens.test.ts` asserts these constants still equal the Tailwind
 * config values, and that they clear 3:1 against SURFACE.
 */

/**
 * Card surface the donut's inner mask has to match.
 *
 * This is the one hardcoded value in the theme that has no token: it is the
 * surface the chart is painted on, and a mismatch shows as a visible disc.
 */
export const SURFACE = "#0A3A5C";

export const CHART = {
  /** Success series, `green-400`. */
  success: "#2FB86E",
  /** Danger series, `red-500` - the light text step, legible as a ring. */
  danger: "#FC8A8A",
  /**
   * Brand series. Not `#0072BC`: that is the button fill and it sits at
   * 1.7:1 on the card, so a donut drawn in it would be nearly invisible.
   * This is a lifted brand blue at 4.55:1.
   */
  brand: "#5FA8D6",
  /**
   * Warning series, `amber-400`. Deliberately distinct from danger: the two
   * hues are only 36 degrees apart, so lightness is doing the separating.
   */
  warning: "#F0B429",
} as const;