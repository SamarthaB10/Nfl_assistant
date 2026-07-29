import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

const styles = readFileSync(resolve("src/app/globals.css"), "utf8");
const darkTokens = styles.slice(0, styles.indexOf('html[data-theme="light"]'));

describe("Drizzle theme styles", () => {
  it("defines a true-black dark palette without the retired red", () => {
    expect(darkTokens).toContain("--canvas: #000;");
    expect(darkTokens).toContain("--ink: #ebdbb2;");
    expect(darkTokens).toContain("--brand: #1e90ff;");
    expect(darkTokens).not.toMatch(/#f12738|#b70f20|--red/);
  });

  it("uses the original display font and blue token for Drizzle titles", () => {
    expect(styles).toMatch(
      /\.brand-wordmark,[\s\S]*?\.hero h1\.hero-brand-title\s*\{[\s\S]*?color:\s*var\(--brand\);[\s\S]*?font-family:\s*var\(--font-display/,
    );
    expect(styles).toMatch(/\.brand-mark__tile\s*\{[\s\S]*?fill:\s*var\(--brand\)/);
    expect(styles).toMatch(
      /\.brand-mark__stroke\s*\{[\s\S]*?stroke:\s*var\(--brand\)/,
    );
    expect(styles).not.toContain("--font-script");
  });

  it("rounds account and authentication actions into pill controls", () => {
    expect(styles).toMatch(
      /\.account-nav a,[\s\S]*?\.account-nav button\s*\{[\s\S]*?border-radius:\s*999px;/,
    );
    expect(styles).toMatch(
      /\.auth-submit\s*\{[\s\S]*?border-radius:\s*999px;/,
    );
  });
});
