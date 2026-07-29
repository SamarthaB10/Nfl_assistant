import { afterEach, describe, expect, it, vi } from "vitest";

import { GET } from "./route";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("GET /api/headlines", () => {
  it("forwards only supported headline fields to FastAPI", async () => {
    const backendResponse = {
      items: [],
      nextCursor: null,
      hasMore: false,
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValue(Response.json(backendResponse, { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const response = await GET(
      new Request(
        "http://localhost:3000/api/headlines?limit=20&source=ESPN&team=NE&cursor=next-page&ignored=yes",
      ),
    );

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/headlines?limit=20&cursor=next-page&source=ESPN&team=NE",
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
      new Request("http://localhost:3000/api/headlines?limit=20"),
    );

    expect(response.status).toBe(502);
    await expect(response.json()).resolves.toEqual({
      detail: "Unable to reach the Drizzle API.",
    });
  });
});
