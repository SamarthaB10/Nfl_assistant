"use client";

import Link from "next/link";

import { authClient } from "@/lib/auth-client";

type AccountUser = {
  displayName: string;
  username: string;
};

type AccountNavViewProps = {
  user: AccountUser | null;
  onSignOut: () => void;
};

export function AccountNavView({
  user,
  onSignOut,
}: AccountNavViewProps) {
  if (!user) {
    return (
      <nav aria-label="Account" className="account-nav">
        <Link className="account-nav__login" href="/login">
          Log in
        </Link>
        <Link className="account-nav__signup" href="/signup">
          Sign up
        </Link>
      </nav>
    );
  }

  return (
    <nav aria-label="Account" className="account-nav">
      <Link
        aria-label={`${user.displayName} profile`}
        className="account-nav__profile"
        href={`/u/${user.username}`}
      >
        <span aria-hidden="true" className="account-nav__avatar">
          {user.displayName.slice(0, 1).toUpperCase()}
        </span>
        <span className="account-nav__name">{user.displayName}</span>
      </Link>
      <button
        className="account-nav__logout"
        onClick={onSignOut}
        type="button"
      >
        Sign out
      </button>
    </nav>
  );
}

export function AccountNav() {
  const { data: session, isPending } = authClient.useSession();

  if (isPending) {
    return (
      <div
        aria-label="Loading account"
        className="account-nav account-nav--loading"
        role="status"
      />
    );
  }

  const username = session?.user.username;
  const user =
    session && username
      ? {
          displayName: session.user.name,
          username,
        }
      : null;

  return (
    <AccountNavView
      onSignOut={async () => {
        await authClient.signOut();
        window.location.assign("/");
      }}
      user={user}
    />
  );
}
