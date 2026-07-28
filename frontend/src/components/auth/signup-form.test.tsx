import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SignupForm } from "./signup-form";

describe("SignupForm", () => {
  it("labels every account field", () => {
    render(<SignupForm />);

    expect(screen.getByLabelText("Email")).toHaveAttribute("type", "email");
    expect(screen.getByLabelText("Username")).toHaveAttribute(
      "autocomplete",
      "username",
    );
    expect(screen.getByLabelText("Display name")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toHaveAttribute(
      "autocomplete",
      "new-password",
    );
  });

  it("blocks invalid public handles before sending a signup request", async () => {
    const submitSignup = vi.fn();
    render(<SignupForm submitSignup={submitSignup} />);

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "fan@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Username"), {
      target: { value: "bad-handle" },
    });
    fireEvent.change(screen.getByLabelText("Display name"), {
      target: { value: "Sunday Fan" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "watchfootball" },
    });
    fireEvent.submit(screen.getByRole("form", { name: "Create account" }));

    expect(
      await screen.findByText(
        "Use only lowercase letters, numbers, and underscores.",
      ),
    ).toBeInTheDocument();
    expect(submitSignup).not.toHaveBeenCalled();
  });

  it("submits normalized account data and reports success", async () => {
    const submitSignup = vi.fn().mockResolvedValue({ error: null });
    const onSuccess = vi.fn();
    render(
      <SignupForm onSuccess={onSuccess} submitSignup={submitSignup} />,
    );

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: " FAN@Example.com " },
    });
    fireEvent.change(screen.getByLabelText("Username"), {
      target: { value: " SUNDAY_FAN " },
    });
    fireEvent.change(screen.getByLabelText("Display name"), {
      target: { value: " Sunday Fan " },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "watchfootball" },
    });
    fireEvent.submit(screen.getByRole("form", { name: "Create account" }));

    await waitFor(() =>
      expect(submitSignup).toHaveBeenCalledWith({
        email: "fan@example.com",
        username: "sunday_fan",
        displayName: "Sunday Fan",
        password: "watchfootball",
      }),
    );
    expect(onSuccess).toHaveBeenCalledWith("sunday_fan");
  });
});
