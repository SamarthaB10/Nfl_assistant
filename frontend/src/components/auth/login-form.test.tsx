import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { LoginForm } from "./login-form";

describe("LoginForm", () => {
  it("uses email rather than username as the login identifier", () => {
    render(<LoginForm />);

    expect(screen.getByLabelText("Email")).toHaveAttribute(
      "autocomplete",
      "email",
    );
    expect(screen.queryByLabelText("Username")).not.toBeInTheDocument();
    expect(screen.getByText("New to Drizzle?")).toBeInTheDocument();
  });

  it("shows a generic message when credentials are rejected", async () => {
    const submitLogin = vi.fn().mockResolvedValue({
      error: { status: 401, message: "specific provider error" },
    });
    render(<LoginForm submitLogin={submitLogin} />);

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "fan@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "wrongpassword" },
    });
    fireEvent.submit(screen.getByRole("form", { name: "Log in" }));

    expect(
      await screen.findByText("Email or password is incorrect."),
    ).toBeInTheDocument();
    expect(screen.queryByText("specific provider error")).not.toBeInTheDocument();
  });

  it("reports success after valid credentials", async () => {
    const submitLogin = vi.fn().mockResolvedValue({ error: null });
    const onSuccess = vi.fn();
    render(<LoginForm onSuccess={onSuccess} submitLogin={submitLogin} />);

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: " FAN@Example.com " },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "watchfootball" },
    });
    fireEvent.submit(screen.getByRole("form", { name: "Log in" }));

    await waitFor(() =>
      expect(submitLogin).toHaveBeenCalledWith({
        email: "fan@example.com",
        password: "watchfootball",
      }),
    );
    expect(onSuccess).toHaveBeenCalled();
  });
});
