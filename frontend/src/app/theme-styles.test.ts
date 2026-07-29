import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

const styles = readFileSync(resolve("src/app/globals.css"), "utf8");
const darkTokens = styles.slice(0, styles.indexOf('html[data-theme="light"]'));

describe("Drizzle theme styles", () => {
  it("defines the requested warm dark palette without the retired red", () => {
    expect(darkTokens).toContain("--canvas: #32302f;");
    expect(darkTokens).toContain("--ink: #ebdbb2;");
    expect(darkTokens).toContain("--brand: #1e90ff;");
    expect(darkTokens).not.toMatch(/#f12738|#b70f20|--red/);
  });

  it("uses the script font and blue brand token for Drizzle titles", () => {
    expect(styles).toMatch(
      /\.hero h1\.hero-brand-title\s*\{[\s\S]*?color:\s*var\(--brand\);[\s\S]*?font-family:\s*var\(--font-script/,
    );
    expect(styles).toMatch(
      /\.brand-mark\s*\{[\s\S]*?color:\s*var\(--brand\);[\s\S]*?font-family:\s*var\(--font-script/,
    );
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
