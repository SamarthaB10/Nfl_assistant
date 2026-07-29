import { auth } from "@/lib/auth";
import { commentIdSchema } from "@/lib/comment-validation";
import { softDeleteOwnComment } from "@/lib/comments";

type CommentRouteContext = {
  params: Promise<{ commentId: string }>;
};

export async function DELETE(
  request: Request,
  { params }: CommentRouteContext,
) {
  const session = await auth.api.getSession({
    headers: request.headers,
  });
  if (!session) {
    return Response.json({ error: "Authentication required." }, { status: 401 });
  }

  const { commentId: rawCommentId } = await params;
  const parsedCommentId = commentIdSchema.safeParse(rawCommentId);
  if (!parsedCommentId.success) {
    return Response.json({ error: "Invalid comment ID." }, { status: 422 });
  }

  const deleted = await softDeleteOwnComment(
    parsedCommentId.data,
    session.user.id,
  );
  if (!deleted) {
    return Response.json({ error: "Comment not found." }, { status: 404 });
  }

  return new Response(null, { status: 204 });
}
