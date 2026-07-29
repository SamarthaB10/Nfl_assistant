"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import {
  type AuthActionResult,
  logInWithEmail,
} from "@/lib/auth-actions";
import { type LoginInput, loginSchema } from "@/lib/profile-validation";

type LoginFormProps = {
  submitLogin?: (input: LoginInput) => Promise<AuthActionResult>;
  onSuccess?: () => void;
};

export function LoginForm({
  submitLogin = logInWithEmail,
  onSuccess,
}: LoginFormProps) {
  const [formError, setFormError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError("");

    const form = new FormData(event.currentTarget);
    const parsed = loginSchema.safeParse({
      email: form.get("email"),
      password: form.get("password"),
    });

    if (!parsed.success) {
      setFormError("Enter a valid email and password.");
      return;
    }

    setIsSubmitting(true);
    const result = await submitLogin(parsed.data);
    setIsSubmitting(false);

    if (result.error) {
      setFormError(
        result.error.status === 429
          ? "Too many attempts. Wait a moment and try again."
          : "Email or password is incorrect.",
      );
      return;
    }

    if (onSuccess) {
      onSuccess();
      return;
    }

    window.location.assign("/");
  }

  return (
    <form
      aria-label="Log in"
      className="auth-form"
      noValidate
      onSubmit={handleSubmit}
    >
      <div className="auth-field">
        <label htmlFor="login-email">Email</label>
        <input
          autoComplete="email"
          id="login-email"
          name="email"
          placeholder="you@example.com"
          type="email"
        />
      </div>
      <div className="auth-field">
        <label htmlFor="login-password">Password</label>
        <input
          autoComplete="current-password"
          id="login-password"
          name="password"
          type="password"
        />
      </div>
      {formError ? (
        <p className="form-message form-message--error" role="alert">
          {formError}
        </p>
      ) : null}
      <button className="auth-submit" disabled={isSubmitting} type="submit">
        {isSubmitting ? "Logging in…" : "Log in"}
      </button>
      <p className="auth-switch">
        New to Drizzle? <Link href="/signup">Create an account</Link>
      </p>
    </form>
  );
}
