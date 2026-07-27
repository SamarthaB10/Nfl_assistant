import type { Metadata, Viewport } from "next";
import { Barlow_Condensed, Inter } from "next/font/google";
import Link from "next/link";

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
  colorScheme: "dark",
  themeColor: "#050505",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
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
            <div className="model-status">
              <span aria-hidden="true" />
              2025 model
            </div>
          </header>
          {children}
          <footer className="site-footer">
            <p>
              NFL season data via nflverse
              <span aria-hidden="true"> · </span>
              Watchability model v6
            </p>
            <p>Ratings describe viewing value, not predicted winners.</p>
          </footer>
        </div>
      </body>
    </html>
  );
}
