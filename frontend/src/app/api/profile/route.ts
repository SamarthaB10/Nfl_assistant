import { auth } from "@/lib/auth";
import { profileUpdateSchema } from "@/lib/profile-validation";
import { updateOwnProfile } from "@/lib/profiles";

export async function PATCH(request: Request) {
  const session = await auth.api.getSession({
    headers: request.headers,
  });

  if (!session) {
    return Response.json({ error: "Authentication required." }, { status: 401 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const parsed = profileUpdateSchema.safeParse(body);
  if (!parsed.success) {
    return Response.json(
      { error: "Display name or About text is invalid." },
      { status: 422 },
    );
  }

  const profile = await updateOwnProfile(session.user.id, parsed.data);
  if (!profile) {
    return Response.json({ error: "Profile not found." }, { status: 404 });
  }

  return Response.json({ profile });
}
