# ADR 001: Hugo over Next.js for guide_japan

**Date**: 2025-04-01
**Status**: Accepted

## Context

We need a content-heavy site that publishes 3+ articles per day, requires fast build times, and needs to run on GitHub Pages (free hosting).

## Decision

Use **Hugo** (static site generator) — same as `openclaw_seo`.

## Rationale

| Factor            | Hugo ✅           | Next.js ❌        |
|-------------------|-------------------|-------------------|
| Build time        | < 1 second        | 30–120 seconds    |
| GitHub Pages      | Native support    | Requires workaround |
| Content-first     | Markdown native   | MDX setup needed  |
| Zero runtime cost | Yes               | Needs Vercel/server |
| Team familiarity  | Same as openclaw_seo | New setup       |

## Consequences

- Hugo templates required for all layout changes.
- No dynamic API routes (use FastAPI backend for those).
- Tailwind CSS loaded via CDN in templates (same pattern as openclaw_seo).
