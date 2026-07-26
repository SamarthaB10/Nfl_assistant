export type SelectionMode = "all" | "top" | "bottom";

export interface RankingsRequest {
  week: number;
  mode: SelectionMode;
  count: number;
}

export interface GameSummary {
  matchup: string;
  records: Record<string, string>;
  score: number;
  reasons: string[];
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
