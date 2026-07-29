import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SiteNavigationView } from "./site-navigation";

describe("SiteNavigation", () => {
  it("links to matchup rankings and the current headlines feed", () => {
    render(<SiteNavigationView pathname="/" />);

    expect(screen.getByRole("link", { name: "Matchups" })).toHaveAttribute(
      "href",
      "/",
    );
    expect(screen.getByRole("link", { name: "LIVE NEWS" })).toHaveAttribute(
      "href",
      "/headlines",
    );
    expect(screen.getByRole("link", { name: "Matchups" })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  it("marks the headlines tab as the current page", () => {
    render(<SiteNavigationView pathname="/headlines" />);

    expect(screen.getByRole("link", { name: "LIVE NEWS" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Matchups" })).not.toHaveAttribute(
      "aria-current",
    );
  });
});
