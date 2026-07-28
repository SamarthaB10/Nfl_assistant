import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ProfileEditForm } from "./profile-edit-form";

describe("ProfileEditForm", () => {
  it("loads the owner's current public fields", () => {
    render(
      <ProfileEditForm
        profile={{
          username: "sunday_fan",
          displayName: "Sunday Fan",
          about: "Watching every divisional matchup.",
        }}
      />,
    );

    expect(screen.getByLabelText("Display name")).toHaveValue("Sunday Fan");
    expect(screen.getByLabelText("About")).toHaveValue(
      "Watching every divisional matchup.",
    );
    expect(screen.getByText("@sunday_fan")).toBeInTheDocument();
  });

  it("blocks an About section over 300 characters", async () => {
    const submitProfile = vi.fn();
    render(
      <ProfileEditForm
        profile={{
          username: "sunday_fan",
          displayName: "Sunday Fan",
          about: "",
        }}
        submitProfile={submitProfile}
      />,
    );

    fireEvent.change(screen.getByLabelText("About"), {
      target: { value: "x".repeat(301) },
    });
    fireEvent.submit(screen.getByRole("form", { name: "Edit profile" }));

    expect(
      await screen.findByText("About must contain at most 300 characters."),
    ).toBeInTheDocument();
    expect(submitProfile).not.toHaveBeenCalled();
  });

  it("submits trimmed profile fields and reports success", async () => {
    const submitProfile = vi.fn().mockResolvedValue({ error: null });
    const onSuccess = vi.fn();
    render(
      <ProfileEditForm
        onSuccess={onSuccess}
        profile={{
          username: "sunday_fan",
          displayName: "Sunday Fan",
          about: "",
        }}
        submitProfile={submitProfile}
      />,
    );

    fireEvent.change(screen.getByLabelText("Display name"), {
      target: { value: " Sunday Ticket " },
    });
    fireEvent.change(screen.getByLabelText("About"), {
      target: { value: " NFC North watcher. " },
    });
    fireEvent.submit(screen.getByRole("form", { name: "Edit profile" }));

    await waitFor(() =>
      expect(submitProfile).toHaveBeenCalledWith({
        displayName: "Sunday Ticket",
        about: "NFC North watcher.",
      }),
    );
    expect(onSuccess).toHaveBeenCalled();
  });
});
