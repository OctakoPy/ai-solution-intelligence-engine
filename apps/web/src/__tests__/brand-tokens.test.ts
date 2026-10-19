import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { CHART, SURFACE } from "@/lib/palette";

/**
 * Guards the brand palette against the two ways it drifts.
 *
 * The palette was previously defined twice - in `tailwind.config.ts` and as
 * thirteen CSS custom properties in `globals.css` that nothing read - and a
 * fourth time as inline hex in the Overview charts, which is how three
 * unrelated ambers ended up in one codebase. Nothing caught it, because no
 * test asserted on colour.
 */

const CONFIG = readFileSync(join(process.cwd(), "tailwind.config.ts"), "utf-8");

/** Values declared for one palette in the Tailwind config. */
function configShades(family: string): Record<string, string> {
  const start = CONFIG.indexOf(`\n        ${family}: {`);
  expect(start, `palette "${family}" must exist in tailwind.config.ts`).toBeGreaterThan(-1);
  // Walk to the matching close brace rather than slicing to end of file,
  // which would merge every later palette into this one.
  let depth = 0;
  let end = start;
  for (let i = CONFIG.indexOf("{", start); i < CONFIG.length; i += 1) {
    if (CONFIG[i] === "{") depth += 1;
    else if (CONFIG[i] === "}") {
      depth -= 1;
      if (depth === 0) {
        end = i;
        break;
      }
    }
  }
  const shades: Record<string, string> = {};
  const re = /(\d{2,3}):\s*"(#[0-9A-Fa-f]{6})"/g;
  let m: RegExpExecArray | null;
  const block = CONFIG.slice(start, end);
  while ((m = re.exec(block)) !== null) shades[m[1]] = m[2];
  return shades;
}

/** Every .ts/.tsx/.css file under src, excluding tests. */
function sourceFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) {
      // Tests assert on literal colour values, so they are not scanned.
      return name === "__tests__" ? [] : sourceFiles(path);
    }
    return /\.(ts|tsx|css)$/.test(name) ? [path] : [];
  });
}

describe("brand palette", () => {
  it("uses NTT Blue as the brand colour on a brand-blue page", () => {
    // NTT Blue, PANTONE 285C. NTT DATA unified their corporate logo colour
    // to the NTT Group colour on 1 July 2023. It stays a *fill* carrying
    // white text, so primary buttons keep the brand colour.
    expect(configShades("blue")["600"]).toBe("#0072BC");
    // The page is the deepest step of the same ramp, not a neutral dark grey.
    expect(configShades("gray")["50"]).toBe("#002E4B");
    expect(configShades("blue")["900"]).toBe("#002E4B");
    // Brand blue as text on a navy card is unreadable, so text uses 300.
    expect(configShades("blue")["300"]).toBe("#7AB5DE");
  });

  it("keeps chart constants in step with the Tailwind config", () => {
    const blue = configShades("blue");
    const green = configShades("green");
    const red = configShades("red");
    const amber = configShades("amber");

    // Chart series use the fill step of each ramp, not the text step.
    expect(CHART.success).toBe(green["400"]);
    expect(CHART.warning).toBe(amber["400"]);
    expect(SURFACE).toBe(configShades("gray")["100"]);

    // danger is the 500 step rather than the 400 fill: the 400 red is only
    // 2.9:1 on the card, too faint for a 12px ring.
    expect(CHART.danger).toBe(red["500"]);

    // The brand series is deliberately NOT blue-600. #0072BC is the brand for
    // fills carrying white text, and on a navy card it is 1.7:1, so a donut
    // drawn in it would be invisible. It is a lifted brand blue instead, and
    // the "visible against the card surface" test below is what holds it.
    expect(CHART.brand).not.toBe(blue["600"]);
  });

  it("defines every shade of every palette so no stock Tailwind colour leaks", () => {
    // theme.extend merges with Tailwind's defaults, so an incomplete palette
    // silently leaves stock shades available at the call site. A quarter of
    // the colour usages in this app were stock Tailwind before this was fixed.
    for (const family of ["blue", "navy", "gray", "green", "amber", "red"]) {
      const shades = configShades(family);
      for (const step of [50, 100, 200, 300, 400, 500, 600, 700, 800, 900]) {
        if (family === "navy" && step < 600) continue; // sidebar needs only the dark steps
        expect(shades[String(step)], `${family}-${step}`).toMatch(/^#[0-9A-F]{6}$/);
      }
    }
  });

  it("keeps every text-range semantic shade above AA on the dark surfaces", () => {
    // The light theme used one shade as both fill and text, so the status
    // vocabulary failed: amber 1.73:1, green 3.95:1, red 3.91:1. These are
    // now the dark-theme text steps and are checked against both surfaces a
    // card or the page can sit on.
    const card = "#0A3A5C";
    const page = "#002E4B";
    const contrast = (a: string, b: string) => {
      const channel = (hex: string, from: number) => {
        const v = parseInt(hex.slice(from, from + 2), 16) / 255;
        return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
      };
      const lum = (hex: string) =>
        0.2126 * channel(hex, 1) + 0.7152 * channel(hex, 3) + 0.0722 * channel(hex, 5);
      const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x);
      return (hi + 0.05) / (lo + 0.05);
    };

    for (const family of ["green", "amber", "red"]) {
      for (const step of [500, 600, 700, 800, 900]) {
        const value = configShades(family)[String(step)];
        expect(contrast(value, card), `${family}-${step} on card`).toBeGreaterThanOrEqual(4.5);
        expect(contrast(value, page), `${family}-${step} on page`).toBeGreaterThanOrEqual(4.5);
      }
    }
  });

  it("keeps body text legible on both dark surfaces", () => {
    const card = "#0A3A5C";
    const page = "#002E4B";
    const luminance = (hex: string) => {
      const channel = (from: number) => {
        const v = parseInt(hex.slice(from, from + 2), 16) / 255;
        return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
      };
      return 0.2126 * channel(1) + 0.7152 * channel(3) + 0.0722 * channel(5);
    };
    const contrast = (a: string, b: string) => {
      const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
      return (hi + 0.05) / (lo + 0.05);
    };
    const gray = configShades("gray");
    // 900 is body text, 500 is the most-used muted token in the app.
    for (const step of ["500", "600", "700", "900"]) {
      expect(contrast(gray[step], card), `gray-${step} on card`).toBeGreaterThanOrEqual(4.5);
      expect(contrast(gray[step], page), `gray-${step} on page`).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("keeps chart series visible against the card surface", () => {
    const luminance = (hex: string) => {
      const channel = (from: number) => {
        const v = parseInt(hex.slice(from, from + 2), 16) / 255;
        return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
      };
      return 0.2126 * channel(1) + 0.7152 * channel(3) + 0.0722 * channel(5);
    };
    const contrast = (a: string, b: string) => {
      const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
      return (hi + 0.05) / (lo + 0.05);
    };
    // Graphics need 3:1, not the 4.5:1 that text does.
    for (const [name, value] of Object.entries(CHART)) {
      expect(contrast(value, SURFACE), `${name} series`).toBeGreaterThanOrEqual(3);
    }
  });

  it("never uses a fill or border tone as text", () => {
    // The dark migration inverted the grey ramp but kept the class names, so
    // `text-gray-800` went from "strong text" to a *fill* — the sidebar hover
    // at #123E5D, which is 1.25:1 on the page and darker than its own
    // background. The contrast tests above only cover the text-range steps, so
    // this catches the fill/text mix-ups they cannot see.
    const fillOrBorder: Record<string, number[]> = {
      // 800 is the sidebar hover fill; 50 is the page.
      gray: [50, 100, 200, 300, 800],
      // Only 300 is a text step: brand blue as text on navy is 2.33:1.
      blue: [50, 100, 200, 400, 500, 600, 700, 800, 900],
      navy: [600, 700, 800, 900],
      // 50–300 are tints and borders; 500+ are the dark-theme text steps.
      green: [50, 100, 200, 300],
      amber: [50, 100, 200, 300],
      red: [50, 100, 200, 300],
    };
    const offenders: string[] = [];
    for (const file of sourceFiles(join(process.cwd(), "src"))) {
      const text = readFileSync(file, "utf-8");
      for (const [family, steps] of Object.entries(fillOrBorder)) {
        for (const step of steps) {
          const re = new RegExp(`\\btext-${family}-${step}\\b`, "g");
          if (re.test(text)) offenders.push(`${file}: text-${family}-${step}`);
        }
      }
    }
    expect(offenders).toEqual([]);
  });

  it("keeps the raised inset step lighter than the card it sits on", () => {
    // An inset panel inside a card must read as raised, not as a hole. The
    // page colour used as an inset is only 1.19:1 against the card, so the
    // distinction disappears entirely.
    const luminance = (hex: string) => {
      const channel = (from: number) => {
        const v = parseInt(hex.slice(from, from + 2), 16) / 255;
        return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
      };
      return 0.2126 * channel(1) + 0.7152 * channel(3) + 0.0722 * channel(5);
    };
    const gray = configShades("gray");
    expect(luminance(gray["200"])).toBeGreaterThan(luminance(gray["100"]));
    expect(luminance(gray["100"])).toBeGreaterThan(luminance(gray["50"]));
  });

  it("contains no raw colour literals in src outside the palette module", () => {
    const offenders: string[] = [];
    for (const file of sourceFiles(join(process.cwd(), "src"))) {
      if (file.endsWith("palette.ts")) continue;
      const text = readFileSync(file, "utf-8");
      // Ignore #root and similar selectors by requiring a hex length of 3 or 6.
      const matches = text.match(/#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b/g) ?? [];
      if (matches.length > 0) {
        offenders.push(`${file}: ${[...new Set(matches)].join(", ")}`);
      }
    }
    expect(offenders).toEqual([]);
  });

  it("defines no CSS colour custom properties", () => {
    // The palette is token-first; components.json sets cssVariables false.
    const css = readFileSync(join(process.cwd(), "src/styles/globals.css"), "utf-8");
    const declared = css.match(/--(?:blue|navy|gray|green|red|amber|white)[\w-]*\s*:/g);
    expect(declared ?? []).toEqual([]);
  });
});
