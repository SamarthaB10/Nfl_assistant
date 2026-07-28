import type { Metadata } from "next";
import { headers } from "next/headers";
import { notFound } from "next/navigation";

import { PublicProfileView } from "@/components/profile/public-profile";
import { auth } from "@/lib/auth";
import { getPublicProfile } from "@/lib/profiles";

export const dynamic = "force-dynamic";

type ProfilePageProps = {
  params: Promise<{ username: string }>;
};

export async function generateMetadata({
  params,
}: ProfilePageProps): Promise<Metadata> {
  const { username } = await params;
  const profile = await getPublicProfile(username);

  return profile
    ? {
        title: `${profile.displayName} (@${profile.username}) | LeagueWatch`,
        description:
          profile.about || `View @${profile.username} on LeagueWatch.`,
      }
    : {
        title: "Profile not found | LeagueWatch",
      };
}

export default async function ProfilePage({ params }: ProfilePageProps) {
  const { username } = await params;
  const [profile, session] = await Promise.all([
    getPublicProfile(username),
    auth.api.getSession({ headers: await headers() }),
  ]);

  if (!profile) {
    notFound();
  }

  return (
    <PublicProfileView
      isOwner={session?.user.id != null && session.user.username === profile.username}
      profile={profile}
    />
  );
}
