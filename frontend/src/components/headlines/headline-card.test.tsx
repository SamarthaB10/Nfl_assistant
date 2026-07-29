import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { HeadlineItem } from "@/lib/headlines";

import { HeadlineCard } from "./headline-card";

const headline: HeadlineItem = {
  id: 1,
  source: "ESPN",
  title: "Falcons open training camp with a revamped offense",
  author: "NFL Nation",
  excerpt: "Atlanta begins a new season with a different offensive identity.",
  url: "https://www.espn.com/nfl/story/_/id/1/falcons-camp",
  imageUrl: null,
  teamCodes: ["ATL"],
  publishedAt: "2026-07-29T19:45:50Z",
};

describe("HeadlineCard", () => {
  it("presents each tagged team with a prominent logo and accessible name", () => {
    render(<HeadlineCard headline={headline} />);

    const teamBadge = screen.getByRole("img", { name: "Atlanta Falcons" });
    const logo = teamBadge.querySelector("img");

    expect(teamBadge).toHaveAttribute("title", "Atlanta Falcons");
    expect(logo).not.toBeNull();
    expect(logo).toHaveAttribute("width", "34");
    expect(logo).toHaveAttribute("height", "34");
  });

  it("shows the NFL shield when no team can be classified", () => {
    render(
      <HeadlineCard
        headline={{
          ...headline,
          title: "League owners approve a new regular-season policy",
          teamCodes: [],
        }}
      />,
    );

    const leagueBadge = screen.getByRole("img", { name: "NFL" });
    const logo = leagueBadge.querySelector("img");

    expect(leagueBadge).toHaveAttribute("title", "NFL");
    expect(leagueBadge).toHaveClass("headline-card__team");
    expect(decodeURIComponent(logo?.getAttribute("src") ?? "")).toContain(
      "https://a.espncdn.com/i/teamlogos/leagues/500/nfl.png",
    );
  });

  it("styles headline team tags as high-contrast gold badges", () => {
    const styles = readFileSync(resolve("src/app/globals.css"), "utf8");
    const badgeStyles = styles.slice(
      styles.indexOf(".headline-card__teams"),
      styles.indexOf(".headline-card__arrow"),
    );

    expect(badgeStyles).toMatch(
      /\.headline-card__team\s*\{[\s\S]*?min-width:\s*44px;[\s\S]*?height:\s*38px;/,
    );
    expect(badgeStyles).toMatch(/background:[\s\S]*linear-gradient/);
    expect(badgeStyles).toContain("#ffd966");
    expect(badgeStyles).toContain("#171300");
  });
});
