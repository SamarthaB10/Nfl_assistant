import "server-only";

import {
  and,
  asc,
  desc,
  eq,
  inArray,
  isNull,
  lt,
  or,
} from "drizzle-orm";

import { db } from "@/db";
import { gameComments, user } from "@/db/schema";

import {
  decodeCommentCursor,
  encodeCommentCursor,
} from "./comment-validation";
import { DEFAULT_AVATAR_URL } from "./public-profile";

const DELETED_COMMENT_BODY = "Comment deleted.";

const commentSelection = {
  id: gameComments.id,
  gameKey: gameComments.gameKey,
  userId: gameComments.userId,
  parentCommentId: gameComments.parentCommentId,
  body: gameComments.body,
  isDeleted: gameComments.isDeleted,
  createdAt: gameComments.createdAt,
  username: user.username,
  displayName: user.name,
};

type CommentRow = {
  id: number;
  gameKey: string;
  userId: string;
  parentCommentId: number | null;
  body: string;
  isDeleted: boolean;
  createdAt: Date;
  username: string;
  displayName: string;
};

export type GameComment = {
  id: number;
  body: string;
  isDeleted: boolean;
  createdAt: string;
  canDelete: boolean;
  author: {
    username: string;
    displayName: string;
    avatarUrl: string;
  };
  replies: GameComment[];
};

export type GameCommentPage = {
  comments: GameComment[];
  nextCursor: string | null;
};

export class InvalidCommentParentError extends Error {}

function toGameComment(
  row: CommentRow,
  viewerId?: string,
  replies: GameComment[] = [],
): GameComment {
  return {
    id: row.id,
    body: row.isDeleted ? DELETED_COMMENT_BODY : row.body,
    isDeleted: row.isDeleted,
    createdAt: row.createdAt.toISOString(),
    canDelete: !row.isDeleted && row.userId === viewerId,
    author: {
      username: row.username,
      displayName: row.displayName,
      avatarUrl: DEFAULT_AVATAR_URL,
    },
    replies,
  };
}

export async function getGameComments({
  gameKey,
  limit,
  cursor,
  viewerId,
}: {
  gameKey: string;
  limit: number;
  cursor?: string;
  viewerId?: string;
}): Promise<GameCommentPage> {
  const decodedCursor = cursor ? decodeCommentCursor(cursor) : null;
  const cursorCondition = decodedCursor
    ? or(
        lt(gameComments.createdAt, decodedCursor.createdAt),
        and(
          eq(gameComments.createdAt, decodedCursor.createdAt),
          lt(gameComments.id, decodedCursor.id),
        ),
      )
    : undefined;

  const rows = await db
    .select(commentSelection)
    .from(gameComments)
    .innerJoin(user, eq(gameComments.userId, user.id))
    .where(
      and(
        eq(gameComments.gameKey, gameKey),
        isNull(gameComments.parentCommentId),
        cursorCondition,
      ),
    )
    .orderBy(desc(gameComments.createdAt), desc(gameComments.id))
    .limit(limit + 1);

  const hasNextPage = rows.length > limit;
  const pageRows = rows.slice(0, limit);
  const parentIds = pageRows.map((row) => row.id);
  const replyRows =
    parentIds.length === 0
      ? []
      : await db
          .select(commentSelection)
          .from(gameComments)
          .innerJoin(user, eq(gameComments.userId, user.id))
          .where(
            and(
              eq(gameComments.gameKey, gameKey),
              inArray(gameComments.parentCommentId, parentIds),
            ),
          )
          .orderBy(asc(gameComments.createdAt), asc(gameComments.id));

  const repliesByParent = new Map<number, GameComment[]>();
  for (const row of replyRows) {
    if (row.parentCommentId === null) {
      continue;
    }

    const replies = repliesByParent.get(row.parentCommentId) ?? [];
    replies.push(toGameComment(row, viewerId));
    repliesByParent.set(row.parentCommentId, replies);
  }

  const comments = pageRows.map((row) =>
    toGameComment(row, viewerId, repliesByParent.get(row.id) ?? []),
  );
  const finalRow = pageRows.at(-1);

  return {
    comments,
    nextCursor:
      hasNextPage && finalRow
        ? encodeCommentCursor({
            createdAt: finalRow.createdAt,
            id: finalRow.id,
          })
        : null,
  };
}

export async function createGameComment({
  gameKey,
  userId,
  body,
  parentCommentId,
}: {
  gameKey: string;
  userId: string;
  body: string;
  parentCommentId?: number;
}): Promise<GameComment> {
  if (parentCommentId !== undefined) {
    const [parent] = await db
      .select({
        gameKey: gameComments.gameKey,
        parentCommentId: gameComments.parentCommentId,
        isDeleted: gameComments.isDeleted,
      })
      .from(gameComments)
      .where(eq(gameComments.id, parentCommentId))
      .limit(1);

    if (
      !parent ||
      parent.gameKey !== gameKey ||
      parent.parentCommentId !== null ||
      parent.isDeleted
    ) {
      throw new InvalidCommentParentError("Invalid reply parent.");
    }
  }

  const [inserted] = await db
    .insert(gameComments)
    .values({
      gameKey,
      userId,
      body,
      parentCommentId,
    })
    .returning({ id: gameComments.id });

  const [row] = await db
    .select(commentSelection)
    .from(gameComments)
    .innerJoin(user, eq(gameComments.userId, user.id))
    .where(eq(gameComments.id, inserted.id))
    .limit(1);

  if (!row) {
    throw new Error("Created comment could not be loaded.");
  }

  return toGameComment(row, userId);
}

export async function softDeleteOwnComment(
  commentId: number,
  userId: string,
): Promise<boolean> {
  const deleted = await db
    .update(gameComments)
    .set({
      body: "",
      isDeleted: true,
      updatedAt: new Date(),
    })
    .where(
      and(
        eq(gameComments.id, commentId),
        eq(gameComments.userId, userId),
        eq(gameComments.isDeleted, false),
      ),
    )
    .returning({ id: gameComments.id });

  return deleted.length === 1;
}
