import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { GameComment } from "@/lib/game-comments";

import { GameComments } from "./game-comments";

const existingComment: GameComment = {
  id: 4,
  body: "This division title game is appointment viewing.",
  isDeleted: false,
  createdAt: "2025-12-29T01:00:00.000Z",
  canDelete: true,
  author: {
    username: "sunday_fan",
    displayName: "Sunday Fan",
    avatarUrl: "/profile-default-avatar.svg",
  },
  replies: [],
};

describe("GameComments", () => {
  it("lets signed-out visitors open and read the public discussion", async () => {
    const loadComments = vi.fn().mockResolvedValue({
      comments: [{ ...existingComment, canDelete: false }],
      nextCursor: null,
    });

    render(
      <GameComments
        gameKey="2025_18_SEA_SF"
        loadComments={loadComments}
        resolveSignedIn={() => Promise.resolve(false)}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Comment" }));

    expect(
      await screen.findByText(
        "This division title game is appointment viewing.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Log in to comment" })).toHaveAttribute(
      "href",
      "/login",
    );
    expect(loadComments).toHaveBeenCalledWith(
      "2025_18_SEA_SF",
      undefined,
      expect.any(AbortSignal),
    );
  });

  it("lets a signed-in user publish a top-level comment", async () => {
    const submitComment = vi.fn().mockResolvedValue({
      ...existingComment,
      id: 8,
      body: "Seattle's offense makes this must-watch.",
    });

    render(
      <GameComments
        gameKey="2025_18_SEA_SF"
        loadComments={() =>
          Promise.resolve({ comments: [], nextCursor: null })
        }
        resolveSignedIn={() => Promise.resolve(true)}
        submitComment={submitComment}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Comment" }));
    const composer = await screen.findByRole("textbox", {
      name: "Write a comment",
    });
    fireEvent.change(composer, {
      target: { value: "Seattle's offense makes this must-watch." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Post comment" }));

    expect(
      await screen.findByText("Seattle's offense makes this must-watch."),
    ).toBeInTheDocument();
    expect(submitComment).toHaveBeenCalledWith(
      "2025_18_SEA_SF",
      "Seattle's offense makes this must-watch.",
      undefined,
    );
  });

  it("supports one-level replies and author-owned deletion", async () => {
    const submitComment = vi.fn().mockResolvedValue({
      ...existingComment,
      id: 12,
      body: "The defensive matchup is the key.",
      replies: [],
    });
    const removeComment = vi.fn().mockResolvedValue(undefined);

    render(
      <GameComments
        gameKey="2025_18_SEA_SF"
        loadComments={() =>
          Promise.resolve({
            comments: [existingComment],
            nextCursor: null,
          })
        }
        removeComment={removeComment}
        resolveSignedIn={() => Promise.resolve(true)}
        submitComment={submitComment}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Comment" }));
    await screen.findByText(
      "This division title game is appointment viewing.",
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Reply to @sunday_fan" }),
    );
    fireEvent.change(
      screen.getByRole("textbox", { name: "Reply to @sunday_fan" }),
      { target: { value: "The defensive matchup is the key." } },
    );
    fireEvent.click(screen.getByRole("button", { name: "Post reply" }));

    await waitFor(() => {
      expect(document.querySelector(".comment-replies")).toHaveTextContent(
        "The defensive matchup is the key.",
      );
    });
    expect(submitComment).toHaveBeenCalledWith(
      "2025_18_SEA_SF",
      "The defensive matchup is the key.",
      4,
    );

    fireEvent.click(
      screen.getAllByRole("button", {
        name: "Delete comment by @sunday_fan",
      })[0],
    );
    await waitFor(() => expect(removeComment).toHaveBeenCalledWith(4));
    expect(screen.getByText("Comment deleted.")).toBeInTheDocument();
  });

  it("loads the next cursor page without replacing existing comments", async () => {
    const laterComment = {
      ...existingComment,
      id: 22,
      body: "The older matchup context belongs on page two.",
      canDelete: false,
    };
    const loadComments = vi
      .fn()
      .mockResolvedValueOnce({
        comments: [{ ...existingComment, canDelete: false }],
        nextCursor: "page-two",
      })
      .mockResolvedValueOnce({
        comments: [laterComment],
        nextCursor: null,
      });

    render(
      <GameComments
        gameKey="2025_18_SEA_SF"
        loadComments={loadComments}
        resolveSignedIn={() => Promise.resolve(false)}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Comment" }));
    await screen.findByText(
      "This division title game is appointment viewing.",
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Load more comments" }),
    );

    expect(
      await screen.findByText(
        "The older matchup context belongs on page two.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("This division title game is appointment viewing."),
    ).toBeInTheDocument();
    expect(loadComments).toHaveBeenLastCalledWith(
      "2025_18_SEA_SF",
      "page-two",
    );
  });
});
