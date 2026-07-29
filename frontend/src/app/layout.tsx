import type { Metadata, Viewport } from "next";
import { Barlow_Condensed, Inter } from "next/font/google";
import Link from "next/link";

import { AccountNav } from "@/components/auth/account-nav";
import { SiteFooter } from "@/components/site-footer";
import { SiteNavigation } from "@/components/site-navigation";
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
  title: "Drizzle | Matchups worth watching",
  description:
    "Rank every 2025 NFL matchup by team quality, rivalry, and playoff stakes.",
};

export const viewport: Viewport = {
  colorScheme: "dark light",
  themeColor: "#000000",
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
            <Link className="brand" href="/" aria-label="Drizzle home">
              <svg
                aria-hidden="true"
                className="brand-mark"
                focusable="false"
                viewBox="0 0 72 52"
              >
                <rect
                  className="brand-mark__tile"
                  x="1"
                  y="1"
                  width="70"
                  height="50"
                  rx="12"
                />
                <rect
                  className="brand-mark__field"
                  x="7"
                  y="7"
                  width="58"
                  height="38"
                  rx="8"
                />
                <path
                  className="brand-mark__stroke"
                  d="M16 14v24M16 14c13-2 20 2 20 12s-7 14-20 12M41 15c7-2 13-2 18 0-6 5-12 10-16 15-3 3-5 6-6 8 8 2 16 2 22-1"
                />
              </svg>
              <span aria-hidden="true" className="brand-wordmark">
                DRIZZLE
              </span>
            </Link>
            <SiteNavigation />
            <div className="header-actions">
              <AccountNav />
              <ThemeToggle />
            </div>
          </header>
          {children}
          <SiteFooter />
        </div>
      </body>
    </html>
  );
}
