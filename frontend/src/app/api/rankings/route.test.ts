import { afterEach, describe, expect, it, vi } from "vitest";

import { GET } from "./route";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("GET /api/rankings", () => {
  it("forwards validated ranking fields to FastAPI", async () => {
    const backendResponse = [
      {
        matchup: "Seattle Seahawks vs San Francisco 49ers",
        records: { SEA: "13-3", SF: "12-4" },
        score: 8.39,
        reasons: ["Divisional matchup"],
      },
    ];
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json(backendResponse, {
        status: 200,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await GET(
      new Request(
        "http://localhost:3000/api/rankings?season=2025&week=18&top=5&ignored=yes",
      ),
    );

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/rankings?season=2025&week=18&top=5",
      {
        cache: "no-store",
        headers: { accept: "application/json" },
      },
    );
    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(backendResponse);
  });

  it("returns a useful gateway error when FastAPI is unreachable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    const response = await GET(
      new Request("http://localhost:3000/api/rankings?season=2025&week=4"),
    );

    expect(response.status).toBe(502);
    await expect(response.json()).resolves.toEqual({
      detail: "Unable to reach the Drizzle API.",
    });
  });
});
