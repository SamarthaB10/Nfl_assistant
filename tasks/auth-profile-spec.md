# Spec: Email Accounts and Public Profiles

**Status:** Approved for implementation

## Objective

Add optional LeagueWatch accounts for personalization without putting the
existing matchup rankings behind a login.

The first account release must let a user:

- sign up with a private email address, unique public username, display name,
  and password;
- sign in with email and password and sign out;
- view any user's public profile at `/u/[username]`;
- edit only their own display name and About text;
- see a mobile-first public profile inspired by the supplied reference, without
  karma, followers, friends, social stats, or other community features.

The existing rankings page at `/` remains public and otherwise unchanged.

## Product Decisions and Assumptions

- Email is private and is the only login identifier.
- Username is the stable public handle. The UI displays it with `@`, while the
  canonical route is `/u/samartha`.
- Display name is independent from username and can be changed.
- Accounts are optional and exist for future personalization; this release does
  not yet personalize ranking scores or save favorite teams.
- Profiles are publicly readable. Only their owner can edit them.
- Version 1 uses static LeagueWatch avatar and header defaults. It stores
  nullable image object keys for a later object-storage integration, but it
  neither accepts uploads nor stores image binaries in PostgreSQL.
- Email verification, password recovery, OAuth, account deletion, and username
  changes are separate follow-up features because they require additional
  product policy or external services.

## Tech Stack

### Existing

- Next.js `16`, React `19`, and TypeScript in `frontend/`.
- FastAPI remains the private NFL rankings service and is not given
  authentication or profile responsibilities in this release.
- npm remains the frontend package manager because `frontend/package-lock.json`
  is authoritative.

### Proposed Additions

- PostgreSQL as the durable store for users, credentials, sessions, and profile
  fields.
- Better Auth for email/password authentication, password hashing, session
  lifecycle, and the Next.js auth route.
- Drizzle ORM and Drizzle Kit for typed PostgreSQL access and committed,
  reviewable migrations.
- A PostgreSQL driver supported by Drizzle.

This keeps all browser-facing identity work inside Next.js, where the current
backend-for-frontend boundary already lives. Better Auth provides built-in
email/password authentication, uses `scrypt` for password hashing, supports
database-backed cookie sessions, and has first-party Next.js and Drizzle
integration.

## Architecture and Request Boundaries

```text
Browser
  |
  v
Next.js
  |- public rankings UI ----------------> FastAPI rankings API
  |- /api/auth/[...all] ----------------> Better Auth
  |- public profile reads --------------> profile data access layer
  |- owner profile mutations -----------> session + ownership check
  |
  v
PostgreSQL
  |- users
  |- accounts (credential password hash)
  |- sessions
  |- verification records reserved by auth schema
```

- Next.js is the only service that reads or writes account tables.
- FastAPI remains unaware of browser sessions and user PII.
- Public profile queries return a field allowlist; they never serialize email,
  credential, session, IP-address, or user-agent data.
- Protected mutations perform a full database-backed session validation at the
  mutation boundary. A cookie-presence check may only be used for an optimistic
  redirect, never for authorization.

## Data Model

Use Better Auth's generated Drizzle schema as the source of truth for its core
tables, then extend the user model with the LeagueWatch profile fields.

### User

| Field | Visibility | Rules |
| --- | --- | --- |
| `id` | internal | generated stable ID |
| `email` | private | normalized, unique, never returned publicly |
| `emailVerified` | private | retained for later verification support |
| `name` | public | display name, `1–50` trimmed characters |
| `username` | public | canonical lowercase, unique, immutable in v1 |
| `about` | public | optional plain text, at most `300` characters |
| `imageObjectKey` | public-derived | nullable; unused until uploads exist |
| `headerObjectKey` | public-derived | nullable; unused until uploads exist |
| `createdAt` | public | displayed as month and year joined |
| `updatedAt` | internal | maintained by the persistence layer |

Proposed usernames are `3–24` characters and match
`^[a-z0-9_]+$`. Normalize email and username before enforcing database
uniqueness. The database constraints, not client-side checks, are authoritative.

### Auth-Owned Tables

- `accounts` stores the credential provider record and password hash.
- `sessions` stores opaque session tokens, user ownership, expiry, and auth
  metadata.
- `verifications` remains available for future email verification and password
  reset flows but is not exposed in the first UI.

Do not add a separate profile table yet. The current profile is one-to-one and
small enough to remain on the user record.

## Routes and Interfaces

### Pages

| Route | Access | Behavior |
| --- | --- | --- |
| `/` | public | existing rankings home |
| `/signup` | signed out | email, username, display name, password form |
| `/login` | signed out | email and password form |
| `/u/[username]` | public | public profile; owner sees Edit profile |
| `/settings/profile` | authenticated | edit display name and About |

Authenticated users see their profile entry point and Sign out in the existing
site header. Signed-out users see Log in and Sign up. Authentication must not
block the rankings request path.

### Auth API

Mount Better Auth at `/api/auth/[...all]` and use its email sign-up, email
sign-in, session, and sign-out operations. Do not create a parallel custom
password or session API.

### Profile Data Access

Expose narrow server-side operations rather than a generic user endpoint:

```ts
type PublicProfile = {
  username: string;
  displayName: string;
  about: string | null;
  avatarUrl: string;
  headerUrl: string;
  joinedAt: string;
};

type UpdateOwnProfileInput = {
  displayName: string;
  about: string;
};
```

- `getPublicProfile(username)` may be called without a session and returns only
  `PublicProfile`.
- `updateOwnProfile(input, session)` derives the target user from the verified
  session. It never accepts a user ID or username as the authorization source.
- A missing public profile renders the Next.js not-found state.
- Duplicate email or username errors use safe, user-actionable messages without
  exposing credential or session details.

## Mobile-First Profile UI

- Design for `320–430px` widths first, then scale to the existing desktop shell.
- Use the current LeagueWatch fonts, dark/light themes, color tokens, header,
  and overall visual language.
- Profile composition: full-width default header image, overlapping circular
  default avatar, display name, `@username`, joined date, About section, and an
  owner-only Edit profile action.
- Preserve visible keyboard focus, labeled inputs, semantic headings, minimum
  touch targets, and sufficient contrast in both themes.
- Do not reproduce the reference image's karma, Rax, Get Pro, social, stats,
  favorites, drafts, follower, friend, or community sections.
- Render About as escaped plain text. User-provided HTML is not accepted.

## Security and Privacy

### Threat Boundaries

- Untrusted inputs: signup, login, username route segment, display name, and
  About text.
- Sensitive assets: password hashes, private email addresses, session tokens,
  and account ownership.
- Primary abuse cases: credential stuffing, account enumeration, username
  squatting/collision, profile tampering, stored XSS, session theft, and
  unauthorized profile updates.

### Required Controls

- Let Better Auth own password hashing and credential verification; never store
  plaintext passwords or log credentials.
- Use opaque, database-backed sessions in `HttpOnly`, `SameSite=Lax` cookies;
  set `Secure` in production. Do not store auth tokens in `localStorage`.
- Require server-side session and ownership checks for every profile mutation.
- Validate and normalize all form, route, and mutation inputs on the server.
- Use Drizzle-generated parameterized queries and database uniqueness
  constraints.
- Return a public-profile DTO allowlist. Never expose email, password hashes,
  tokens, IP addresses, or user agents.
- Use generic invalid-credential responses and rate-limit authentication
  attempts using Better Auth's supported rate-limiting behavior.
- Use React's normal text escaping; do not use `dangerouslySetInnerHTML` for
  profile content.
- Keep database credentials and auth secrets in ignored environment files.
  Commit only an `.env.example` with placeholders.
- Add and verify appropriate security headers without weakening the existing
  application.
- Preserve HTTPS-only production behavior and restrict trusted origins to the
  deployed LeagueWatch origin.

## Project Structure

Exact names may adjust to framework conventions during planning, but ownership
must remain:

```text
frontend/
  drizzle/
    <committed migrations>
  src/
    app/
      api/auth/[...all]/route.ts
      login/page.tsx
      signup/page.tsx
      settings/profile/page.tsx
      u/[username]/page.tsx
    components/
      auth/
      profile/
    db/
      index.ts
      schema.ts
    lib/
      auth.ts
      auth-client.ts
      profiles.ts
      profile-validation.ts
  drizzle.config.ts
  .env.example
```

Do not reorganize the existing ranking components or FastAPI modules as part of
this feature.

## Commands

These commands describe the expected implemented workflow; they are not to be
run during the specification phase.

```bash
cd frontend
npm ci
npm run db:generate
npm run db:migrate
npm test
npm run lint
npm run typecheck
npm run build
```

Local PostgreSQL startup will be documented in the implementation plan after
the deployment target is selected. Migration generation and application must be
separate scripts so schema changes are reviewable before execution.

## Code Style

- Follow the existing TypeScript, React Server Component, and colocated test
  conventions.
- Prefer server components for public profile reads and small client components
  only where forms or reactive session state require them.
- Keep database access in a server-only data access layer.
- Define explicit public DTOs instead of spreading database rows into UI props.
- Use typed validation schemas at every request boundary.
- Keep auth-library configuration centralized; do not duplicate session parsing
  or password logic.

## Testing Strategy

### Unit and Component Tests

- Signup validation: normalized email, username syntax, display-name limits,
  password limits, and About limits.
- Public-profile mapping excludes every private/auth field.
- Profile edit controls render only for the owner.
- Mobile signup, login, profile, and edit forms have labels, errors, keyboard
  focus, and theme-compatible states.

### Integration Tests

- A user can sign up, receives a session, and can sign out.
- Email and username uniqueness are case-insensitive and database-enforced.
- Login succeeds with email/password and fails generically for invalid
  credentials.
- Anonymous users can view `/u/[username]`.
- An authenticated owner can update their display name and About text.
- Anonymous users and other authenticated users cannot modify that profile.
- Public responses never include email, credentials, or session fields.
- Session expiry or revocation blocks protected mutations.

### Regression and Verification

- Existing rankings page and `/api/rankings` tests remain green.
- Test at mobile widths and at the current desktop layout.
- Verify dark and light themes.
- Run npm audit against the committed lockfile and triage reachable findings;
  do not apply forced remediation.
- Verify production responses set expected session cookies and security headers.

## Boundaries

### Always

- Keep rankings public.
- Store durable account state in PostgreSQL.
- Treat email as private and username/display name/About as public.
- Check authorization at the data mutation boundary.
- Commit forward-only database migrations.
- Use default local images until object storage is explicitly approved.

### Ask First

- Add OAuth providers, email delivery, verification, or password reset.
- Add image uploads or any object-storage provider.
- Make usernames mutable or add reserved/verified handles.
- Add user roles, moderation, admin access, or public social features.
- Share user identity with FastAPI or change the ranking response.
- Add Redis, a managed database vendor, or a production deployment service.

### Never

- Store plaintext passwords, raw image binaries, or auth tokens in browser
  storage.
- Expose email, password hashes, session data, or internal IDs on public
  profiles.
- Trust client-side validation or a cookie-presence check for authorization.
- Let one user edit another user's profile.
- Put authentication in front of the public rankings experience.
- Add karma, followers, friends, or unrelated community features in this slice.

## Success Criteria

- A new user can create an account with a unique email and username, sign in
  with email/password, persist a database-backed session, and sign out.
- Any visitor can load a responsive `/u/[username]` profile showing the default
  header/avatar, display name, public handle, joined date, and About text.
- Only the authenticated owner can access and submit profile edits.
- Email and all auth/session fields remain private in server and browser
  responses.
- Public rankings work exactly as they did before accounts were added.
- PostgreSQL schema and migrations are reproducible from a clean database.
- Unit, integration, accessibility-focused component tests, lint, typecheck,
  build, and existing regression tests pass.
- The profile is usable at common mobile-preview widths in both dark and light
  mode.

## Approved Defaults

- Better Auth + Drizzle is the account and PostgreSQL integration stack.
- Usernames use `3–24` lowercase letters, numbers, and underscores.
- Display names are limited to `50` characters.
- About text is limited to `300` characters.
- The PostgreSQL hosting provider remains undecided until deployment planning;
  it does not change the application contract in this spec.

## References

- [Next.js Authentication Guide](https://nextjs.org/docs/app/guides/authentication)
- [Next.js Backend-for-Frontend Guide](https://nextjs.org/docs/app/guides/backend-for-frontend)
- [Better Auth email and password](https://better-auth.com/docs/authentication/email-password)
- [Better Auth session management](https://better-auth.com/docs/concepts/session-management)
- [Better Auth Next.js integration](https://better-auth.com/docs/integrations/next)
- [Better Auth Drizzle adapter](https://better-auth.com/docs/adapters/drizzle)
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
