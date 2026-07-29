import { afterEach, describe, expect, it, vi } from "vitest";

import { buildHeadlinesSearch, fetchHeadlines } from "./headlines";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("buildHeadlinesSearch", () => {
  it("includes only selected filters and a continuation cursor", () => {
    expect(
      buildHeadlinesSearch({
        source: "CBS",
        team: "BUF",
        cursor: "next-page",
      }).toString(),
    ).toBe("limit=20&source=CBS&team=BUF&cursor=next-page");
  });

  it("omits all-source and all-team filters", () => {
    expect(
      buildHeadlinesSearch({
        source: "ALL",
        team: "ALL",
      }).toString(),
    ).toBe("limit=20");
  });
});

describe("fetchHeadlines", () => {
  it("returns the paginated headline response", async () => {
    const page = {
      items: [
        {
          id: 1,
          source: "FOX",
          title: "Training camp opens",
          author: null,
          excerpt: "Current NFL coverage.",
          url: "https://www.foxsports.com/stories/nfl/training-camp-opens",
          imageUrl: null,
          teamCodes: ["KC"],
          publishedAt: "2026-07-29T18:00:00Z",
        },
      ],
      nextCursor: "next-page",
      hasMore: true,
    };
    const fetchMock = vi.fn().mockResolvedValue(Response.json(page));
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      fetchHeadlines({ source: "ALL", team: "ALL" }),
    ).resolves.toEqual(page);
    expect(fetchMock).toHaveBeenCalledWith("/api/headlines?limit=20", {
      signal: undefined,
    });
  });

  it("surfaces a backend error message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        Response.json(
          { detail: "Current NFL headlines are temporarily unavailable." },
          { status: 503 },
        ),
      ),
    );

    await expect(
      fetchHeadlines({ source: "ALL", team: "ALL" }),
    ).rejects.toThrow("Current NFL headlines are temporarily unavailable.");
  });
});
