import {
  type AnyPgColumn,
  bigint,
  bigserial,
  boolean,
  index,
  pgTable,
  text,
  timestamp,
  uniqueIndex,
} from "drizzle-orm/pg-core";

const createdAt = timestamp("created_at", { withTimezone: true })
  .defaultNow()
  .notNull();
const updatedAt = timestamp("updated_at", { withTimezone: true })
  .defaultNow()
  .$onUpdate(() => new Date())
  .notNull();

export const user = pgTable(
  "users",
  {
    id: text("id").primaryKey(),
    name: text("name").notNull(),
    email: text("email").notNull(),
    emailVerified: boolean("email_verified").default(false).notNull(),
    image: text("image"),
    username: text("username").notNull(),
    displayUsername: text("display_username"),
    about: text("about"),
    imageObjectKey: text("image_object_key"),
    headerObjectKey: text("header_object_key"),
    createdAt,
    updatedAt,
  },
  (table) => [
    uniqueIndex("users_email_unique").on(table.email),
    uniqueIndex("users_username_unique").on(table.username),
  ],
);

export const session = pgTable(
  "sessions",
  {
    id: text("id").primaryKey(),
    expiresAt: timestamp("expires_at", { withTimezone: true }).notNull(),
    token: text("token").notNull(),
    createdAt,
    updatedAt,
    ipAddress: text("ip_address"),
    userAgent: text("user_agent"),
    userId: text("user_id")
      .notNull()
      .references(() => user.id, { onDelete: "cascade" }),
  },
  (table) => [
    uniqueIndex("sessions_token_unique").on(table.token),
    index("sessions_user_id_index").on(table.userId),
  ],
);

export const account = pgTable(
  "accounts",
  {
    id: text("id").primaryKey(),
    accountId: text("account_id").notNull(),
    providerId: text("provider_id").notNull(),
    userId: text("user_id")
      .notNull()
      .references(() => user.id, { onDelete: "cascade" }),
    accessToken: text("access_token"),
    refreshToken: text("refresh_token"),
    idToken: text("id_token"),
    accessTokenExpiresAt: timestamp("access_token_expires_at", {
      withTimezone: true,
    }),
    refreshTokenExpiresAt: timestamp("refresh_token_expires_at", {
      withTimezone: true,
    }),
    scope: text("scope"),
    password: text("password"),
    createdAt,
    updatedAt,
  },
  (table) => [
    uniqueIndex("accounts_provider_account_unique").on(
      table.providerId,
      table.accountId,
    ),
    index("accounts_user_id_index").on(table.userId),
  ],
);

export const verification = pgTable(
  "verifications",
  {
    id: text("id").primaryKey(),
    identifier: text("identifier").notNull(),
    value: text("value").notNull(),
    expiresAt: timestamp("expires_at", { withTimezone: true }).notNull(),
    createdAt,
    updatedAt,
  },
  (table) => [index("verifications_identifier_index").on(table.identifier)],
);

export const rateLimit = pgTable(
  "rate_limits",
  {
    id: text("id").primaryKey(),
    key: text("key").notNull(),
    count: bigint("count", { mode: "number" }).notNull(),
    lastRequest: bigint("last_request", { mode: "number" }).notNull(),
  },
  (table) => [uniqueIndex("rate_limits_key_unique").on(table.key)],
);

export const newsArticles = pgTable(
  "news_articles",
  {
    id: bigserial("id", { mode: "number" }).primaryKey(),
    source: text("source").notNull(),
    sourceArticleId: text("source_article_id").notNull(),
    title: text("title").notNull(),
    author: text("author"),
    excerpt: text("excerpt"),
    canonicalUrl: text("canonical_url").notNull(),
    imageUrl: text("image_url"),
    teamCodes: text("team_codes").array().notNull(),
    publishedAt: timestamp("published_at", { withTimezone: true }).notNull(),
    fetchedAt: timestamp("fetched_at", { withTimezone: true })
      .defaultNow()
      .notNull(),
    updatedAt: timestamp("updated_at", { withTimezone: true })
      .defaultNow()
      .notNull(),
  },
  (table) => [
    uniqueIndex("news_articles_source_article_unique").on(
      table.source,
      table.sourceArticleId,
    ),
    uniqueIndex("news_articles_canonical_url_unique").on(table.canonicalUrl),
    index("news_articles_cursor_idx").on(
      table.publishedAt.desc(),
      table.id.desc(),
    ),
    index("news_articles_source_cursor_idx").on(
      table.source,
      table.publishedAt.desc(),
      table.id.desc(),
    ),
    index("news_articles_team_codes_idx").using("gin", table.teamCodes),
  ],
);

export const gameComments = pgTable(
  "game_comments",
  {
    id: bigserial("id", { mode: "number" }).primaryKey(),
    gameKey: text("game_key").notNull(),
    userId: text("user_id")
      .notNull()
      .references(() => user.id, { onDelete: "cascade" }),
    parentCommentId: bigint("parent_comment_id", {
      mode: "number",
    }).references((): AnyPgColumn => gameComments.id, {
      onDelete: "cascade",
    }),
    body: text("body").notNull(),
    isDeleted: boolean("is_deleted").default(false).notNull(),
    createdAt,
    updatedAt,
  },
  (table) => [
    index("game_comments_game_cursor_idx").on(
      table.gameKey,
      table.createdAt.desc(),
      table.id.desc(),
    ),
    index("game_comments_parent_created_idx").on(
      table.parentCommentId,
      table.createdAt,
      table.id,
    ),
    index("game_comments_user_id_idx").on(table.userId),
  ],
);

export const authSchema = {
  user,
  session,
  account,
  verification,
  rateLimit,
};

export type UserRecord = typeof user.$inferSelect;
export type GameCommentRecord = typeof gameComments.$inferSelect;
