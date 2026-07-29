import "server-only";

import { drizzleAdapter } from "@better-auth/drizzle-adapter";
import { betterAuth } from "better-auth";
import { APIError } from "better-auth/api";
import { username } from "better-auth/plugins";

import { db } from "@/db";
import { authSchema } from "@/db/schema";

import { signupIdentitySchema } from "./profile-validation";

const appUrl = process.env.BETTER_AUTH_URL ?? "http://localhost:3000";

export const auth = betterAuth({
  appName: "Drizzle",
  baseURL: appUrl,
  secret: process.env.BETTER_AUTH_SECRET,
  database: drizzleAdapter(db, {
    provider: "pg",
    schema: authSchema,
  }),
  emailAndPassword: {
    enabled: true,
    autoSignIn: true,
    minPasswordLength: 8,
    maxPasswordLength: 128,
  },
  session: {
    expiresIn: 60 * 60 * 24 * 7,
    updateAge: 60 * 60 * 24,
  },
  rateLimit: {
    enabled: true,
    storage: "database",
    modelName: "rateLimit",
    customRules: {
      "/sign-in/email": {
        window: 60,
        max: 5,
      },
      "/sign-up/email": {
        window: 60 * 10,
        max: 5,
      },
    },
  },
  databaseHooks: {
    user: {
      create: {
        before: async (newUser) => {
          const accountCandidate = newUser as typeof newUser & {
            username?: unknown;
          };
          const parsed = signupIdentitySchema.safeParse({
            email: accountCandidate.email,
            username: accountCandidate.username,
            displayName: accountCandidate.name,
          });

          if (!parsed.success) {
            throw new APIError("BAD_REQUEST", {
              message: "Invalid account details.",
            });
          }

          return {
            data: {
              ...newUser,
              email: parsed.data.email,
              name: parsed.data.displayName,
              username: parsed.data.username,
            },
          };
        },
      },
    },
  },
  user: {
    additionalFields: {
      about: {
        type: "string",
        required: false,
        input: false,
      },
      imageObjectKey: {
        type: "string",
        required: false,
        input: false,
        returned: false,
      },
      headerObjectKey: {
        type: "string",
        required: false,
        input: false,
        returned: false,
      },
    },
  },
  disabledPaths: [
    "/sign-in/username",
    "/is-username-available",
    "/update-user",
  ],
  trustedOrigins: [appUrl],
  plugins: [
    username({
      minUsernameLength: 3,
      maxUsernameLength: 24,
      usernameValidator: (value) => /^[a-z0-9_]+$/.test(value),
      validationOrder: {
        username: "post-normalization",
      },
    }),
  ],
  telemetry: {
    enabled: false,
  },
});
