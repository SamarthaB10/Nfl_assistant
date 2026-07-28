export const DEFAULT_AVATAR_URL = "/profile-default-avatar.svg";
export const DEFAULT_HEADER_URL = "/profile-default-header.svg";

type PublicProfileSource = {
  name: string;
  username: string;
  about: string | null;
  imageObjectKey: string | null;
  headerObjectKey: string | null;
  createdAt: Date;
};

export type PublicProfile = {
  username: string;
  displayName: string;
  about: string | null;
  avatarUrl: string;
  headerUrl: string;
  joinedAt: string;
};

export function toPublicProfile<T extends PublicProfileSource>(
  user: T,
): PublicProfile {
  return {
    username: user.username,
    displayName: user.name,
    about: user.about,
    avatarUrl: DEFAULT_AVATAR_URL,
    headerUrl: DEFAULT_HEADER_URL,
    joinedAt: user.createdAt.toISOString(),
  };
}
