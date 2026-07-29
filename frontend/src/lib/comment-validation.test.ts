import { describe, expect, it } from "vitest";

import {
  commentCreateSchema,
  commentIdSchema,
  commentPageQuerySchema,
  decodeCommentCursor,
  encodeCommentCursor,
  gameKeySchema,
} from "./comment-validation";

describe("gameKeySchema", () => {
  it("accepts a 2025 regular-season matchup key", () => {
    expect(gameKeySchema.parse("2025_18_SEA_SF")).toBe("2025_18_SEA_SF");
  });

  it("rejects unsupported seasons, weeks, teams, and duplicate teams", () => {
    expect(gameKeySchema.safeParse("2026_01_SEA_SF").success).toBe(false);
    expect(gameKeySchema.safeParse("2025_19_SEA_SF").success).toBe(false);
    expect(gameKeySchema.safeParse("2025_01_XXX_SF").success).toBe(false);
    expect(gameKeySchema.safeParse("2025_01_SEA_SEA").success).toBe(false);
  });
});

describe("commentCreateSchema", () => {
  it("trims a comment and accepts an optional parent identifier", () => {
    expect(
      commentCreateSchema.parse({
        body: "  Huge divisional game.  ",
        parentCommentId: 42,
      }),
    ).toEqual({
      body: "Huge divisional game.",
      parentCommentId: 42,
    });
  });

  it("rejects empty, oversized, and deeply nested input shapes", () => {
    expect(commentCreateSchema.safeParse({ body: "   " }).success).toBe(false);
    expect(
      commentCreateSchema.safeParse({ body: "x".repeat(1001) }).success,
    ).toBe(false);
    expect(
      commentCreateSchema.safeParse({
        body: "Reply",
        parentCommentId: 2,
        grandparentCommentId: 1,
      }).success,
    ).toBe(false);
  });
});

describe("comment pagination validation", () => {
  it("defaults to 20 comments and round-trips an opaque cursor", () => {
    const cursor = encodeCommentCursor({
      createdAt: new Date("2025-12-29T01:00:00.000Z"),
      id: 91,
    });

    expect(
      commentPageQuerySchema.parse({ cursor: cursor }).limit,
    ).toBe(20);
    expect(decodeCommentCursor(cursor)).toEqual({
      createdAt: new Date("2025-12-29T01:00:00.000Z"),
      id: 91,
    });
  });

  it("rejects malformed cursors, oversized limits, and unsafe IDs", () => {
    expect(
      commentPageQuerySchema.safeParse({ cursor: "not-a-cursor" }).success,
    ).toBe(false);
    expect(commentPageQuerySchema.safeParse({ limit: "21" }).success).toBe(
      false,
    );
    expect(commentIdSchema.safeParse("0").success).toBe(false);
    expect(
      commentIdSchema.safeParse(String(Number.MAX_SAFE_INTEGER + 1)).success,
    ).toBe(false);
  });
});
