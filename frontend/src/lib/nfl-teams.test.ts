import { describe, expect, it } from "vitest";

import { getNflTeam } from "./nfl-teams";

describe("getNflTeam", () => {
  it("returns the display name and ESPN logo for a known team", () => {
    expect(getNflTeam("ATL")).toEqual({
      code: "ATL",
      name: "Atlanta Falcons",
      logoUrl: "https://a.espncdn.com/i/teamlogos/nfl/500/atl.png",
    });
  });

  it("uses ESPN's Washington logo alias", () => {
    expect(getNflTeam("WAS")?.logoUrl).toBe(
      "https://a.espncdn.com/i/teamlogos/nfl/500/wsh.png",
    );
  });

  it("returns null for an unknown team code", () => {
    expect(getNflTeam("NFL")).toBeNull();
  });
});
