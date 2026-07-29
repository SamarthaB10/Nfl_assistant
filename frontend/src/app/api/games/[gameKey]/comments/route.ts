import { auth } from "@/lib/auth";
import {
  InvalidCommentParentError,
  createGameComment,
  getGameComments,
} from "@/lib/comments";
import {
  commentCreateSchema,
  commentPageQuerySchema,
  gameKeySchema,
} from "@/lib/comment-validation";

type GameCommentsRouteContext = {
  params: Promise<{ gameKey: string }>;
};

export async function GET(
  request: Request,
  { params }: GameCommentsRouteContext,
) {
  const { gameKey: rawGameKey } = await params;
  const parsedGameKey = gameKeySchema.safeParse(rawGameKey);
  const url = new URL(request.url);
  const parsedQuery = commentPageQuerySchema.safeParse({
    limit: url.searchParams.get("limit") ?? undefined,
    cursor: url.searchParams.get("cursor") ?? undefined,
  });

  if (!parsedGameKey.success || !parsedQuery.success) {
    return Response.json(
      { error: "Invalid game or pagination parameters." },
      { status: 422 },
    );
  }

  const session = request.headers.has("cookie")
    ? await auth.api.getSession({ headers: request.headers })
    : null;
  const page = await getGameComments({
    gameKey: parsedGameKey.data,
    limit: parsedQuery.data.limit,
    cursor: parsedQuery.data.cursor,
    viewerId: session?.user.id,
  });

  return Response.json(page);
}

export async function POST(
  request: Request,
  { params }: GameCommentsRouteContext,
) {
  const session = await auth.api.getSession({
    headers: request.headers,
  });
  if (!session) {
    return Response.json({ error: "Authentication required." }, { status: 401 });
  }

  const { gameKey: rawGameKey } = await params;
  const parsedGameKey = gameKeySchema.safeParse(rawGameKey);
  if (!parsedGameKey.success) {
    return Response.json({ error: "Invalid game key." }, { status: 422 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const parsedBody = commentCreateSchema.safeParse(body);
  if (!parsedBody.success) {
    return Response.json({ error: "Invalid comment." }, { status: 422 });
  }

  try {
    const comment = await createGameComment({
      gameKey: parsedGameKey.data,
      userId: session.user.id,
      body: parsedBody.data.body,
      parentCommentId: parsedBody.data.parentCommentId,
    });

    return Response.json({ comment }, { status: 201 });
  } catch (error) {
    if (error instanceof InvalidCommentParentError) {
      return Response.json({ error: "Invalid reply parent." }, { status: 422 });
    }
    throw error;
  }
}
