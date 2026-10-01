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
  it("uses NTT Blue as the brand colour", () => {
    // NTT Blue, PANTONE 285C. NTT DATA unified their corporate logo colour
    // to the NTT Group colour on 1 July 2023.
    expect(configShades("blue")["600"]).toBe("#0072BC");
  });

  it("keeps chart constants in step with the Tailwind config", () => {
    const blue = configShades("blue");
    const green = configShades("green");
    const red = configShades("red");
    const amber = configShades("amber");

    expect(CHART.brand).toBe(blue["600"]);
    // Chart series use the fill step of each ramp, not the text step.
    expect(CHART.success).toBe(green["400"]);
    expect(CHART.danger).toBe(red["500"]);
    expect(CHART.warning).toBe(amber["400"]);
    expect(SURFACE).toBe("#FFFFFF");
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

  it("keeps every text-range semantic shade above AA on white", () => {
    // The old palette used one shade as both fill and text, so the status
    // vocabulary failed: amber 1.73:1, green 3.95:1, red 3.91:1.
    const luminance = (hex: string) => {
      const channel = (v: number) => {
        const c = v / 255;
        return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
      };
      const r = channel(parseInt(hex.slice(1, 3), 16));
      const g = channel(parseInt(hex.slice(3, 5), 16));
      const b = channel(parseInt(hex.slice(5, 7), 16));
      return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };
    const contrast = (hex: string) => 1.05 / (luminance(hex) + 0.05);

    for (const family of ["green", "amber", "red"]) {
      for (const step of [500, 600, 700, 800, 900]) {
        const value = configShades(family)[String(step)];
        expect(contrast(value), `${family}-${step} on white`).toBeGreaterThanOrEqual(4.5);
      }
    }
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
