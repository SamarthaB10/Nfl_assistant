"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import {
  type ProfileUpdateInput,
  profileUpdateSchema,
} from "@/lib/profile-validation";

type EditableProfile = {
  username: string;
  displayName: string;
  about: string | null;
};

type ProfileSubmitResult = {
  error: string | null;
};

type ProfileEditFormProps = {
  profile: EditableProfile;
  submitProfile?: (input: ProfileUpdateInput) => Promise<ProfileSubmitResult>;
  onSuccess?: () => void;
};

async function updateProfile(
  input: ProfileUpdateInput,
): Promise<ProfileSubmitResult> {
  const response = await fetch("/api/profile", {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
  });

  if (!response.ok) {
    return {
      error:
        response.status === 401
          ? "Your session expired. Log in and try again."
          : "Your profile could not be saved.",
    };
  }

  return { error: null };
}

export function ProfileEditForm({
  profile,
  submitProfile = updateProfile,
  onSuccess,
}: ProfileEditFormProps) {
  const [about, setAbout] = useState(profile.about ?? "");
  const [fieldError, setFieldError] = useState("");
  const [formError, setFormError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFieldError("");
    setFormError("");

    const form = new FormData(event.currentTarget);
    const parsed = profileUpdateSchema.safeParse({
      displayName: form.get("displayName"),
      about: form.get("about"),
    });

    if (!parsed.success) {
      const aboutIssue = parsed.error.issues.some(
        (issue) => issue.path[0] === "about",
      );
      setFieldError(
        aboutIssue
          ? "About must contain at most 300 characters."
          : "Display name must contain between 1 and 50 characters.",
      );
      return;
    }

    setIsSubmitting(true);
    const result = await submitProfile(parsed.data);
    setIsSubmitting(false);

    if (result.error) {
      setFormError(result.error);
      return;
    }

    if (onSuccess) {
      onSuccess();
      return;
    }

    window.location.assign(`/u/${profile.username}`);
  }

  return (
    <form
      aria-label="Edit profile"
      className="profile-form"
      noValidate
      onSubmit={handleSubmit}
    >
      <div className="profile-form__handle">
        <span>Public handle</span>
        <strong>@{profile.username}</strong>
        <small>Usernames cannot be changed in this version.</small>
      </div>
      <div className="auth-field">
        <label htmlFor="profile-display-name">Display name</label>
        <input
          defaultValue={profile.displayName}
          id="profile-display-name"
          maxLength={50}
          name="displayName"
        />
      </div>
      <div className="auth-field">
        <div className="profile-form__label-row">
          <label htmlFor="profile-about">About</label>
          <span>{about.length}/300</span>
        </div>
        <textarea
          id="profile-about"
          maxLength={301}
          name="about"
          onChange={(event) => setAbout(event.currentTarget.value)}
          rows={6}
          value={about}
        />
      </div>
      {fieldError ? (
        <p className="form-message form-message--error" role="alert">
          {fieldError}
        </p>
      ) : null}
      {formError ? (
        <p className="form-message form-message--error" role="alert">
          {formError}
        </p>
      ) : null}
      <div className="profile-form__actions">
        <button className="auth-submit" disabled={isSubmitting} type="submit">
          {isSubmitting ? "Saving…" : "Save profile"}
        </button>
        <Link href={`/u/${profile.username}`}>Cancel</Link>
      </div>
    </form>
  );
}
