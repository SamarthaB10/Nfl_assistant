import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { GameCard } from "./game-card";

describe("GameCard", () => {
  it("renders two dynamic players with season and peer details", () => {
    render(
      <GameCard
        game={{
          matchup: "Los Angeles Chargers vs Denver Broncos",
          records: { LAC: "11-5", DEN: "13-3" },
          logos: { LAC: null, DEN: null },
          score: 8.1,
          reasons: [],
          playersToWatch: [
            {
              playerId: "00-001",
              teamId: "LAC",
              name: "Ladd McConkey",
              position: "WR",
              imageUrl: "https://example.test/mcconkey.png",
              profileUrl: "https://example.test/mcconkey",
              details: [
                "1,108 receiving yards this season",
                "7 receiving TDs this season",
                "Ranked 5th among WRs in receiving yards",
              ],
            },
            {
              playerId: "00-002",
              teamId: "DEN",
              name: "Bo Nix",
              position: "QB",
              imageUrl: "https://example.test/nix.png",
              profileUrl: "https://example.test/nix",
              details: [
                "3,931 passing yards this season",
                "28 passing TDs this season",
                "Ranked 4th among QBs in passing yards",
              ],
            },
          ],
        }}
        rank={1}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: "View details for Los Angeles Chargers vs Denver Broncos",
      }),
    );

    expect(screen.getByRole("img", { name: "Ladd McConkey" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Bo Nix" })).toBeInTheDocument();
    expect(screen.getByText("1,108 receiving yards this season")).toBeInTheDocument();
    expect(
      screen.getByText("Ranked 4th among QBs in passing yards"),
    ).toBeInTheDocument();
  });

  it("renders Jaxson Dart instead of unavailable Malik Nabers", () => {
    render(
      <GameCard
        game={{
          matchup: "New York Giants vs Washington Commanders",
          records: { NYG: "2-12", WAS: "4-10" },
          logos: { NYG: null, WAS: null },
          score: 4.2,
          reasons: [],
          unavailablePlayerIds: ["4595348"],
        }}
        rank={1}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: "View details for New York Giants vs Washington Commanders",
      }),
    );

    expect(
      screen.queryByRole("img", { name: "Malik Nabers" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: "Jaxson Dart" }),
    ).toBeInTheDocument();
  });
});
