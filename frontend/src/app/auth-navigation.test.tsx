import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import LoginPage from "./login/page";
import SignupPage from "./signup/page";

describe("authentication page navigation", () => {
  it.each([
    ["login", LoginPage],
    ["signup", SignupPage],
  ])("links from the %s page to the LeagueWatch home page", (_page, Page) => {
    render(<Page />);

    expect(
      screen.getByRole("link", { name: "LeagueWatch home" }),
    ).toHaveAttribute("href", "/");
  });
});
