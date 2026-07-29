import { beforeEach, describe, expect, it, vi } from "vitest";

const getSession = vi.fn();
const createGameComment = vi.fn();
const getGameComments = vi.fn();

vi.mock("@/lib/auth", () => ({
  auth: {
    api: {
      getSession,
    },
  },
}));

vi.mock("@/lib/comments", () => ({
  InvalidCommentParentError: class InvalidCommentParentError extends Error {},
  createGameComment,
  getGameComments,
}));

const context = {
  params: Promise.resolve({ gameKey: "2025_18_SEA_SF" }),
};

describe("GET /api/games/:gameKey/comments", () => {
  beforeEach(() => {
    getSession.mockReset();
    createGameComment.mockReset();
    getGameComments.mockReset();
  });

  it("allows public cursor-paginated reads", async () => {
    getSession.mockResolvedValue(null);
    getGameComments.mockResolvedValue({
      comments: [],
      nextCursor: null,
    });
    const { GET } = await import("./route");

    const response = await GET(
      new Request("http://localhost/api/games/2025_18_SEA_SF/comments?limit=20"),
      context,
    );

    expect(response.status).toBe(200);
    expect(getGameComments).toHaveBeenCalledWith({
      gameKey: "2025_18_SEA_SF",
      limit: 20,
      cursor: undefined,
      viewerId: undefined,
    });
  });

  it("rejects invalid game keys before reading the database", async () => {
    const { GET } = await import("./route");
    const response = await GET(
      new Request("http://localhost/api/games/invalid/comments"),
      { params: Promise.resolve({ gameKey: "invalid" }) },
    );

    expect(response.status).toBe(422);
    expect(getGameComments).not.toHaveBeenCalled();
  });
});

describe("POST /api/games/:gameKey/comments", () => {
  beforeEach(() => {
    getSession.mockReset();
    createGameComment.mockReset();
    getGameComments.mockReset();
  });

  it("requires authentication before accepting a comment", async () => {
    getSession.mockResolvedValue(null);
    const { POST } = await import("./route");

    const response = await POST(
      new Request("http://localhost/api/games/2025_18_SEA_SF/comments", {
        method: "POST",
        body: JSON.stringify({ body: "Must watch." }),
      }),
      context,
    );

    expect(response.status).toBe(401);
    expect(createGameComment).not.toHaveBeenCalled();
  });

  it("derives the author from the verified session", async () => {
    getSession.mockResolvedValue({ user: { id: "session-user" } });
    createGameComment.mockResolvedValue({ id: 7, body: "Must watch." });
    const { POST } = await import("./route");

    const response = await POST(
      new Request("http://localhost/api/games/2025_18_SEA_SF/comments", {
        method: "POST",
        body: JSON.stringify({
          body: "  Must watch.  ",
        }),
      }),
      context,
    );

    expect(response.status).toBe(201);
    expect(createGameComment).toHaveBeenCalledWith({
      gameKey: "2025_18_SEA_SF",
      userId: "session-user",
      body: "Must watch.",
      parentCommentId: undefined,
    });
  });

  it("rejects invalid JSON and invalid reply parents", async () => {
    getSession.mockResolvedValue({ user: { id: "session-user" } });
    const { InvalidCommentParentError } = await import("@/lib/comments");
    const { POST } = await import("./route");

    const invalidJson = await POST(
      new Request("http://localhost/api/games/2025_18_SEA_SF/comments", {
        method: "POST",
        body: "{",
      }),
      context,
    );
    expect(invalidJson.status).toBe(400);

    createGameComment.mockRejectedValue(
      new InvalidCommentParentError("Invalid parent."),
    );
    const invalidParent = await POST(
      new Request("http://localhost/api/games/2025_18_SEA_SF/comments", {
        method: "POST",
        body: JSON.stringify({ body: "Reply", parentCommentId: 9 }),
      }),
      context,
    );
    expect(invalidParent.status).toBe(422);
  });
});
