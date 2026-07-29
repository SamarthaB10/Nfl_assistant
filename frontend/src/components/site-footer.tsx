"use client";

import { usePathname } from "next/navigation";

interface SiteFooterViewProps {
  pathname: string;
}

export function SiteFooterView({ pathname }: SiteFooterViewProps) {
  if (pathname.startsWith("/headlines")) {
    return (
      <footer className="site-footer">
        <div className="footer-meta">
          <p>Current NFL coverage · Updated hourly</p>
          <p>Headlines via ESPN, CBS Sports, FOX Sports, and NBC Sports</p>
          <p>Drizzle stores metadata only. Stories open at the publisher.</p>
        </div>
      </footer>
    );
  }

  return (
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
            7.00-10
          </li>
          <li>
            <span
              aria-hidden="true"
              className="rating-legend__dot rating-legend__dot--mid"
            />
            5.50-6.99
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
  );
}

export function SiteFooter() {
  return <SiteFooterView pathname={usePathname()} />;
}
