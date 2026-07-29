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
