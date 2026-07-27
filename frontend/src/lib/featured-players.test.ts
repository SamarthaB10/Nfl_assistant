import { describe, expect, it } from "vitest";

import {
  FEATURED_PLAYER_CANDIDATES,
  selectFeaturedPlayers,
} from "./featured-players";

const NFL_TEAM_IDS = [
  "ARI",
  "ATL",
  "BAL",
  "BUF",
  "CAR",
  "CHI",
  "CIN",
  "CLE",
  "DAL",
  "DEN",
  "DET",
  "GB",
  "HOU",
  "IND",
  "JAX",
  "KC",
  "LAC",
  "LAR",
  "LV",
  "MIA",
  "MIN",
  "NE",
  "NO",
  "NYG",
  "NYJ",
  "PHI",
  "PIT",
  "SEA",
  "SF",
  "TB",
  "TEN",
  "WAS",
];

describe("FEATURED_PLAYER_CANDIDATES", () => {
  it("provides candidates for every NFL team", () => {
    expect(Object.keys(FEATURED_PLAYER_CANDIDATES).sort()).toEqual(NFL_TEAM_IDS);
    expect(
      Object.values(FEATURED_PLAYER_CANDIDATES).every(
        (candidates) => candidates.length > 0,
      ),
    ).toBe(true);
  });

  it("covers both teams in the Bills-Patriots matchup", () => {
    expect(FEATURED_PLAYER_CANDIDATES.BUF?.[0]?.name).toBe("Josh Allen");
    expect(FEATURED_PLAYER_CANDIDATES.NE?.[0]?.name).toBe("Drake Maye");
  });
});

describe("selectFeaturedPlayers", () => {
  it("selects Jaxson Dart when Malik Nabers is unavailable", () => {
    const players = selectFeaturedPlayers(["NYG"], ["4595348"]);

    expect(players).toEqual([
      expect.objectContaining({
        id: "4689114",
        name: "Jaxson Dart",
        position: "QB",
        teamId: "NYG",
      }),
    ]);
    expect(players.map((player) => player.id)).not.toContain("4595348");
  });

  it("treats an absent unavailable-player list as empty", () => {
    expect(selectFeaturedPlayers(["NYG"])).toEqual([
      expect.objectContaining({
        id: "4595348",
        name: "Malik Nabers",
        teamId: "NYG",
      }),
    ]);
  });
});
