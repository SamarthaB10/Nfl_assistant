import { z } from "zod";

import { NFL_TEAMS } from "./nfl-teams";

const teamCodes = new Set<string>(NFL_TEAMS.map((team) => team.code));
const gameKeyPattern = /^2025_(0[1-9]|1[0-8])_([A-Z]{2,3})_([A-Z]{2,3})$/;

export const gameKeySchema = z.string().superRefine((value, context) => {
  const match = gameKeyPattern.exec(value);
  if (!match) {
    context.addIssue({
      code: "custom",
      message: "Invalid game key.",
    });
    return;
  }

  const awayTeam = match[2];
  const homeTeam = match[3];
  if (
    !teamCodes.has(awayTeam) ||
    !teamCodes.has(homeTeam) ||
    awayTeam === homeTeam
  ) {
    context.addIssue({
      code: "custom",
      message: "Invalid game key.",
    });
  }
});

export const commentCreateSchema = z
  .object({
    body: z.string().trim().min(1).max(1000),
    parentCommentId: z.number().int().positive().safe().optional(),
  })
  .strict();

const cursorPayloadSchema = z.object({
  createdAt: z.string().datetime(),
  id: z.number().int().positive().safe(),
});

export type CommentCursor = {
  createdAt: Date;
  id: number;
};

export function encodeCommentCursor(cursor: CommentCursor): string {
  return Buffer.from(
    JSON.stringify({
      createdAt: cursor.createdAt.toISOString(),
      id: cursor.id,
    }),
  ).toString("base64url");
}

export function decodeCommentCursor(rawCursor: string): CommentCursor | null {
  try {
    const decoded: unknown = JSON.parse(
      Buffer.from(rawCursor, "base64url").toString("utf8"),
    );
    const parsed = cursorPayloadSchema.safeParse(decoded);
    if (!parsed.success) {
      return null;
    }

    return {
      createdAt: new Date(parsed.data.createdAt),
      id: parsed.data.id,
    };
  } catch {
    return null;
  }
}

export const commentPageQuerySchema = z.object({
  limit: z.coerce.number().int().min(1).max(20).default(20),
  cursor: z
    .string()
    .max(256)
    .refine((value) => decodeCommentCursor(value) !== null, {
      message: "Invalid comment cursor.",
    })
    .optional(),
});

export const commentIdSchema = z
  .string()
  .regex(/^[1-9]\d*$/)
  .transform(Number)
  .refine(Number.isSafeInteger);

export type CommentCreateInput = z.infer<typeof commentCreateSchema>;
