import Image from "next/image";
import Link from "next/link";

import type { PublicProfile } from "@/lib/public-profile";

type PublicProfileViewProps = {
  profile: PublicProfile;
  isOwner: boolean;
};

function joinedLabel(joinedAt: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(joinedAt));
}

export function PublicProfileView({
  profile,
  isOwner,
}: PublicProfileViewProps) {
  return (
    <main className="public-profile">
      <section aria-labelledby="profile-name" className="profile-identity">
        <div className="profile-header-image">
          <Image
            alt=""
            fill
            priority
            sizes="(max-width: 1040px) 100vw, 1040px"
            src={profile.headerUrl}
          />
        </div>
        <div className="profile-identity__body">
          <div className="profile-avatar">
            <Image
              alt={`Default avatar for ${profile.displayName}`}
              fill
              sizes="132px"
              src={profile.avatarUrl}
            />
          </div>
          <div className="profile-title">
            <p className="section-kicker">LeagueWatch profile</p>
            <h1 id="profile-name">{profile.displayName}</h1>
            <p className="profile-handle">@{profile.username}</p>
          </div>
          {isOwner ? (
            <Link className="profile-edit-link" href="/settings/profile">
              Edit profile
            </Link>
          ) : null}
        </div>
      </section>

      <section aria-labelledby="about-heading" className="profile-about">
        <div className="profile-section-heading">
          <div>
            <p className="section-kicker">Off the field</p>
            <h2 id="about-heading">About</h2>
          </div>
          <p>Joined {joinedLabel(profile.joinedAt)}</p>
        </div>
        <p className={profile.about ? undefined : "profile-about__empty"}>
          {profile.about || "No bio added yet."}
        </p>
      </section>

      <section aria-labelledby="coming-heading" className="profile-coming">
        <p className="section-kicker">Personalization</p>
        <h2 id="coming-heading">Your season starts here</h2>
        <p>
          Favorite teams and personal matchup recommendations are the next
          account features coming to LeagueWatch.
        </p>
        <Link href="/">Explore this week&apos;s rankings</Link>
      </section>
    </main>
  );
}
