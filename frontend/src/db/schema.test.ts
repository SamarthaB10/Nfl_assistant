import { getTableConfig } from "drizzle-orm/pg-core";
import { describe, expect, it } from "vitest";

import {
  account,
  newsArticles,
  rateLimit,
  session,
  user,
  verification,
} from "./schema";

describe("authentication schema", () => {
  it("stores LeagueWatch public profile fields with unique identity constraints", () => {
    const config = getTableConfig(user);
    const indexNames = config.indexes.map((index) => index.config.name);

    expect(config.name).toBe("users");
    expect(user.email.notNull).toBe(true);
    expect(user.username.notNull).toBe(true);
    expect(user.about.notNull).toBe(false);
    expect(user.imageObjectKey.notNull).toBe(false);
    expect(user.headerObjectKey.notNull).toBe(false);
    expect(indexNames).toEqual(
      expect.arrayContaining(["users_email_unique", "users_username_unique"]),
    );
  });

  it("defines every Better Auth and database rate-limit table", () => {
    expect(
      [session, account, verification, rateLimit].map(
        (table) => getTableConfig(table).name,
      ),
    ).toEqual(["sessions", "accounts", "verifications", "rate_limits"]);
  });
});

describe("news article schema", () => {
  it("stores publisher metadata for a rolling current-news feed", () => {
    const config = getTableConfig(newsArticles);

    expect(config.name).toBe("news_articles");
    expect(newsArticles.source.notNull).toBe(true);
    expect(newsArticles.sourceArticleId.notNull).toBe(true);
    expect(newsArticles.title.notNull).toBe(true);
    expect(newsArticles.author.notNull).toBe(false);
    expect(newsArticles.excerpt.notNull).toBe(false);
    expect(newsArticles.canonicalUrl.notNull).toBe(true);
    expect(newsArticles.imageUrl.notNull).toBe(false);
    expect(newsArticles.teamCodes.notNull).toBe(true);
    expect(newsArticles.publishedAt.notNull).toBe(true);
  });

  it("defines deduplication and cursor filtering indexes", () => {
    const config = getTableConfig(newsArticles);
    const indexes = new Map(
      config.indexes.map((index) => [index.config.name, index.config]),
    );

    expect([...indexes.keys()]).toEqual(
      expect.arrayContaining([
        "news_articles_source_article_unique",
        "news_articles_canonical_url_unique",
        "news_articles_cursor_idx",
        "news_articles_source_cursor_idx",
        "news_articles_team_codes_idx",
      ]),
    );
    expect(indexes.get("news_articles_source_article_unique")?.unique).toBe(
      true,
    );
    expect(indexes.get("news_articles_canonical_url_unique")?.unique).toBe(
      true,
    );
    expect(indexes.get("news_articles_team_codes_idx")?.method).toBe("gin");
  });
});
