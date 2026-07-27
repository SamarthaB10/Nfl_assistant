"use client";

import { useCallback, useEffect, useState } from "react";

import { GameList } from "@/components/game-list";
import { RankingControls } from "@/components/ranking-controls";
import {
  fetchRankings,
  type GameSummary,
  type RankingsRequest,
} from "@/lib/rankings";

const DEFAULT_REQUEST: RankingsRequest = {
  week: 18,
  mode: "top",
  count: 5,
};

export function RankingsWorkspace() {
  const [draft, setDraft] = useState(DEFAULT_REQUEST);
  const [applied, setApplied] = useState(DEFAULT_REQUEST);
  const [games, setGames] = useState<GameSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (request: RankingsRequest, signal?: AbortSignal) => {
      setLoading(true);
      setError(null);

      try {
        const nextGames = await fetchRankings(request, signal);
        setGames(nextGames);
        setApplied(request);
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === "AbortError") {
          return;
        }
        setError(
          caught instanceof Error
            ? caught.message
            : "The matchup rankings could not be loaded.",
        );
      } finally {
        if (!signal?.aborted) {
          setLoading(false);
        }
      }
    },
    [],
  );

  useEffect(() => {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(
      () => void load(DEFAULT_REQUEST, controller.signal),
      0,
    );
    return () => {
      window.clearTimeout(timeoutId);
      controller.abort();
    };
  }, [load]);

  return (
    <main className="workspace">
      <header className="hero">
        <h1>
          Know what’s <span>worth watching.</span>
        </h1>
        <p>
          Every matchup, ranked by team quality, rivalry, and playoff stakes.
        </p>
      </header>

      <RankingControls
        loading={loading}
        onChange={setDraft}
        onSubmit={() => void load(draft)}
        request={draft}
      />

      <div aria-live="polite">
        {loading ? (
          <div
            aria-label="Loading matchups"
            className="results-skeleton"
            role="status"
          >
            {Array.from({ length: draft.mode === "all" ? 5 : draft.count }).map(
              (_, index) => (
                <span key={index} />
              ),
            )}
          </div>
        ) : error ? (
          <div className="error-state" role="alert">
            <p>Rankings unavailable</p>
            <strong>{error}</strong>
            <span>Make sure FastAPI is running on port 8000, then retry.</span>
          </div>
        ) : (
          <GameList games={games} request={applied} />
        )}
      </div>
    </main>
  );
}
