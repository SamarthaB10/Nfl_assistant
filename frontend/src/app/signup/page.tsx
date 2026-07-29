import type { Metadata } from "next";
import Link from "next/link";

import { SignupForm } from "@/components/auth/signup-form";

export const metadata: Metadata = {
  title: "Create account | LeagueWatch",
  description: "Create a LeagueWatch account and public NFL profile.",
};

export default function SignupPage() {
  return (
    <main className="auth-page">
      <section className="auth-page__intro">
        <Link className="auth-home-link" href="/">
          <span aria-hidden="true">←</span>
          LeagueWatch home
        </Link>
        <p className="section-kicker">Your season. Your profile.</p>
        <h1>Join LeagueWatch</h1>
        <p>
          Claim a public handle now. Your account will power personalized NFL
          viewing recommendations as LeagueWatch grows.
        </p>
      </section>
      <section aria-labelledby="signup-title" className="auth-panel">
        <div className="auth-panel__heading">
          <span aria-hidden="true">01</span>
          <div>
            <p>New account</p>
            <h2 id="signup-title">Create your profile</h2>
          </div>
        </div>
        <SignupForm />
      </section>
    </main>
  );
}
