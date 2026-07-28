import type { Metadata } from "next";
import { headers } from "next/headers";
import { notFound, redirect } from "next/navigation";

import { ProfileEditForm } from "@/components/profile/profile-edit-form";
import { auth } from "@/lib/auth";
import { getEditableProfile } from "@/lib/profiles";

export const metadata: Metadata = {
  title: "Edit profile | LeagueWatch",
};

export const dynamic = "force-dynamic";

export default async function ProfileSettingsPage() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) {
    redirect("/login");
  }

  const profile = await getEditableProfile(session.user.id);
  if (!profile) {
    notFound();
  }

  return (
    <main className="profile-settings">
      <section className="profile-settings__intro">
        <p className="section-kicker">Account settings</p>
        <h1>Edit profile</h1>
        <p>
          These fields appear publicly. Your login email remains private and
          cannot be edited here.
        </p>
      </section>
      <section aria-labelledby="public-details-heading" className="auth-panel">
        <div className="auth-panel__heading">
          <span aria-hidden="true">03</span>
          <div>
            <p>Public details</p>
            <h2 id="public-details-heading">Your identity</h2>
          </div>
        </div>
        <ProfileEditForm profile={profile} />
      </section>
    </main>
  );
}
