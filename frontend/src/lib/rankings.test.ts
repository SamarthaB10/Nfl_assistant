import { describe, expect, it } from "vitest";

import { buildGameKey, buildRankingsSearch } from "./rankings";

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

describe("buildGameKey", () => {
  it("combines the selected week with away and home team order", () => {
    expect(buildGameKey(18, ["SEA", "SF"])).toBe("2025_18_SEA_SF");
    expect(buildGameKey(4, ["TB", "SEA"])).toBe("2025_04_TB_SEA");
  });

  it("rejects a matchup without exactly two teams", () => {
    expect(() => buildGameKey(18, ["SEA"])).toThrow(
      "A game key requires exactly two teams.",
    );
  });
});
