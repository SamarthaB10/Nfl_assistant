import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RankingsWorkspace } from "./rankings-workspace";

const topGame = {
  matchup: "Seattle Seahawks vs San Francisco 49ers",
  records: { SEA: "13-3", SF: "12-4" },
  logos: {
    SEA: "https://a.espncdn.com/i/teamlogos/nfl/500/sea.png",
    SF: "https://a.espncdn.com/i/teamlogos/nfl/500/sf.png",
  },
  score: 8.39,
  reasons: [
    "Divisional matchup",
    "Direct division race matchup",
    "Headline: 49ers host the Seahawks with the division title on the line",
  ],
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("RankingsWorkspace", () => {
  it("loads the default Week 18 top-five rankings", async () => {
    const fetchMock = vi.fn().mockResolvedValue(Response.json([topGame]));
    vi.stubGlobal("fetch", fetchMock);

    render(<RankingsWorkspace />);

    expect(
      screen.getByRole("heading", {
        name: "Know what’s worth watching.",
      }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Loading matchups")).toBeInTheDocument();
    expect(
      await screen.findByText("Seattle Seahawks vs San Francisco 49ers"),
    ).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "SEA logo" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "SF logo" })).toBeInTheDocument();
    expect(screen.getByText("8.39")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/rankings?season=2025&week=18&top=5",
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    );
  });

  it("reveals headlines and featured players when a game is opened", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(Response.json([topGame])));

    render(<RankingsWorkspace />);
    await screen.findByText("Seattle Seahawks vs San Francisco 49ers");

    expect(
      screen.queryByText(
        "49ers host the Seahawks with the division title on the line",
      ),
    ).not.toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", {
        name: "View details for Seattle Seahawks vs San Francisco 49ers",
      }),
    );

    expect(
      screen.getByText(
        "49ers host the Seahawks with the division title on the line",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: "Jaxon Smith-Njigba" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: "Christian McCaffrey" }),
    ).toBeInTheDocument();
  });

  it("requests the bottom count selected by the user", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(Response.json([topGame]))
      .mockResolvedValueOnce(
        Response.json([
          {
            matchup: "Kansas City Chiefs vs Las Vegas Raiders",
            records: { KC: "6-10", LV: "2-14" },
            logos: {
              KC: "https://a.espncdn.com/i/teamlogos/nfl/500/kc.png",
              LV: "https://a.espncdn.com/i/teamlogos/nfl/500/lv.png",
            },
            score: 2.78,
            reasons: ["Divisional matchup"],
          },
        ]),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<RankingsWorkspace />);
    await screen.findByText("Seattle Seahawks vs San Francisco 49ers");

    fireEvent.click(screen.getByRole("button", { name: "Bottom" }));
    fireEvent.change(screen.getByRole("spinbutton", { name: "Number of games" }), {
      target: { value: "3" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Rank matchups" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenLastCalledWith(
        "/api/rankings?season=2025&week=18&bottom=3",
        expect.objectContaining({ signal: undefined }),
      );
    });
    expect(
      await screen.findByText("Kansas City Chiefs vs Las Vegas Raiders"),
    ).toBeInTheDocument();
    expect(screen.getByText("Week 18 · Bottom 3")).toBeInTheDocument();
  });

  it("shows the API error without removing the controls", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        Response.json(
          { detail: "Unable to reach the NFL Viewer API." },
          { status: 502 },
        ),
      ),
    );

    render(<RankingsWorkspace />);

    expect(
      await screen.findByText("Unable to reach the NFL Viewer API."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Rank matchups" }),
    ).toBeEnabled();
  });
});
