import type { Config } from "tailwindcss";

/**
 * Colour tokens.
 *
 * Brand: NTT Blue `#0072BC` (PANTONE 285C). NTT DATA unified its corporate
 * logo colour to the NTT Group colour on 1 July 2023, so this is their
 * wordmark colour, not an approximation of it.
 *
 * Every palette is defined in full. `theme.extend` merges with Tailwind's
 * defaults, so a partially-defined palette silently leaves stock Tailwind
 * shades available at the call site - which is how a quarter of the colour
 * usages in this app were unaffected by the previous palette.
 *
 * Shades 600 and darker are the text range and clear WCAG AA (>= 4.5:1) on
 * white. Shades 400 and lighter are fills, chart series, dots and progress
 * bars, where contrast is not the constraint. The old palette used one
 * shade for both jobs, so status text failed AA: amber was 1.73:1, green
 * 3.95:1, red 3.91:1.
 *
 * Semantic hues are held apart from the brand deliberately. Measured hue
 * angles: brand 204, success 151, warning 36, danger 0. The brand is 53
 * degrees from green and over 150 from amber and red, so brand blue never
 * reads as a status. The tight pair is warning to danger at 36 degrees,
 * which is why warning always ships with a tint and an icon as well.
 */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // NTT Blue. 600 is the brand colour.
        blue: {
          50: "#F2F8FC",
          100: "#E0EEF7",
          200: "#BDDAEE",
          300: "#8FC1E2",
          400: "#57A2D3",
          500: "#2486C5",
          600: "#0072BC",
          700: "#005B96",
          800: "#004471",
          900: "#002E4B",
        },
        // The dark navigation surface. Kept as its own family because the
        // sidebar needs a near-black anchor, and it is the deepest steps of
        // the brand ramp so the chrome reads as brand rather than as generic
        // dark grey.
        navy: {
          600: "#0072BC",
          700: "#005B96",
          800: "#004471",
          900: "#002E4B",
        },
        // Cool neutrals, unchanged. The existing greys sit well against a
        // cyan-leaning blue and carry no brand meaning, so replacing them
        // would be churn. The four values the app already used are kept
        // exactly; the rest are filled in so no stock shade leaks through.
        gray: {
          50: "#F7F8FA",
          100: "#F3F4F6",
          200: "#E5E7EB",
          300: "#D1D5DB",
          400: "#9CA3AF",
          500: "#6B7280",
          600: "#4B5563",
          700: "#374151",
          800: "#1F2937",
          900: "#111827",
        },
        // Success. 500 and up are text-safe, matching amber and red; 400 and
        // below are the fill steps.
        green: {
          50: "#EDF8F2",
          100: "#D3EFE0",
          200: "#A9DEC1",
          300: "#71C79C",
          400: "#35A874",
          500: "#0A7F47",
          600: "#086E3D",
          700: "#075A35",
          800: "#05432A",
          900: "#03301F",
        },
        // Warning. 500 is the text shade at 5.33:1, so the flag status can
        // stop borrowing a fill tone.
        amber: {
          50: "#FEF7EA",
          100: "#FDEDCB",
          200: "#FADCA0",
          300: "#F8C570",
          400: "#E8A33A",
          500: "#9A5D00",
          600: "#8A5100",
          700: "#7A4800",
          800: "#5C3700",
          900: "#432900",
        },
        // Danger. 500 is the text shade at 5.63:1.
        red: {
          50: "#FEF2F2",
          100: "#FDE0E0",
          200: "#FBC7C7",
          300: "#F79E9E",
          400: "#E56464",
          500: "#C42B2B",
          600: "#B02525",
          700: "#9A2020",
          800: "#7A1A1A",
          900: "#5C1414",
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
        card: "0 1px 2px rgba(0,46,75,0.06)",
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
