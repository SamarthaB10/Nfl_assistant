import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { PublicProfile } from "@/lib/public-profile";

import { PublicProfileView } from "./public-profile";

const profile: PublicProfile = {
  username: "sunday_fan",
  displayName: "Sunday Fan",
  about: "Watching every divisional matchup.",
  avatarUrl: "/profile-default-avatar.svg",
  headerUrl: "/profile-default-header.svg",
  joinedAt: "2025-09-04T12:00:00.000Z",
};

describe("PublicProfileView", () => {
  it("renders the approved public identity without community metrics", () => {
    render(<PublicProfileView isOwner={false} profile={profile} />);

    expect(
      screen.getByRole("heading", { name: "Sunday Fan" }),
    ).toBeInTheDocument();
    expect(screen.getByText("@sunday_fan")).toBeInTheDocument();
    expect(
      screen.getByText("Watching every divisional matchup."),
    ).toBeInTheDocument();
    expect(screen.getByText("Joined September 2025")).toBeInTheDocument();
    expect(screen.queryByText(/karma/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/followers/i)).not.toBeInTheDocument();
  });

  it("shows profile editing only to the owner", () => {
    const { rerender } = render(
      <PublicProfileView isOwner={false} profile={profile} />,
    );
    expect(
      screen.queryByRole("link", { name: "Edit profile" }),
    ).not.toBeInTheDocument();

    rerender(<PublicProfileView isOwner profile={profile} />);
    expect(screen.getByRole("link", { name: "Edit profile" })).toHaveAttribute(
      "href",
      "/settings/profile",
    );
  });

  it("provides a meaningful empty About state", () => {
    render(
      <PublicProfileView
        isOwner={false}
        profile={{ ...profile, about: null }}
      />,
    );

    expect(screen.getByText("No bio added yet.")).toBeInTheDocument();
  });
});
