"use client";

import { useEffect, useState } from "react";

type Theme = "dark" | "light";

const THEME_STORAGE_KEY = "leaguewatch-theme";

function applyTheme(theme: Theme) {
  document.documentElement.dataset.theme = theme;
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("dark");

  useEffect(() => {
    const savedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
    const initialTheme: Theme = savedTheme === "light" ? "light" : "dark";

    applyTheme(initialTheme);
    setTheme(initialTheme);
  }, []);

  function selectTheme(nextTheme: Theme) {
    applyTheme(nextTheme);
    window.localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
    setTheme(nextTheme);
  }

  const nextTheme = theme === "dark" ? "light" : "dark";

  return (
    <button
      aria-label={`Switch to ${nextTheme} mode`}
      className="theme-toggle"
      onClick={() => selectTheme(nextTheme)}
      type="button"
    >
      <span aria-hidden="true" className="theme-toggle__indicator" />
      <span>{nextTheme === "light" ? "Light" : "Dark"}</span>
    </button>
  );
}
