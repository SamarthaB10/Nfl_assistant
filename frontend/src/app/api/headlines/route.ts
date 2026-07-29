const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const ALLOWED_QUERY_FIELDS = ["limit", "cursor", "source", "team"] as const;

function backendUrlFor(request: Request): string {
  const incoming = new URL(request.url);
  const backend = new URL(
    "/api/v1/headlines",
    process.env.NFL_API_BASE_URL ?? DEFAULT_API_BASE_URL,
  );

  for (const field of ALLOWED_QUERY_FIELDS) {
    const value = incoming.searchParams.get(field);
    if (value !== null) {
      backend.searchParams.set(field, value);
    }
  }

  return backend.toString();
}

export async function GET(request: Request): Promise<Response> {
  try {
    const response = await fetch(backendUrlFor(request), {
      cache: "no-store",
      headers: { accept: "application/json" },
    });
    const body = await response.text();

    return new Response(body, {
      status: response.status,
      headers: {
        "cache-control": "no-store",
        "content-type":
          response.headers.get("content-type") ?? "application/json",
      },
    });
  } catch {
    return Response.json(
      { detail: "Unable to reach the Drizzle API." },
      { status: 502 },
    );
  }
}
