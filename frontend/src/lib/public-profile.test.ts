import { describe, expect, it } from "vitest";

import {
  DEFAULT_AVATAR_URL,
  DEFAULT_HEADER_URL,
  toPublicProfile,
} from "./public-profile";

describe("toPublicProfile", () => {
  it("returns only fields approved for a public profile", () => {
    const profile = toPublicProfile({
      id: "internal-user-id",
      email: "private@example.com",
      emailVerified: false,
      name: "Sunday Fan",
      username: "sunday_fan",
      about: "I never miss a divisional game.",
      imageObjectKey: null,
      headerObjectKey: null,
      createdAt: new Date("2025-09-04T12:00:00Z"),
      updatedAt: new Date("2025-09-05T12:00:00Z"),
    });

    expect(profile).toEqual({
      username: "sunday_fan",
      displayName: "Sunday Fan",
      about: "I never miss a divisional game.",
      avatarUrl: DEFAULT_AVATAR_URL,
      headerUrl: DEFAULT_HEADER_URL,
      joinedAt: "2025-09-04T12:00:00.000Z",
    });
    expect(profile).not.toHaveProperty("email");
    expect(profile).not.toHaveProperty("id");
    expect(profile).not.toHaveProperty("emailVerified");
  });
});
