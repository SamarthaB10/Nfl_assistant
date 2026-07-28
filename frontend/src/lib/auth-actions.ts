"use client";

import type { LoginInput, SignupInput } from "./profile-validation";
import { authClient } from "./auth-client";

export type AuthActionError = {
  status?: number;
  message?: string;
};

export type AuthActionResult = {
  error: AuthActionError | null;
};

export async function signUpWithEmail(
  input: SignupInput,
): Promise<AuthActionResult> {
  const { error } = await authClient.signUp.email({
    email: input.email,
    name: input.displayName,
    password: input.password,
    username: input.username,
  });

  return {
    error: error
      ? { status: error.status, message: error.message }
      : null,
  };
}

export async function logInWithEmail(
  input: LoginInput,
): Promise<AuthActionResult> {
  const { error } = await authClient.signIn.email({
    email: input.email,
    password: input.password,
  });

  return {
    error: error
      ? { status: error.status, message: error.message }
      : null,
  };
}
