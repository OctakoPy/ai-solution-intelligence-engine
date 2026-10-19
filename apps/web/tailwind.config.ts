import type { Config } from "tailwindcss";

/**
 * Colour tokens — dark theme, brand-blue surfaces.
 *
 * Brand: NTT Blue `#0072BC` (PANTONE 285C). NTT DATA unified their corporate
 * logo colour to the NTT Group colour on 1 July 2023, so this is their
 * wordmark colour, not an approximation of it.
 *
 * The page background is `#002E4B`, the deepest step of the brand ramp, so the
 * whole application reads as brand blue rather than as a generic dark theme.
 * The sidebar goes one step darker again so the two do not merge, and cards
 * sit lighter than the page so they read as raised.
 *
 * Every palette is defined in full. `theme.extend` merges with Tailwind's
 * defaults, so a partially-defined palette silently leaves stock Tailwind
 * shades available at the call site — which is how a quarter of the colour
 * usages in this app were unaffected by the previous palette.
 *
 * Step numbers keep their *role* rather than their lightness, which is what
 * let this theme be built without editing 240 call sites: the grey ramp is
 * inverted, so `text-gray-900` is now near-white body text and `bg-gray-50`
 * is the page, from the same class names.
 *
 * Within a family:
 *   50–100  surface fills: tints, chat bubbles, banner backgrounds
 *   200–300 borders, and the raised inset surface used inside a card
 *   400–500 solid fills: dots, bars, chart series
 *   600–900 text, all clearing WCAG AA (>= 4.5:1) on both the page and a card
 *
 * An inset panel inside a card must be *lighter* than the card, never the page
 * colour: `bg-gray-50` is the page, so on a card it reads as a hole punched in
 * the surface at 1.19:1 rather than as a raised chip. `bg-gray-200` is that
 * inset step, and every text tone on it still clears AA (gray-500 is 5.26:1).
 *
 * The text/fill split is load-bearing. `gray-800` is a *fill* — the sidebar
 * hover — and `text-gray-800` on the page is 1.25:1, darker than its own
 * background. Fill and border tones are never used as text; the brand-tokens
 * test enforces that.
 *
 * The one deliberate exception is the blue family. Its 500–900 steps are the
 * brand's dark end and are used as *fills* carrying white text — a primary
 * button at 5.08:1 — not as text. Where blue is needed as text it uses 300,
 * because brand blue on a navy card is only 2.33:1 and unreadable.
 *
 * Semantic hues stay clear of the brand. Measured hue angles: brand 204,
 * success 151, warning 36, danger 0, so brand blue never reads as a status.
 * The tight pair is warning to danger at 36 degrees, which is why warning
 * always ships with a tint and an icon as well as the colour.
 */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Surfaces and text. Inverted from the light theme so that the
        // existing class names keep meaning the same thing.
        gray: {
          50: "#002E4B", // page background
          100: "#0A3A5C", // card / raised surface
          200: "#14496B", // border, raised inset surface
          300: "#1D5C85", // border, emphasis
          400: "#93B2C8", // faint text
          500: "#A8C4D8", // muted text (the most-used token in the app)
          600: "#C4D9E8", // secondary text
          700: "#D2E3EF", // strong secondary text
          800: "#123E5D", // sidebar hover fill — a FILL, never text
          900: "#F2F8FC", // body text
        },
        // NTT Blue. 600 is the brand colour and is a *fill*: white text on it
        // is 5.08:1. Text uses 300 (5.35:1 on a card).
        blue: {
          50: "#14557F", // user bubble / hover surface
          100: "#1A5A85", // raised tint
          200: "#2A6E9C", // border
          300: "#7AB5DE", // accent text, focus border
          400: "#57A2D3", // bar gradient end, ring
          500: "#2486C5", // spinner
          600: "#0072BC", // BRAND: primary buttons, active states
          700: "#005B96",
          800: "#004471",
          900: "#002E4B",
        },
        // The dark chrome. The sidebar is deeper than the page background.
        navy: {
          600: "#0072BC",
          700: "#0E4C72", // active nav item
          800: "#0A3A5C",
          900: "#001F35", // sidebar
        },
        // Success.
        green: {
          50: "#0E3A2A",
          100: "#144D38",
          200: "#2F8F63",
          300: "#4AD98E", // border
          400: "#2FB86E", // dot, bar
          500: "#35C47A",
          600: "#4AD98E", // 6.55:1
          700: "#6EE0A8",
          800: "#8FE9BE",
          900: "#B0F2D1",
        },
        // Warning. This carries the abstain / guardrail banner.
        amber: {
          50: "#3D2E0C",
          100: "#4A3A10",
          200: "#8A6A1E",
          300: "#C99A2E", // border
          400: "#F0B429", // dot, bar
          500: "#F0B429", // 6.36:1
          600: "#F6C44E",
          700: "#FFD066",
          800: "#FFE09A",
          900: "#FFF0C7",
        },
        // Danger.
        red: {
          50: "#3D1414",
          100: "#4E1B1B",
          200: "#7A2E2E",
          300: "#C05B5B", // border
          400: "#F87171", // dot, bar
          500: "#FC8A8A", // 5.16:1
          600: "#FCA5A5",
          700: "#FFC4C4",
          800: "#FFDCDC",
          900: "#FFEBEB",
        },
      },
      fontFamily: {
        // Noto Sans is what nttdata.com loads. The system stack stays behind
        // it so the app still renders correctly offline or in the packaged
        // wheel, where nothing fetches from a CDN.
        sans: [
          "Noto Sans",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Helvetica",
          "Arial",
          "sans-serif",
        ],
      },
      fontSize: {
        metric: ["28px", { lineHeight: "1.1", fontWeight: "700" }],
        "card-title": ["15px", { lineHeight: "1.2", fontWeight: "600" }],
        body: ["13px", { lineHeight: "1.5", fontWeight: "400" }],
        meta: ["12px", { lineHeight: "1.4", fontWeight: "400" }],
        label: ["11px", { lineHeight: "1.4", fontWeight: "600" }],
      },
      boxShadow: {
        // A dark surface needs a shadow that reads as depth rather than as a
        // grey haze, so this is a black shadow plus a faint brand rim.
        card: "0 1px 2px rgba(0,0,0,0.35), inset 0 1px 0 rgba(122,181,222,0.06)",
      },
      keyframes: {
        blink: { "50%": { opacity: "0" } },
        pulse: {
          "0%": { transform: "scale(1)" },
          "50%": { transform: "scale(1.15)" },
          "100%": { transform: "scale(1)" },
        },
        dots: { "50%": { opacity: ".2" } },
      },
      animation: {
        blink: "blink 1s steps(1) infinite",
        pulse: "pulse 200ms ease-out",
        dots: "dots 1s infinite",
      },
    },
  },
  plugins: [],
} satisfies Config;
