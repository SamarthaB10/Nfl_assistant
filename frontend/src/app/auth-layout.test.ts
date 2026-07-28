import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

const styles = readFileSync(resolve("src/app/globals.css"), "utf8");

describe("authentication page layout", () => {
  it("scales the hero heading against its grid column instead of the viewport", () => {
    expect(styles).toMatch(
      /\.auth-page__intro\s*\{[\s\S]*?container-type:\s*inline-size;/,
    );
    expect(styles).toMatch(
      /\.auth-page__intro h1\s*\{[\s\S]*?font-size:\s*clamp\(2\.1rem,\s*12cqi,\s*6\.8rem\);/,
    );
  });
});
