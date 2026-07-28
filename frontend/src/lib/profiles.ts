import "server-only";

import { eq } from "drizzle-orm";

import { db } from "@/db";
import { user } from "@/db/schema";

import type { ProfileUpdateInput } from "./profile-validation";
import { publicUsernameSchema } from "./profile-validation";
import { type PublicProfile, toPublicProfile } from "./public-profile";

const publicProfileSelection = {
  username: user.username,
  name: user.name,
  about: user.about,
  imageObjectKey: user.imageObjectKey,
  headerObjectKey: user.headerObjectKey,
  createdAt: user.createdAt,
};

export async function getPublicProfile(
  rawUsername: string,
): Promise<PublicProfile | null> {
  const parsedUsername = publicUsernameSchema.safeParse(rawUsername);
  if (!parsedUsername.success) {
    return null;
  }

  const [record] = await db
    .select(publicProfileSelection)
    .from(user)
    .where(eq(user.username, parsedUsername.data))
    .limit(1);

  return record ? toPublicProfile(record) : null;
}

export async function getEditableProfile(userId: string) {
  const [record] = await db
    .select({
      username: user.username,
      displayName: user.name,
      about: user.about,
    })
    .from(user)
    .where(eq(user.id, userId))
    .limit(1);

  return record ?? null;
}

export async function updateOwnProfile(
  userId: string,
  input: ProfileUpdateInput,
): Promise<PublicProfile | null> {
  const [updated] = await db
    .update(user)
    .set({
      name: input.displayName,
      about: input.about || null,
      updatedAt: new Date(),
    })
    .where(eq(user.id, userId))
    .returning(publicProfileSelection);

  return updated ? toPublicProfile(updated) : null;
}
