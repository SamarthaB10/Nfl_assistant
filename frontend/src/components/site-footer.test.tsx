import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SiteFooterView } from "./site-footer";

describe("SiteFooter", () => {
  it("shows live-news attribution on the headlines page", () => {
    render(<SiteFooterView pathname="/headlines" />);

    expect(screen.getByText("Current NFL coverage · Updated hourly")).toBeInTheDocument();
    expect(screen.getByText(/ESPN, CBS Sports, and FOX Sports/)).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Watch rating color guide"),
    ).not.toBeInTheDocument();
  });

  it("keeps the watch-rating guide on matchup pages", () => {
    render(<SiteFooterView pathname="/" />);

    expect(screen.getByLabelText("Watch rating color guide")).toBeInTheDocument();
    expect(screen.getByText("2025 regular season · Live model v6")).toBeInTheDocument();
  });
});
