import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: { 900: "#0C172F", 700: "#1A366B" },
        blue: { 600: "#175FEE", 50: "#EAF1FF" },
        green: { 600: "#0E9354" },
        red: { 500: "#E5484D", soft: "#F4A6AC" },
        amber: { 500: "#FDB84E" },
        gray: {
          900: "#111827",
          500: "#6B7280",
          200: "#E5E7EB",
          50: "#F7F8FA",
        },
      },
      fontFamily: {
        sans: [
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
        card: "0 1px 2px rgba(16,24,40,0.05)",
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
