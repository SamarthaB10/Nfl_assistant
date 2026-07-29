"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import {
  type AuthActionResult,
  signUpWithEmail,
} from "@/lib/auth-actions";
import {
  type SignupInput,
  signupSchema,
} from "@/lib/profile-validation";

type SignupFormProps = {
  submitSignup?: (input: SignupInput) => Promise<AuthActionResult>;
  onSuccess?: (username: string) => void;
};

type FieldErrors = Partial<Record<keyof SignupInput, string>>;

export function SignupForm({
  submitSignup = signUpWithEmail,
  onSuccess,
}: SignupFormProps) {
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFieldErrors({});
    setFormError("");

    const form = new FormData(event.currentTarget);
    const parsed = signupSchema.safeParse({
      email: form.get("email"),
      username: form.get("username"),
      displayName: form.get("displayName"),
      password: form.get("password"),
    });

    if (!parsed.success) {
      const errors: FieldErrors = {};
      for (const issue of parsed.error.issues) {
        const field = issue.path[0] as keyof SignupInput | undefined;
        if (field && !errors[field]) {
          errors[field] = issue.message;
        }
      }
      setFieldErrors(errors);
      return;
    }

    setIsSubmitting(true);
    const result = await submitSignup(parsed.data);
    setIsSubmitting(false);

    if (result.error) {
      setFormError(
        result.error.status === 429
          ? "Too many attempts. Wait a moment and try again."
          : "An account already uses that email or username.",
      );
      return;
    }

    if (onSuccess) {
      onSuccess(parsed.data.username);
      return;
    }

    window.location.assign(`/u/${parsed.data.username}`);
  }

  return (
    <form
      aria-label="Create account"
      className="auth-form"
      noValidate
      onSubmit={handleSubmit}
    >
      <AuthField
        autoComplete="email"
        error={fieldErrors.email}
        label="Email"
        name="email"
        placeholder="you@example.com"
        type="email"
      />
      <AuthField
        autoComplete="username"
        error={fieldErrors.username}
        hint="3-24 lowercase letters, numbers, or underscores"
        label="Username"
        name="username"
        placeholder="sunday_fan"
      />
      <AuthField
        autoComplete="name"
        error={fieldErrors.displayName}
        label="Display name"
        name="displayName"
        placeholder="Sunday Fan"
      />
      <AuthField
        autoComplete="new-password"
        error={fieldErrors.password}
        hint="Use at least 8 characters"
        label="Password"
        name="password"
        type="password"
      />
      {formError ? (
        <p className="form-message form-message--error" role="alert">
          {formError}
        </p>
      ) : null}
      <button className="auth-submit" disabled={isSubmitting} type="submit">
        {isSubmitting ? "Creating account…" : "Create account"}
      </button>
      <p className="auth-switch">
        Already have an account? <Link href="/login">Log in</Link>
      </p>
    </form>
  );
}

type AuthFieldProps = {
  autoComplete: string;
  error?: string;
  hint?: string;
  label: string;
  name: string;
  placeholder?: string;
  type?: string;
};

function AuthField({
  autoComplete,
  error,
  hint,
  label,
  name,
  placeholder,
  type = "text",
}: AuthFieldProps) {
  const descriptionId = `${name}-description`;

  return (
    <div className="auth-field">
      <label htmlFor={name}>{label}</label>
      <input
        aria-describedby={hint || error ? descriptionId : undefined}
        aria-invalid={Boolean(error)}
        autoComplete={autoComplete}
        id={name}
        name={name}
        placeholder={placeholder}
        type={type}
      />
      {error ? (
        <span className="auth-field__error" id={descriptionId}>
          {error}
        </span>
      ) : hint ? (
        <span className="auth-field__hint" id={descriptionId}>
          {hint}
        </span>
      ) : null}
    </div>
  );
}
