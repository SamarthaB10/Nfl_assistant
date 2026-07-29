"use client";

import { useCallback, useEffect, useState } from "react";

import { HeadlineCard } from "@/components/headlines/headline-card";
import { HeadlineFilters } from "@/components/headlines/headline-filters";
import {
  fetchHeadlines,
  type HeadlineItem,
  type HeadlinesRequest,
  type HeadlineSourceFilter,
} from "@/lib/headlines";

const DEFAULT_REQUEST: HeadlinesRequest = {
  source: "ALL",
  team: "ALL",
};

export function HeadlinesWorkspace() {
  const [source, setSource] = useState<HeadlineSourceFilter>("ALL");
  const [team, setTeam] = useState("ALL");
  const [applied, setApplied] = useState(DEFAULT_REQUEST);
  const [headlines, setHeadlines] = useState<HeadlineItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (
      request: HeadlinesRequest,
      options: { append?: boolean; signal?: AbortSignal } = {},
    ) => {
      const append = options.append ?? false;
      if (append) {
        setLoadingMore(true);
      } else {
        setLoading(true);
        setApplied({ source: request.source, team: request.team });
      }
      setError(null);

      try {
        const page = await fetchHeadlines(request, options.signal);
        setHeadlines((current) => {
          if (!append) {
            return page.items;
          }
          const existingIds = new Set(current.map((item) => item.id));
          return [
            ...current,
            ...page.items.filter((item) => !existingIds.has(item.id)),
          ];
        });
        setNextCursor(page.nextCursor);
        setHasMore(page.hasMore);
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === "AbortError") {
          return;
        }
        setError(
          caught instanceof Error
            ? caught.message
            : "The latest NFL headlines could not be loaded.",
        );
      } finally {
        if (!options.signal?.aborted) {
          if (append) {
            setLoadingMore(false);
          } else {
            setLoading(false);
          }
        }
      }
    },
    [],
  );

  useEffect(() => {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(
      () =>
        void load(DEFAULT_REQUEST, {
          signal: controller.signal,
        }),
      0,
    );
    return () => {
      window.clearTimeout(timeoutId);
      controller.abort();
    };
  }, [load]);

  return (
    <main className="headlines-workspace">
      <header className="headlines-hero">
        <p className="section-kicker">Live NFL desk</p>
        <h1>LIVE NEWS</h1>
        <p>
          Current reporting from ESPN, CBS Sports, and FOX Sports. One clean
          feed, refreshed every hour.
        </p>
      </header>

      <HeadlineFilters
        loading={loading}
        onSourceChange={setSource}
        onSubmit={() => void load({ source, team })}
        onTeamChange={setTeam}
        source={source}
        team={team}
      />

      <section aria-labelledby="headlines-heading" className="headlines-results">
        <header className="headlines-results__header">
          <div>
            <p className="eyebrow">Latest coverage</p>
            <h2 id="headlines-heading">NFL Headlines</h2>
          </div>
          <p>{filterLabel(applied)}</p>
        </header>

        <div aria-live="polite">
          {loading ? (
            <div
              aria-label="Loading headlines"
              className="headline-skeleton"
              role="status"
            >
              {Array.from({ length: 6 }).map((_, index) => (
                <span key={index} />
              ))}
            </div>
          ) : error ? (
            <div className="headlines-message" role="alert">
              <p>News desk unavailable</p>
              <strong>{error}</strong>
              <button onClick={() => void load(applied)} type="button">
                Try again
              </button>
            </div>
          ) : headlines.length === 0 ? (
            <div className="headlines-message" role="status">
              <p>Filtered feed</p>
              <strong>No stories found.</strong>
              <span>Try another publisher or team.</span>
            </div>
          ) : (
            <>
              <ol className="headline-list">
                {headlines.map((headline) => (
                  <li key={headline.id}>
                    <HeadlineCard headline={headline} />
                  </li>
                ))}
              </ol>
              {hasMore && nextCursor ? (
                <button
                  className="headlines-load-more"
                  disabled={loadingMore}
                  onClick={() =>
                    void load(
                      { ...applied, cursor: nextCursor },
                      { append: true },
                    )
                  }
                  type="button"
                >
                  {loadingMore ? "Loading…" : "Load 20 more"}
                </button>
              ) : null}
            </>
          )}
        </div>
      </section>
    </main>
  );
}

function filterLabel(request: HeadlinesRequest): string {
  const source =
    request.source === "ALL" ? "All publishers" : request.source;
  const team = request.team === "ALL" ? "All teams" : request.team;
  return `${source} · ${team}`;
}
