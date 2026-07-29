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

async function responseError(response: Response): Promise<Error> {
  let message = "The discussion request failed.";
  try {
    const payload: unknown = await response.json();
    if (
      typeof payload === "object" &&
      payload !== null &&
      "error" in payload &&
      typeof payload.error === "string"
    ) {
      message = payload.error;
    }
  } catch {
    // Keep the generic message for an empty or non-JSON error response.
  }
  return new Error(message);
}

export async function fetchGameComments(
  gameKey: string,
  cursor?: string,
  signal?: AbortSignal,
): Promise<GameCommentPage> {
  const search = new URLSearchParams({ limit: "20" });
  if (cursor) {
    search.set("cursor", cursor);
  }

  const response = await fetch(
    `/api/games/${encodeURIComponent(gameKey)}/comments?${search}`,
    { signal },
  );
  if (!response.ok) {
    throw await responseError(response);
  }

  return (await response.json()) as GameCommentPage;
}

export async function createGameComment(
  gameKey: string,
  body: string,
  parentCommentId?: number,
): Promise<GameComment> {
  const response = await fetch(
    `/api/games/${encodeURIComponent(gameKey)}/comments`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ body, parentCommentId }),
    },
  );
  if (!response.ok) {
    throw await responseError(response);
  }

  const payload = (await response.json()) as { comment: GameComment };
  return payload.comment;
}

export async function deleteGameComment(commentId: number): Promise<void> {
  const response = await fetch(`/api/comments/${commentId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw await responseError(response);
  }
}
