---
name: github-trending-newsletter
description: Use when building, planning, reviewing, or operating the GitHub Trending daily newsletter app: Trending ingestion, GitHub API enrichment, repository scoring, email rendering, delivery, state, scheduling, and free deployment constraints.
---

# GitHub Trending Newsletter Skill

## Mission

Build a daily developer intelligence email from GitHub Trending. Review every
repository returned by `https://github.com/trending?since=daily` for language
`any`, spoken language `any`, and range `today`.

## Default Architecture

- Prefer Python 3.12 CLI over an always-on server.
- Run daily through GitHub Actions `schedule` plus `workflow_dispatch`.
- Store state as committed JSON files under `data/`.
- Do not commit recipient emails, API keys, or SMTP credentials.
- Keep MVP ranking deterministic and explainable.
- Add AI summaries only as an optional adapter with a deterministic fallback.

## Required Workflow

1. Consult Codegraph before editing source. If no source is indexed yet, note
   that and re-check after adding source files.
2. Preserve the no-paid-service constraint unless the user explicitly changes
   it.
3. Fetch Trending HTML once per run and parse all repo cards.
4. Enrich only repositories discovered from Trending.
5. Use low concurrency, timeouts, and partial-failure tolerance for GitHub API
   calls.
6. Render both HTML and plain-text email.
7. Check idempotency before sending.
8. Write run artifacts before or with send metadata so failures are debuggable.

## Scoring Guidance

Use a 100-point transparent score:

- Practical usefulness: 20
- AI workflow impact: 18
- Ease of adoption: 14
- Technical quality: 14
- Momentum: 12
- Novelty: 8
- Production readiness: 7
- Strategic relevance: 7

Every recommendation should cite observable evidence: README, topics, license,
recent activity, stars today, release state, or docs quality.

## Verification

Before claiming completion, verify:

- Parser tests pass against a frozen Trending HTML fixture.
- Ranking is deterministic from fixed input.
- Email snapshot covers HTML and text.
- Dry run creates a daily archive without sending.
- Send mode creates or respects a sent marker.
- Workflow has manual dispatch and scheduled trigger.
