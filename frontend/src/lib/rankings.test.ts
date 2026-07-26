import { describe, expect, it } from "vitest";

import { buildRankingsSearch } from "./rankings";

describe("buildRankingsSearch", () => {
  it("omits a result limit when all games are requested", () => {
    expect(
      buildRankingsSearch({ week: 4, mode: "all", count: 5 }).toString(),
    ).toBe("season=2025&week=4");
  });

  it("sends a top limit for the best games", () => {
    expect(
      buildRankingsSearch({ week: 18, mode: "top", count: 5 }).toString(),
    ).toBe("season=2025&week=18&top=5");
  });

  it("sends a bottom limit for the least-watchable games", () => {
    expect(
      buildRankingsSearch({ week: 9, mode: "bottom", count: 3 }).toString(),
    ).toBe("season=2025&week=9&bottom=3");
  });
});
