import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AccountNavView } from "./account-nav";

describe("AccountNavView", () => {
  it("offers login and signup when no account is active", () => {
    render(<AccountNavView onSignOut={vi.fn()} user={null} />);

    expect(screen.getByRole("link", { name: "Log in" })).toHaveAttribute(
      "href",
      "/login",
    );
    expect(screen.getByRole("link", { name: "Sign up" })).toHaveAttribute(
      "href",
      "/signup",
    );
  });

  it("links a signed-in user to the public profile without exposing email", () => {
    const onSignOut = vi.fn();
    render(
      <AccountNavView
        onSignOut={onSignOut}
        user={{ displayName: "Sunday Fan", username: "sunday_fan" }}
      />,
    );

    expect(screen.getByRole("link", { name: "Sunday Fan profile" })).toHaveAttribute(
      "href",
      "/u/sunday_fan",
    );
    expect(screen.queryByText(/@example.com/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Sign out" }));
    expect(onSignOut).toHaveBeenCalled();
  });
});
