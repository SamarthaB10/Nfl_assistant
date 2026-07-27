export type SelectionMode = "all" | "top" | "bottom";

export interface RankingsRequest {
  week: number;
  mode: SelectionMode;
  count: number;
}

export interface PlayerSpotlight {
  playerId: string;
  teamId: string;
  name: string;
  position: string;
  imageUrl: string;
  profileUrl: string;
  details: string[];
}

export interface GameSummary {
  matchup: string;
  records: Record<string, string>;
  logos: Record<string, string | null>;
  score: number;
  reasons: string[];
  unavailablePlayerIds?: string[];
  playersToWatch?: PlayerSpotlight[];
}

export function buildRankingsSearch({
  week,
  mode,
  count,
}: RankingsRequest): URLSearchParams {
  const search = new URLSearchParams({
    season: "2025",
    week: String(week),
  });

  if (mode !== "all") {
    search.set(mode, String(count));
  }

  return search;
}

export async function fetchRankings(
  request: RankingsRequest,
  signal?: AbortSignal,
): Promise<GameSummary[]> {
  const search = buildRankingsSearch(request);
  const response = await fetch(`/api/rankings?${search}`, { signal });
  const payload: unknown = await response.json();

  if (!response.ok) {
    const detail =
      typeof payload === "object" &&
      payload !== null &&
      "detail" in payload &&
      typeof payload.detail === "string"
        ? payload.detail
        : "The matchup rankings could not be loaded.";
    throw new Error(detail);
  }

  if (!Array.isArray(payload)) {
    throw new Error("The rankings API returned an unexpected response.");
  }

  return payload as GameSummary[];
}
