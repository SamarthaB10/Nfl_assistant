import { beforeEach, describe, expect, it, vi } from "vitest";

const getSession = vi.fn();
const softDeleteOwnComment = vi.fn();

vi.mock("@/lib/auth", () => ({
  auth: {
    api: {
      getSession,
    },
  },
}));

vi.mock("@/lib/comments", () => ({
  softDeleteOwnComment,
}));

const context = {
  params: Promise.resolve({ commentId: "17" }),
};

describe("DELETE /api/comments/:commentId", () => {
  beforeEach(() => {
    getSession.mockReset();
    softDeleteOwnComment.mockReset();
  });

  it("requires authentication", async () => {
    getSession.mockResolvedValue(null);
    const { DELETE } = await import("./route");

    const response = await DELETE(
      new Request("http://localhost/api/comments/17", { method: "DELETE" }),
      context,
    );

    expect(response.status).toBe(401);
    expect(softDeleteOwnComment).not.toHaveBeenCalled();
  });

  it("uses the session user for an author-owned soft delete", async () => {
    getSession.mockResolvedValue({ user: { id: "session-user" } });
    softDeleteOwnComment.mockResolvedValue(true);
    const { DELETE } = await import("./route");

    const response = await DELETE(
      new Request("http://localhost/api/comments/17", { method: "DELETE" }),
      context,
    );

    expect(response.status).toBe(204);
    expect(softDeleteOwnComment).toHaveBeenCalledWith(17, "session-user");
  });

  it("returns a generic not-found response for invalid ownership", async () => {
    getSession.mockResolvedValue({ user: { id: "another-user" } });
    softDeleteOwnComment.mockResolvedValue(false);
    const { DELETE } = await import("./route");

    const response = await DELETE(
      new Request("http://localhost/api/comments/17", { method: "DELETE" }),
      context,
    );

    expect(response.status).toBe(404);
  });
});
