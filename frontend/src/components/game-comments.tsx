"use client";

import Link from "next/link";
import {
  FormEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import { authClient } from "@/lib/auth-client";
import {
  createGameComment,
  deleteGameComment,
  fetchGameComments,
  type GameComment,
  type GameCommentPage,
} from "@/lib/game-comments";

type GameCommentsProps = {
  gameKey: string;
  loadComments?: (
    gameKey: string,
    cursor?: string,
    signal?: AbortSignal,
  ) => Promise<GameCommentPage>;
  submitComment?: (
    gameKey: string,
    body: string,
    parentCommentId?: number,
  ) => Promise<GameComment>;
  removeComment?: (commentId: number) => Promise<void>;
  resolveSignedIn?: () => Promise<boolean>;
};

async function resolveCurrentSession(): Promise<boolean> {
  const { data } = await authClient.getSession();
  return Boolean(data?.user);
}

function removeCommentFromTree(
  comments: GameComment[],
  commentId: number,
): GameComment[] {
  return comments
    .filter((comment) => comment.id !== commentId)
    .map((comment) => ({
      ...comment,
      replies: removeCommentFromTree(comment.replies, commentId),
    }));
}

function appendReply(
  comments: GameComment[],
  parentCommentId: number,
  reply: GameComment,
): GameComment[] {
  return comments.map((comment) =>
    comment.id === parentCommentId
      ? { ...comment, replies: [...comment.replies, reply] }
      : comment,
  );
}

function formatCommentDate(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

export function GameComments({
  gameKey,
  loadComments = fetchGameComments,
  submitComment = createGameComment,
  removeComment = deleteGameComment,
  resolveSignedIn = resolveCurrentSession,
}: GameCommentsProps) {
  const [open, setOpen] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [signedIn, setSignedIn] = useState<boolean | null>(null);
  const [comments, setComments] = useState<GameComment[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [body, setBody] = useState("");
  const [replyBody, setReplyBody] = useState("");
  const [replyingTo, setReplyingTo] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(
    () => () => {
      controllerRef.current?.abort();
    },
    [],
  );

  async function loadInitialComments() {
    setLoading(true);
    setError("");
    const controller = new AbortController();
    controllerRef.current = controller;

    const sessionPromise = resolveSignedIn().catch(() => false);
    try {
      const [page, hasSession] = await Promise.all([
        loadComments(gameKey, undefined, controller.signal),
        sessionPromise,
      ]);
      setComments(page.comments);
      setNextCursor(page.nextCursor);
      setSignedIn(hasSession);
      setLoaded(true);
    } catch (caught) {
      if (caught instanceof DOMException && caught.name === "AbortError") {
        return;
      }
      setSignedIn(await sessionPromise);
      setError(
        caught instanceof Error
          ? caught.message
          : "The discussion could not be loaded.",
      );
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false);
      }
    }
  }

  function toggleComments() {
    const nextOpen = !open;
    setOpen(nextOpen);
    if (nextOpen && !loaded && !loading) {
      void loadInitialComments();
    }
  }

  async function handleTopLevelSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextBody = body.trim();
    if (!nextBody || submitting) {
      return;
    }

    setSubmitting(true);
    setError("");
    try {
      const comment = await submitComment(gameKey, nextBody, undefined);
      setComments((current) => [comment, ...current]);
      setBody("");
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Your comment was not posted.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleReplySubmit(
    event: FormEvent<HTMLFormElement>,
    parentCommentId: number,
  ) {
    event.preventDefault();
    const nextBody = replyBody.trim();
    if (!nextBody || submitting) {
      return;
    }

    setSubmitting(true);
    setError("");
    try {
      const reply = await submitComment(gameKey, nextBody, parentCommentId);
      setComments((current) => appendReply(current, parentCommentId, reply));
      setReplyBody("");
      setReplyingTo(null);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Your reply was not posted.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(commentId: number) {
    setError("");
    try {
      await removeComment(commentId);
      setComments((current) => removeCommentFromTree(current, commentId));
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "The comment could not be deleted.",
      );
    }
  }

  async function handleLoadMore() {
    if (!nextCursor || loadingMore) {
      return;
    }

    setLoadingMore(true);
    setError("");
    try {
      const page = await loadComments(gameKey, nextCursor);
      setComments((current) => [...current, ...page.comments]);
      setNextCursor(page.nextCursor);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "More comments could not be loaded.",
      );
    } finally {
      setLoadingMore(false);
    }
  }

  return (
    <section className={`game-comments${open ? " is-open" : ""}`}>
      <div className="game-comments__control">
        <button
          aria-expanded={open}
          className="comment-toggle"
          onClick={toggleComments}
          type="button"
        >
          <span aria-hidden="true">✦</span>
          Comment
        </button>
      </div>

      {open ? (
        <div className="comment-thread">
          <header className="comment-thread__header">
            <div>
              <p className="detail-label">Game discussion</p>
              <h4>What are you watching for?</h4>
            </div>
            {signedIn === false ? (
              <Link className="comment-login" href="/login">
                Log in to comment
              </Link>
            ) : null}
          </header>

          {signedIn ? (
            <form
              className="comment-composer"
              onSubmit={handleTopLevelSubmit}
            >
              <label className="sr-only" htmlFor={`comment-${gameKey}`}>
                Write a comment
              </label>
              <textarea
                id={`comment-${gameKey}`}
                maxLength={1000}
                onChange={(event) => setBody(event.target.value)}
                placeholder="Add your read on this matchup…"
                value={body}
              />
              <div>
                <span>{body.length}/1000</span>
                <button
                  disabled={!body.trim() || submitting}
                  type="submit"
                >
                  {submitting ? "Posting…" : "Post comment"}
                </button>
              </div>
            </form>
          ) : signedIn === false ? (
            <p className="comment-thread__notice">
              Comments are public. Sign in when you want to join the
              conversation.
            </p>
          ) : null}

          {error ? (
            <p className="comment-thread__error" role="alert">
              {error}
            </p>
          ) : null}

          {loading ? (
            <div
              aria-label="Loading comments"
              className="comment-thread__loading"
              role="status"
            >
              <span />
              <span />
            </div>
          ) : comments.length === 0 && loaded ? (
            <p className="comment-thread__empty">
              No comments yet. Start the conversation.
            </p>
          ) : (
            <ol className="comment-list">
              {comments.map((comment) => (
                <CommentEntry
                  comment={comment}
                  key={comment.id}
                  onDelete={handleDelete}
                  onReply={(commentId) => {
                    setReplyBody("");
                    setReplyingTo((current) =>
                      current === commentId ? null : commentId,
                    );
                  }}
                  onReplySubmit={handleReplySubmit}
                  replyBody={replyBody}
                  replyingTo={replyingTo}
                  setReplyBody={setReplyBody}
                  signedIn={Boolean(signedIn)}
                  submitting={submitting}
                />
              ))}
            </ol>
          )}

          {nextCursor ? (
            <button
              className="comment-load-more"
              disabled={loadingMore}
              onClick={() => void handleLoadMore()}
              type="button"
            >
              {loadingMore ? "Loading…" : "Load more comments"}
            </button>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

type CommentEntryProps = {
  comment: GameComment;
  signedIn: boolean;
  replyingTo: number | null;
  replyBody: string;
  submitting: boolean;
  setReplyBody: (body: string) => void;
  onReply: (commentId: number) => void;
  onDelete: (commentId: number) => Promise<void>;
  onReplySubmit: (
    event: FormEvent<HTMLFormElement>,
    parentCommentId: number,
  ) => Promise<void>;
};

function CommentEntry({
  comment,
  signedIn,
  replyingTo,
  replyBody,
  submitting,
  setReplyBody,
  onReply,
  onDelete,
  onReplySubmit,
}: CommentEntryProps) {
  const isReplying = replyingTo === comment.id;

  return (
    <li
      className={`comment${comment.isDeleted ? " is-deleted" : ""}`}
    >
      <div className="comment__avatar" aria-hidden="true">
        {comment.author.displayName.slice(0, 1).toUpperCase()}
      </div>
      <div className="comment__content">
        <header>
          <div>
            <strong>{comment.author.displayName}</strong>
            <Link href={`/u/${comment.author.username}`}>
              @{comment.author.username}
            </Link>
          </div>
          <time dateTime={comment.createdAt}>
            {formatCommentDate(comment.createdAt)}
          </time>
        </header>
        <p>{comment.body}</p>
        <footer>
          {signedIn && !comment.isDeleted ? (
            <button
              aria-label={`Reply to @${comment.author.username}`}
              onClick={() => onReply(comment.id)}
              type="button"
            >
              Reply
            </button>
          ) : null}
          {comment.canDelete ? (
            <button
              aria-label={`Delete comment by @${comment.author.username}`}
              className="comment__delete"
              onClick={() => void onDelete(comment.id)}
              type="button"
            >
              Delete
            </button>
          ) : null}
        </footer>

        {isReplying ? (
          <form
            className="reply-composer"
            onSubmit={(event) => void onReplySubmit(event, comment.id)}
          >
            <label className="sr-only" htmlFor={`reply-${comment.id}`}>
              Reply to @{comment.author.username}
            </label>
            <textarea
              autoFocus
              id={`reply-${comment.id}`}
              maxLength={1000}
              onChange={(event) => setReplyBody(event.target.value)}
              placeholder={`Reply to @${comment.author.username}…`}
              value={replyBody}
            />
            <div>
              <button onClick={() => onReply(comment.id)} type="button">
                Cancel
              </button>
              <button
                disabled={!replyBody.trim() || submitting}
                type="submit"
              >
                {submitting ? "Posting…" : "Post reply"}
              </button>
            </div>
          </form>
        ) : null}

        {comment.replies.length > 0 ? (
          <ol className="comment-replies">
            {comment.replies.map((reply) => (
              <CommentEntry
                comment={reply}
                key={reply.id}
                onDelete={onDelete}
                onReply={() => undefined}
                onReplySubmit={onReplySubmit}
                replyBody=""
                replyingTo={null}
                setReplyBody={() => undefined}
                signedIn={false}
                submitting={submitting}
              />
            ))}
          </ol>
        ) : null}
      </div>
    </li>
  );
}
