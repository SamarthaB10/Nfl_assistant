import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { GameCard } from "./game-card";

describe("GameCard", () => {
  it("renders an unranked scheduled game without a watch score", () => {
    render(
      <GameCard
        gameKey="2026_01_NE_BUF"
        game={
          {
            matchup: "New England Patriots vs Buffalo Bills",
            records: { NE: "Scheduled", BUF: "Scheduled" },
            logos: { NE: null, BUF: null },
            kickoff: "2026-09-10T00:20:00Z",
          }
        }
        rank={1}
      />,
    );

    expect(screen.getByText("Schedule")).toBeInTheDocument();
    expect(screen.queryByText("Watch rating")).not.toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  });

  it("renders the 2026 starting quarterbacks in the existing player format", () => {
    render(
      <GameCard
        gameKey="2026_01_NYG_DAL"
        game={{
          matchup: "New York Giants vs Dallas Cowboys",
          records: { NYG: "Scheduled", DAL: "Scheduled" },
          logos: { NYG: null, DAL: null },
          kickoff: "2026-09-13T17:00:00Z",
        }}
        rank={1}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: "View details for New York Giants vs Dallas Cowboys",
      }),
    );

    expect(screen.getByText("Starting quarterbacks")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Jaxson Dart" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Dak Prescott" })).toBeInTheDocument();
    expect(document.querySelectorAll(".player-portrait")).toHaveLength(2);
  });

  it("shows final scores beside each team and marks only the winner", () => {
    render(
      <GameCard
        gameKey="2025_01_SF_SEA"
        game={{
          matchup: "San Francisco 49ers vs Seattle Seahawks",
          records: { SF: "0-0", SEA: "0-0" },
          logos: { SF: null, SEA: null },
          finalScores: { SF: 17, SEA: 30 },
          score: 7.2,
          reasons: [],
        }}
        rank={1}
      />,
    );

    const winningScore = screen.getByLabelText(
      "Seattle Seahawks final score 30, winner",
    );
    const losingScore = screen.getByLabelText(
      "San Francisco 49ers final score 17",
    );

    expect(winningScore).toHaveTextContent("– 30");
    expect(winningScore).toHaveClass("is-winner");
    expect(losingScore).toHaveTextContent("– 17");
    expect(losingScore).not.toHaveClass("is-winner");
  });

  it("does not show scores when a game has not finished", () => {
    render(
      <GameCard
        gameKey="2025_02_BUF_DAL"
        game={{
          matchup: "Buffalo Bills vs Dallas Cowboys",
          records: { BUF: "1-0", DAL: "1-0" },
          logos: { BUF: null, DAL: null },
          finalScores: {},
          score: 6.4,
          reasons: [],
        }}
        rank={1}
      />,
    );

    expect(screen.queryByLabelText(/final score/)).not.toBeInTheDocument();
  });

  it("does not mark either team as the winner when a game ends tied", () => {
    render(
      <GameCard
        gameKey="2025_01_CIN_GB"
        game={{
          matchup: "Cincinnati Bengals vs Green Bay Packers",
          records: { CIN: "0-0", GB: "0-0" },
          logos: { CIN: null, GB: null },
          finalScores: { CIN: 27, GB: 27 },
          score: 6.8,
          reasons: [],
        }}
        rank={1}
      />,
    );

    expect(document.querySelectorAll(".team-final-score")).toHaveLength(2);
    expect(document.querySelectorAll(".team-final-score.is-winner")).toHaveLength(0);
  });

  it("assigns rating colors at the 7.0 and 5.5 boundaries", () => {
    render(
      <ul>
        <GameCard
          gameKey="2025_11_BUF_KC"
          game={{
            matchup: "Buffalo Bills vs Kansas City Chiefs",
            records: { BUF: "8-2", KC: "9-1" },
            logos: { BUF: null, KC: null },
            score: 7,
            reasons: [],
          }}
          rank={1}
        />
        <GameCard
          gameKey="2025_11_CHI_DET"
          game={{
            matchup: "Chicago Bears vs Detroit Lions",
            records: { CHI: "5-5", DET: "7-3" },
            logos: { CHI: null, DET: null },
            score: 5.5,
            reasons: [],
          }}
          rank={2}
        />
        <GameCard
          gameKey="2025_11_CAR_TEN"
          game={{
            matchup: "Carolina Panthers vs Tennessee Titans",
            records: { CAR: "3-7", TEN: "2-8" },
            logos: { CAR: null, TEN: null },
            score: 5.49,
            reasons: [],
          }}
          rank={3}
        />
      </ul>,
    );

    expect(
      screen
        .getByLabelText("Buffalo Bills vs Kansas City Chiefs watchability score")
        .closest(".rating-block"),
    ).toHaveClass("is-high-rating");
    expect(
      screen
        .getByLabelText("Chicago Bears vs Detroit Lions watchability score")
        .closest(".rating-block"),
    ).toHaveClass("is-mid-rating");
    expect(
      screen
        .getByLabelText("Chicago Bears vs Detroit Lions watchability score")
        .closest(".rating-block"),
    ).not.toHaveClass("is-high-rating");
    expect(
      screen
        .getByLabelText(
          "Carolina Panthers vs Tennessee Titans watchability score",
        )
        .closest(".rating-block"),
    ).not.toHaveClass("is-high-rating");
    expect(
      screen
        .getByLabelText(
          "Carolina Panthers vs Tennessee Titans watchability score",
        )
        .closest(".rating-block"),
    ).not.toHaveClass("is-mid-rating");
  });

  it("renders two dynamic players with season and peer details", () => {
    render(
      <GameCard
        gameKey="2025_18_LAC_DEN"
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
    expect(document.querySelectorAll(".player-portrait")).toHaveLength(2);
    expect(screen.getByText("1,108 receiving yards this season")).toBeInTheDocument();
    expect(
      screen.getByText("Ranked 4th among QBs in passing yards"),
    ).toBeInTheDocument();
  });

  it("renders Jaxson Dart instead of unavailable Malik Nabers", () => {
    render(
      <GameCard
        gameKey="2025_16_NYG_WAS"
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
