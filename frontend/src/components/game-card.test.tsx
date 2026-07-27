import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { GameCard } from "./game-card";

describe("GameCard", () => {
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
