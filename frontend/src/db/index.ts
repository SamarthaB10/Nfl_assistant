import "server-only";

import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";

import * as schema from "./schema";

const databaseUrl = process.env.DATABASE_URL;

if (!databaseUrl) {
  throw new Error("DATABASE_URL is required.");
}

const globalForDatabase = globalThis as typeof globalThis & {
  leagueWatchPool?: Pool;
};

const pool =
  globalForDatabase.leagueWatchPool ??
  new Pool({
    connectionString: databaseUrl,
    max: 10,
  });

if (process.env.NODE_ENV !== "production") {
  globalForDatabase.leagueWatchPool = pool;
}

export const db = drizzle({ client: pool, schema });
