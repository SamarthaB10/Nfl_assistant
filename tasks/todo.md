# Accounts and Public Profiles Tasks

- [x] Task 1: Establish the PostgreSQL identity schema
  - Acceptance: Better Auth core tables and LeagueWatch profile fields are
    represented by typed Drizzle schema and a committed migration.
  - Verify: focused schema and validation tests, typecheck, lint.
  - Files: `frontend/src/db/`, `frontend/drizzle/`,
    `frontend/drizzle.config.ts`, frontend package manifests.

- [x] Task 2: Implement email/password authentication
  - Acceptance: users can sign up, log in, keep a database session, and sign
    out; invalid credentials are generic and auth requests are rate limited.
  - Verify: auth unit/component tests, typecheck, lint, build.
  - Files: `frontend/src/lib/auth*`, `frontend/src/app/api/auth/`,
    login/signup components and pages, site header.

- [x] Task 3: Implement public profile reads
  - Acceptance: `/u/[username]` is public, responsive, and exposes only the
    approved public fields with default images.
  - Verify: DTO tests, component tests, not-found behavior, mobile browser pass.
  - Files: `frontend/src/lib/profiles.ts`, `frontend/src/app/u/`,
    `frontend/src/components/profile/`.

- [x] Task 4: Implement owner profile editing
  - Acceptance: the signed-in owner can update display name and About; anonymous
    users and other accounts cannot.
  - Verify: authorization and form tests plus browser verification.
  - Files: `frontend/src/app/settings/profile/`, profile validation/data access.

- [ ] Task 5: Verify and document the complete feature
  - Acceptance: frontend and Python regressions pass, migrations work from a
    clean database, setup is documented, and the final diff passes review.
  - Verify: npm test/lint/typecheck/build/audit, pytest/Ruff, live browser flow.
  - Files: `README.md`, `.gitignore`, task tracking documents.
