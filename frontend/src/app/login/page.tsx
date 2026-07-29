import type { Metadata } from "next";
import Link from "next/link";

import { LoginForm } from "@/components/auth/login-form";

export const metadata: Metadata = {
  title: "Log in | Drizzle",
  description: "Log in to your Drizzle NFL profile.",
};

export default function LoginPage() {
  return (
    <main className="auth-page">
      <section className="auth-page__intro">
        <Link className="auth-home-link" href="/">
          <span aria-hidden="true">←</span>
          Drizzle home
        </Link>
        <div className="auth-welcome">
          <svg
            aria-hidden="true"
            className="auth-welcome__mark"
            focusable="false"
            viewBox="0 0 72 52"
          >
            <rect
              className="brand-mark__tile"
              x="1"
              y="1"
              width="70"
              height="50"
              rx="12"
            />
            <rect
              className="brand-mark__field"
              x="7"
              y="7"
              width="58"
              height="38"
              rx="8"
            />
            <path
              className="brand-mark__stroke"
              d="M16 14v24M16 14c13-2 20 2 20 12s-7 14-20 12M41 15c7-2 13-2 18 0-6 5-12 10-16 15-3 3-5 6-6 8 8 2 16 2 22-1"
            />
          </svg>
          <h1>Welcome back</h1>
        </div>
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
