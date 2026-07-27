import type { Metadata, Viewport } from "next";
import { Barlow_Condensed, Inter } from "next/font/google";
import Link from "next/link";

import { ThemeToggle } from "@/components/theme-toggle";

import "./globals.css";

const display = Barlow_Condensed({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["600", "700", "800"],
});

const body = Inter({
  subsets: ["latin"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "LeagueWatch | Matchups worth watching",
  description:
    "Rank every 2025 NFL matchup by team quality, rivalry, and playoff stakes.",
};

export const viewport: Viewport = {
  colorScheme: "dark light",
  themeColor: "#050505",
};

const themeInitializer = `
  (function () {
    try {
      var savedTheme = window.localStorage.getItem("leaguewatch-theme");
      document.documentElement.dataset.theme =
        savedTheme === "light" ? "light" : "dark";
    } catch (error) {
      document.documentElement.dataset.theme = "dark";
    }
  })();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html data-theme="dark" lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitializer }} />
      </head>
      <body className={`${display.variable} ${body.variable}`}>
        <div className="site-shell">
          <header className="site-header">
            <Link className="brand" href="/" aria-label="LeagueWatch home">
              <span className="brand-mark" aria-hidden="true">
                L
              </span>
              <span>
                LEAGUE<strong>WATCH</strong>
              </span>
            </Link>
            <ThemeToggle />
          </header>
          {children}
          <footer className="site-footer">
            <div className="footer-meta">
              <p>2025 regular season · Live model v6</p>
              <p>NFL season data via nflverse</p>
              <p>Ratings describe viewing value, not predicted winners.</p>
            </div>
            <div
              aria-label="Watch rating color guide"
              className="rating-legend"
              role="group"
            >
              <span className="rating-legend__title">Rating guide</span>
              <ul>
                <li>
                  <span
                    aria-hidden="true"
                    className="rating-legend__dot rating-legend__dot--high"
                  />
                  7.00–10
                </li>
                <li>
                  <span
                    aria-hidden="true"
                    className="rating-legend__dot rating-legend__dot--mid"
                  />
                  5.50–6.99
                </li>
                <li>
                  <span
                    aria-hidden="true"
                    className="rating-legend__dot rating-legend__dot--low"
                  />
                  Below 5.50
                </li>
              </ul>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
