import { describe, expect, it } from "vitest";

import {
  profileUpdateSchema,
  signupSchema,
} from "./profile-validation";

describe("signupSchema", () => {
  it("normalizes email and username while trimming the display name", () => {
    const result = signupSchema.parse({
      email: "  FAN@Example.COM ",
      username: "  Fourth_Down  ",
      displayName: "  Sunday Fan  ",
      password: "watchfootball",
    });

    expect(result).toEqual({
      email: "fan@example.com",
      username: "fourth_down",
      displayName: "Sunday Fan",
      password: "watchfootball",
    });
  });

  it("rejects usernames outside the approved public-handle format", () => {
    const result = signupSchema.safeParse({
      email: "fan@example.com",
      username: "two-minute!",
      displayName: "Sunday Fan",
      password: "watchfootball",
    });

    expect(result.success).toBe(false);
  });

  it("enforces the password and display-name limits", () => {
    const shortPassword = signupSchema.safeParse({
      email: "fan@example.com",
      username: "fourth_down",
      displayName: "Sunday Fan",
      password: "short",
    });
    const longName = signupSchema.safeParse({
      email: "fan@example.com",
      username: "fourth_down",
      displayName: "x".repeat(51),
      password: "watchfootball",
    });

    expect(shortPassword.success).toBe(false);
    expect(longName.success).toBe(false);
  });
});

describe("profileUpdateSchema", () => {
  it("trims public profile text", () => {
    expect(
      profileUpdateSchema.parse({
        displayName: "  Sunday Fan  ",
        about: "  Watching every AFC East matchup.  ",
      }),
    ).toEqual({
      displayName: "Sunday Fan",
      about: "Watching every AFC East matchup.",
    });
  });

  it("allows an empty About section but rejects more than 300 characters", () => {
    expect(
      profileUpdateSchema.safeParse({
        displayName: "Sunday Fan",
        about: "",
      }).success,
    ).toBe(true);
    expect(
      profileUpdateSchema.safeParse({
        displayName: "Sunday Fan",
        about: "x".repeat(301),
      }).success,
    ).toBe(false);
  });
});
