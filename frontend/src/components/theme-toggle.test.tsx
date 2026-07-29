import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { ThemeToggle } from "./theme-toggle";

beforeEach(() => {
  window.localStorage.clear();
  delete document.documentElement.dataset.theme;
});

describe("ThemeToggle", () => {
  it("defaults to dark mode and lets the user select light mode", () => {
    render(<ThemeToggle />);

    const toggle = screen.getByRole("button", {
      name: "Switch to light mode",
    });

    expect(document.documentElement).toHaveAttribute("data-theme", "dark");

    fireEvent.click(toggle);

    expect(document.documentElement).toHaveAttribute("data-theme", "light");
    expect(window.localStorage.getItem("leaguewatch-theme")).toBe("light");
    expect(
      screen.getByRole("button", { name: "Switch to dark mode" }),
    ).toBeInTheDocument();
  });

  it("restores the saved light mode preference", async () => {
    window.localStorage.setItem("leaguewatch-theme", "light");

    render(<ThemeToggle />);

    await waitFor(() => {
      expect(document.documentElement).toHaveAttribute("data-theme", "light");
    });
    expect(
      screen.getByRole("button", { name: "Switch to dark mode" }),
    ).toBeInTheDocument();
  });
});
