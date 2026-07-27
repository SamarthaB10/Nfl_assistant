import { describe, expect, it } from "vitest";

import { FEATURED_PLAYERS } from "./featured-players";

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

describe("FEATURED_PLAYERS", () => {
  it("provides exactly one player for every NFL team", () => {
    expect(Object.keys(FEATURED_PLAYERS).sort()).toEqual(NFL_TEAM_IDS);
  });

  it("covers both teams in the Bills-Patriots matchup", () => {
    expect(FEATURED_PLAYERS.BUF?.name).toBe("Josh Allen");
    expect(FEATURED_PLAYERS.NE?.name).toBe("Drake Maye");
  });
});
