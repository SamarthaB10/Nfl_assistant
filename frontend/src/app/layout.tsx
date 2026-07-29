import type { Metadata, Viewport } from "next";
import { Barlow_Condensed, Dancing_Script, Inter } from "next/font/google";
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

const script = Dancing_Script({
  subsets: ["latin"],
  variable: "--font-script",
  weight: ["600", "700"],
});

export const metadata: Metadata = {
  title: "Drizzle | Matchups worth watching",
  description:
    "Rank every 2025 NFL matchup by team quality, rivalry, and playoff stakes.",
};

export const viewport: Viewport = {
  colorScheme: "dark light",
  themeColor: "#32302f",
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
      <body className={`${display.variable} ${body.variable} ${script.variable}`}>
        <div className="site-shell">
          <header className="site-header">
            <Link className="brand" href="/" aria-label="Drizzle home">
              <span className="brand-mark" aria-hidden="true">
                DZ
              </span>
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
