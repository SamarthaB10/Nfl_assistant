import type { Metadata } from "next";

import { LoginForm } from "@/components/auth/login-form";

export const metadata: Metadata = {
  title: "Log in | LeagueWatch",
  description: "Log in to your LeagueWatch NFL profile.",
};

export default function LoginPage() {
  return (
    <main className="auth-page">
      <section className="auth-page__intro">
        <p className="section-kicker">Back for another week.</p>
        <h1>Welcome back</h1>
        <p>
          Log in with your private email. Your public profile keeps the handle
          and name you chose.
        </p>
      </section>
      <section aria-labelledby="login-title" className="auth-panel">
        <div className="auth-panel__heading">
          <span aria-hidden="true">02</span>
          <div>
            <p>Existing account</p>
            <h2 id="login-title">Log in</h2>
          </div>
        </div>
        <LoginForm />
      </section>
    </main>
  );
}
