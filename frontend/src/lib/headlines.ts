export type HeadlineSource = "ESPN" | "CBS" | "FOX";
export type HeadlineSourceFilter = "ALL" | HeadlineSource;

export interface HeadlineItem {
  id: number;
  source: HeadlineSource;
  title: string;
  author: string | null;
  excerpt: string | null;
  url: string;
  imageUrl: string | null;
  teamCodes: string[];
  publishedAt: string;
}

export interface HeadlinesPage {
  items: HeadlineItem[];
  nextCursor: string | null;
  hasMore: boolean;
}

export interface HeadlinesRequest {
  source: HeadlineSourceFilter;
  team: string;
  cursor?: string;
}

export function buildHeadlinesSearch({
  source,
  team,
  cursor,
}: HeadlinesRequest): URLSearchParams {
  const search = new URLSearchParams({ limit: "20" });

  if (source !== "ALL") {
    search.set("source", source);
  }
  if (team !== "ALL") {
    search.set("team", team);
  }
  if (cursor) {
    search.set("cursor", cursor);
  }

  return search;
}

export async function fetchHeadlines(
  request: HeadlinesRequest,
  signal?: AbortSignal,
): Promise<HeadlinesPage> {
  const response = await fetch(`/api/headlines?${buildHeadlinesSearch(request)}`, {
    signal,
  });
  const payload: unknown = await response.json();

  if (!response.ok) {
    const detail =
      typeof payload === "object" &&
      payload !== null &&
      "detail" in payload &&
      typeof payload.detail === "string"
        ? payload.detail
        : "The latest NFL headlines could not be loaded.";
    throw new Error(detail);
  }

  if (
    typeof payload !== "object" ||
    payload === null ||
    !("items" in payload) ||
    !Array.isArray(payload.items)
  ) {
    throw new Error("The headlines API returned an unexpected response.");
  }

  return payload as HeadlinesPage;
}
