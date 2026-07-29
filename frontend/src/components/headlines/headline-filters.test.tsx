import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { HeadlineFilters } from "./headline-filters";

function renderFilters(
  overrides: Partial<React.ComponentProps<typeof HeadlineFilters>> = {},
) {
  const props: React.ComponentProps<typeof HeadlineFilters> = {
    loading: false,
    onSourceChange: vi.fn(),
    onSubmit: vi.fn(),
    onTeamChange: vi.fn(),
    source: "ALL",
    team: "ALL",
    ...overrides,
  };

  render(<HeadlineFilters {...props} />);
  return props;
}

describe("HeadlineFilters", () => {
  it("renders branded publisher and team pickers instead of native selects", () => {
    renderFilters();

    expect(
      screen.getByRole("combobox", { name: "Publisher: All publishers" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("combobox", { name: "Team: All NFL teams" }),
    ).toBeInTheDocument();
    expect(document.querySelector("select")).not.toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("combobox", { name: "Team: All NFL teams" }),
    );

    const falcons = screen.getByRole("option", { name: "Atlanta Falcons" });
    expect(falcons).toBeInTheDocument();
    expect(falcons.querySelector("img")).toHaveAttribute(
      "src",
      expect.stringContaining("atl.png"),
    );
  });

  it("selects filters with the keyboard and closes on Escape", () => {
    const props = renderFilters();
    const publisher = screen.getByRole("combobox", {
      name: "Publisher: All publishers",
    });

    fireEvent.keyDown(publisher, { key: "ArrowDown" });
    expect(screen.getByRole("listbox", { name: "Publisher" })).toBeInTheDocument();

    fireEvent.keyDown(screen.getByRole("listbox", { name: "Publisher" }), {
      key: "ArrowDown",
    });
    fireEvent.keyDown(screen.getByRole("listbox", { name: "Publisher" }), {
      key: "Enter",
    });
    expect(props.onSourceChange).toHaveBeenCalledWith("ESPN");

    fireEvent.click(
      screen.getByRole("combobox", { name: "Team: All NFL teams" }),
    );
    fireEvent.keyDown(screen.getByRole("listbox", { name: "Team" }), {
      key: "Escape",
    });
    expect(
      screen.queryByRole("listbox", { name: "Team" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("combobox", { name: "Team: All NFL teams" }),
    ).toHaveFocus();
  });
});
