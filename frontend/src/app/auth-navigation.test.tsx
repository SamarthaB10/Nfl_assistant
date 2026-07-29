import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import LoginPage from "./login/page";
import SignupPage from "./signup/page";

describe("authentication page navigation", () => {
  it.each([
    ["login", LoginPage],
    ["signup", SignupPage],
  ])("links from the %s page to the Drizzle home page", (_page, Page) => {
    render(<Page />);

    expect(
      screen.getByRole("link", { name: "Drizzle home" }),
    ).toHaveAttribute("href", "/");
  });

  it("uses the Drizzle brand on the signup page", () => {
    render(<SignupPage />);

    expect(
      screen.getByRole("heading", { name: "Join Drizzle" }),
    ).toBeInTheDocument();
  });

  it("pairs the Drizzle mark with the welcome heading without the old kicker", () => {
    const { container } = render(<LoginPage />);

    expect(
      screen.getByRole("heading", { name: "Welcome back" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByText("Back for another week."),
    ).not.toBeInTheDocument();
    expect(container.querySelector(".auth-welcome__mark")).not.toBeNull();
  });
});
