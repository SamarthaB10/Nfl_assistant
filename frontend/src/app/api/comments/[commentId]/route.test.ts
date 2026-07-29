import { beforeEach, describe, expect, it, vi } from "vitest";

const getSession = vi.fn();
const deleteOwnComment = vi.fn();

vi.mock("@/lib/auth", () => ({
  auth: {
    api: {
      getSession,
    },
  },
}));

vi.mock("@/lib/comments", () => ({
  deleteOwnComment,
}));

const context = {
  params: Promise.resolve({ commentId: "17" }),
};

describe("DELETE /api/comments/:commentId", () => {
  beforeEach(() => {
    getSession.mockReset();
    deleteOwnComment.mockReset();
  });

  it("requires authentication", async () => {
    getSession.mockResolvedValue(null);
    const { DELETE } = await import("./route");

    const response = await DELETE(
      new Request("http://localhost/api/comments/17", { method: "DELETE" }),
      context,
    );

    expect(response.status).toBe(401);
    expect(deleteOwnComment).not.toHaveBeenCalled();
  });

  it("uses the session user for an author-owned hard delete", async () => {
    getSession.mockResolvedValue({ user: { id: "session-user" } });
    deleteOwnComment.mockResolvedValue(true);
    const { DELETE } = await import("./route");

    const response = await DELETE(
      new Request("http://localhost/api/comments/17", { method: "DELETE" }),
      context,
    );

    expect(response.status).toBe(204);
    expect(deleteOwnComment).toHaveBeenCalledWith(17, "session-user");
  });

  it("returns a generic not-found response for invalid ownership", async () => {
    getSession.mockResolvedValue({ user: { id: "another-user" } });
    deleteOwnComment.mockResolvedValue(false);
    const { DELETE } = await import("./route");

    const response = await DELETE(
      new Request("http://localhost/api/comments/17", { method: "DELETE" }),
      context,
    );

    expect(response.status).toBe(404);
  });
});
