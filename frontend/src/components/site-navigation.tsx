"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

interface SiteNavigationViewProps {
  pathname: string;
}

const TABS = [
  { href: "/", label: "Matchups" },
  { href: "/headlines", label: "Headlines" },
] as const;

export function SiteNavigationView({ pathname }: SiteNavigationViewProps) {
  return (
    <nav aria-label="Primary" className="site-nav">
      {TABS.map((tab) => {
        const isCurrent =
          tab.href === "/" ? pathname === "/" : pathname.startsWith(tab.href);
        return (
          <Link
            aria-current={isCurrent ? "page" : undefined}
            href={tab.href}
            key={tab.href}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}

export function SiteNavigation() {
  return <SiteNavigationView pathname={usePathname()} />;
}
