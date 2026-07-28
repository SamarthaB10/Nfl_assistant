import { getTableConfig } from "drizzle-orm/pg-core";
import { describe, expect, it } from "vitest";

import { account, rateLimit, session, user, verification } from "./schema";

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
