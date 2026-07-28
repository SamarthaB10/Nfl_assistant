import { defineConfig } from "drizzle-kit";

const localDatabaseUrl =
  "postgresql://leaguewatch:leaguewatch@127.0.0.1:5433/leaguewatch";

export default defineConfig({
  dialect: "postgresql",
  schema: "./src/db/schema.ts",
  out: "./drizzle",
  dbCredentials: {
    url: process.env.DATABASE_URL ?? localDatabaseUrl,
  },
  strict: true,
  verbose: true,
});
