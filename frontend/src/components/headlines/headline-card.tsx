import Image from "next/image";

import type { HeadlineItem } from "@/lib/headlines";
import { getNflTeam } from "@/lib/nfl-teams";

interface HeadlineCardProps {
  headline: HeadlineItem;
}

function publishedLabel(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "America/Chicago",
  }).format(new Date(value));
}

export function HeadlineCard({ headline }: HeadlineCardProps) {
  return (
    <article className="headline-card">
      <a
        className="headline-card__link"
        href={headline.url}
        rel="noreferrer noopener"
        target="_blank"
      >
        <div className="headline-card__media">
          {headline.imageUrl ? (
            <Image
              alt=""
              height={338}
              sizes="(min-width: 900px) 300px, (min-width: 640px) 38vw, 100vw"
              src={headline.imageUrl}
              width={600}
            />
          ) : (
            <span aria-hidden="true">{headline.source}</span>
          )}
        </div>
        <div className="headline-card__body">
          <div className="headline-card__meta">
            <strong>{headline.source}</strong>
            <span>{publishedLabel(headline.publishedAt)}</span>
          </div>
          <h2>{headline.title}</h2>
          {headline.excerpt ? <p>{headline.excerpt}</p> : null}
          <footer>
            <span>{headline.author ?? `${headline.source} Sports`}</span>
            {headline.teamCodes.length > 0 ? (
              <span className="headline-card__teams">
                {headline.teamCodes.map((teamCode) => {
                  const team = getNflTeam(teamCode);

                  return team ? (
                    <span
                      aria-label={team.name}
                      className="headline-card__team"
                      key={team.code}
                      role="img"
                      title={team.name}
                    >
                      <Image
                        alt=""
                        aria-hidden="true"
                        height={22}
                        src={team.logoUrl}
                        width={22}
                      />
                    </span>
                  ) : (
                    <b key={teamCode}>{teamCode}</b>
                  );
                })}
              </span>
            ) : null}
          </footer>
        </div>
        <span aria-hidden="true" className="headline-card__arrow">
          ↗
        </span>
      </a>
    </article>
  );
}
