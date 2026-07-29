# Game Comments Specification

## Objective

Add a public discussion thread to each expanded weekly game ranking. Everyone
can read comments. Signed-in users can create top-level comments, reply once,
and soft-delete only their own comments.

## Approved Behaviour

- The discussion belongs to a stable game key such as `2025_18_SEA_SF`.
- Top-level comments are newest first.
- The API returns 20 top-level comments per page using cursor pagination.
- Replies are oldest first and support one nesting level only.
- Anyone can read comments.
- A verified server session is required to create, reply, or delete.
- Authors can delete their own comments. Comments cannot be edited.
- Deleting a comment replaces its body with a deleted placeholder so replies
  remain attached and readable.
- The expanded game view places a rounded, shiny green `Comment` control beneath
  the players-to-watch area.

## Data Model

`game_comments` stores:

| Column | Type | Rules |
| --- | --- | --- |
| `id` | bigint | Primary key |
| `game_key` | text | Required stable season/week/matchup key |
| `user_id` | text | Required foreign key to `users.id` |
| `parent_comment_id` | bigint | Optional self-reference for one-level replies |
| `body` | text | Required; validated as 1–1000 trimmed characters |
| `is_deleted` | boolean | Required; defaults to `false` |
| `created_at` | timestamptz | Required; defaults to the database clock |
| `updated_at` | timestamptz | Required; updated when soft-deleted |

Indexes support:

- newest-first cursor reads by game;
- oldest-first reply reads by parent;
- author-owned comment lookup and deletion.

The ranking data is not persisted, so `game_key` is deliberately not a foreign
key. API validation will enforce the key format and supported teams.

## API Contract

Planned routes:

- `GET /api/games/:gameKey/comments?limit=20&cursor=...`
- `POST /api/games/:gameKey/comments`
- `DELETE /api/comments/:commentId`

Create accepts `body` and an optional `parentCommentId`. A reply parent must be
an undeleted top-level comment for the same game. Delete derives the actor from
the server session and never accepts a user ID from the client.

## Security Rules

- Treat game keys, cursors, identifiers, and bodies as untrusted input.
- Validate and trim bodies at the HTTP boundary.
- Use parameterized Drizzle queries.
- Render comment text as React text only; do not use raw HTML.
- Require authentication for all writes and verify ownership for deletion.
- Do not return a deleted comment body after soft deletion.

Comment-specific rate limiting is not included in this slice and requires a
separate product decision.

## Out of Scope

- Editing
- Anonymous posting
- Reactions or votes
- More than one reply level
- Admin moderation tools
- Comments on news articles
- Live updates or notifications

## Delivery Increments

1. PostgreSQL schema, migration, and schema tests.
2. Validated API and authorization tests.
3. Responsive game-card discussion UI and browser verification.
