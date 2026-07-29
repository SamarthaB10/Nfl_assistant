import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { HeadlinesWorkspace } from "./headlines-workspace";

const espnStory = {
  id: 1,
  source: "ESPN",
  title: "Sources: Browns and Delpit agree to extension",
  author: "NFL Nation",
  excerpt: "Cleveland secured a key member of its secondary before camp.",
  url: "https://www.espn.com/nfl/story/_/id/1/current",
  imageUrl: null,
  teamCodes: ["CLE"],
  publishedAt: "2026-07-29T19:45:50Z",
};

const cbsStory = {
  id: 2,
  source: "CBS",
  title: "NFL training camp injury tracker",
  author: null,
  excerpt: "The latest updates from practices around the league.",
  url: "https://www.cbssports.com/nfl/news/training-camp-injury-tracker/",
  imageUrl: "https://sportshub.cbsistatic.com/i/training-camp.jpg",
  teamCodes: ["BUF"],
  publishedAt: "2026-07-29T18:18:09Z",
};

function chooseFilter(label: string, option: string) {
  fireEvent.click(
    screen.getByRole("combobox", { name: new RegExp(`^${label}:`) }),
  );
  fireEvent.click(screen.getByRole("option", { name: option }));
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("HeadlinesWorkspace", () => {
  it("loads and presents the newest current NFL stories", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json({
        items: [espnStory],
        nextCursor: null,
        hasMore: false,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<HeadlinesWorkspace />);

    expect(
      screen.getByRole("heading", { name: "LIVE NEWS" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Loading headlines")).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", { name: espnStory.title }),
    ).toBeInTheDocument();
    expect(screen.getByText("NFL Nation")).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: "Cleveland Browns" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("CLE")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Sources: Browns/ })).toHaveAttribute(
      "href",
      espnStory.url,
    );
    expect(fetchMock).toHaveBeenCalledWith("/api/headlines?limit=20", {
      signal: expect.any(AbortSignal),
    });
  });

  it("reloads the feed with the selected publisher and team", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        Response.json({
          items: [espnStory],
          nextCursor: null,
          hasMore: false,
        }),
      )
      .mockResolvedValueOnce(
        Response.json({
          items: [cbsStory],
          nextCursor: null,
          hasMore: false,
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<HeadlinesWorkspace />);
    await screen.findByRole("heading", { name: espnStory.title });

    chooseFilter("Publisher", "CBS Sports");
    chooseFilter("Team", "Buffalo Bills");
    fireEvent.click(screen.getByRole("button", { name: "Update feed" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenLastCalledWith(
        "/api/headlines?limit=20&source=CBS&team=BUF",
        { signal: undefined },
      );
    });
    expect(
      await screen.findByRole("heading", { name: cbsStory.title }),
    ).toBeInTheDocument();
  });

  it("appends the next cursor page without removing visible stories", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        Response.json({
          items: [espnStory],
          nextCursor: "next-page",
          hasMore: true,
        }),
      )
      .mockResolvedValueOnce(
        Response.json({
          items: [cbsStory],
          nextCursor: null,
          hasMore: false,
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<HeadlinesWorkspace />);
    await screen.findByRole("heading", { name: espnStory.title });

    fireEvent.click(screen.getByRole("button", { name: "Load 20 more" }));

    expect(
      await screen.findByRole("heading", { name: cbsStory.title }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: espnStory.title }),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/headlines?limit=20&cursor=next-page",
      { signal: undefined },
    );
    expect(
      screen.queryByRole("button", { name: "Load 20 more" }),
    ).not.toBeInTheDocument();
  });

  it("shows meaningful empty and unavailable states", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        Response.json({
          items: [],
          nextCursor: null,
          hasMore: false,
        }),
      )
      .mockResolvedValueOnce(
        Response.json(
          { detail: "Current NFL headlines are temporarily unavailable." },
          { status: 503 },
        ),
      );
    vi.stubGlobal("fetch", fetchMock);

    const { unmount } = render(<HeadlinesWorkspace />);
    expect(await screen.findByText("No stories found.")).toBeInTheDocument();
    unmount();

    render(<HeadlinesWorkspace />);
    expect(
      await screen.findByText(
        "Current NFL headlines are temporarily unavailable.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try again" })).toBeEnabled();
  });

  it("retries the publisher and team selection that failed", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        Response.json({
          items: [espnStory],
          nextCursor: null,
          hasMore: false,
        }),
      )
      .mockResolvedValueOnce(
        Response.json(
          { detail: "Current NFL headlines are temporarily unavailable." },
          { status: 503 },
        ),
      )
      .mockResolvedValueOnce(
        Response.json({
          items: [cbsStory],
          nextCursor: null,
          hasMore: false,
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<HeadlinesWorkspace />);
    await screen.findByRole("heading", { name: espnStory.title });

    chooseFilter("Publisher", "CBS Sports");
    chooseFilter("Team", "Buffalo Bills");
    fireEvent.click(screen.getByRole("button", { name: "Update feed" }));
    await screen.findByText(
      "Current NFL headlines are temporarily unavailable.",
    );

    fireEvent.click(screen.getByRole("button", { name: "Try again" }));

    await screen.findByRole("heading", { name: cbsStory.title });
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/headlines?limit=20&source=CBS&team=BUF",
      { signal: undefined },
    );
  });
});
