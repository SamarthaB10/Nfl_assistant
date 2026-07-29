import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createGameComment,
  deleteGameComment,
  fetchGameComments,
} from "./game-comments";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("game comments client", () => {
  it("loads a cursor page with the approved 20-comment limit", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json({ comments: [], nextCursor: null }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await fetchGameComments("2025_18_SEA_SF", "next page");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/games/2025_18_SEA_SF/comments?limit=20&cursor=next+page",
      expect.objectContaining({ signal: undefined }),
    );
  });

  it("posts a reply without accepting a client-supplied author", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json({ comment: { id: 9, body: "Reply" } }, { status: 201 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await createGameComment("2025_18_SEA_SF", "Reply", 4);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/games/2025_18_SEA_SF/comments",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ body: "Reply", parentCommentId: 4 }),
      }),
    );
  });

  it("uses the author-owned delete endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(null, { status: 204 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await deleteGameComment(14);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/comments/14",
      expect.objectContaining({ method: "DELETE" }),
    );
  });
});
