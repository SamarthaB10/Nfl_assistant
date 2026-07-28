import { beforeEach, describe, expect, it, vi } from "vitest";

const getSession = vi.fn();
const updateOwnProfile = vi.fn();

vi.mock("@/lib/auth", () => ({
  auth: {
    api: {
      getSession,
    },
  },
}));

vi.mock("@/lib/profiles", () => ({
  updateOwnProfile,
}));

describe("PATCH /api/profile", () => {
  beforeEach(() => {
    getSession.mockReset();
    updateOwnProfile.mockReset();
  });

  it("rejects anonymous profile updates", async () => {
    getSession.mockResolvedValue(null);
    const { PATCH } = await import("./route");

    const response = await PATCH(
      new Request("http://localhost/api/profile", {
        method: "PATCH",
        body: JSON.stringify({
          displayName: "Sunday Fan",
          about: "Updated bio",
        }),
      }),
    );

    expect(response.status).toBe(401);
    expect(updateOwnProfile).not.toHaveBeenCalled();
  });

  it("derives the updated user from the verified session", async () => {
    getSession.mockResolvedValue({
      user: { id: "session-user", username: "sunday_fan" },
    });
    updateOwnProfile.mockResolvedValue({
      username: "sunday_fan",
      displayName: "Sunday Fan",
      about: "Updated bio",
      avatarUrl: "/profile-default-avatar.svg",
      headerUrl: "/profile-default-header.svg",
      joinedAt: "2025-09-04T12:00:00.000Z",
    });
    const { PATCH } = await import("./route");

    const response = await PATCH(
      new Request("http://localhost/api/profile", {
        method: "PATCH",
        body: JSON.stringify({
          userId: "another-user",
          displayName: " Sunday Fan ",
          about: " Updated bio ",
        }),
      }),
    );

    expect(response.status).toBe(200);
    expect(updateOwnProfile).toHaveBeenCalledWith("session-user", {
      displayName: "Sunday Fan",
      about: "Updated bio",
    });
  });

  it("rejects invalid profile text before writing", async () => {
    getSession.mockResolvedValue({
      user: { id: "session-user", username: "sunday_fan" },
    });
    const { PATCH } = await import("./route");

    const response = await PATCH(
      new Request("http://localhost/api/profile", {
        method: "PATCH",
        body: JSON.stringify({
          displayName: "",
          about: "x".repeat(301),
        }),
      }),
    );

    expect(response.status).toBe(422);
    expect(updateOwnProfile).not.toHaveBeenCalled();
  });
});
