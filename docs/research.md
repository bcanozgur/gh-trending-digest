# Research: Daily GitHub Trending Letterbox

Date: 2026-06-07

## Objective

Build a daily email product for developers who want signal from GitHub
Trending without checking it manually. The job should review every repository
returned by the daily Trending page with programming language `any` and spoken
language `any`, rank the results, and send a compact daily email.

## Findings

GitHub Trending is an HTML product page, not a documented official API. The
current page exposes the required fields in HTML: repo owner/name, description,
language, total stars, forks, contributor avatars, and "stars today". The daily
input URL should be:

`https://github.com/trending?since=daily`

Leaving language and `spoken_language_code` unset represents programming
language `any` and spoken language `any`.

GitHub REST API rate limits are sufficient for enrichment if the workflow uses
the built-in `GITHUB_TOKEN`: GitHub documents 1,000 requests per hour per
repository for `GITHUB_TOKEN`, 60 requests per hour unauthenticated, and 5,000
requests per hour for normal authenticated requests. The app should still batch
GraphQL calls where useful, keep concurrency low, and tolerate partial
enrichment.

GitHub Actions is the strongest free run target. Public repositories can use
standard GitHub-hosted runners for free, while private repos have included free
minutes. Scheduled workflows run on the default branch, use UTC unless a
timezone is configured, support POSIX cron syntax, and should avoid the top of
the hour because schedules can be delayed under load.

GitHub Actions has usage and policy constraints. The proposed daily job is low
burden and tied to developing/publishing this software project, but it must not
become a high-frequency scraper, a serverless backend, or unrelated compute.

Email delivery is the main product constraint:

- Resend free: 3,000 emails/month and 100/day, good API, usually requires a
  verified owned domain for real sending.
- Brevo free: 300 emails/day and large contact storage, but free mail may carry
  provider branding.
- MailerSend free: smaller monthly quota and approval requirements.
- Gmail/App Script: acceptable for self-notifications, weak for a public list.

GitHub Models has included free but rate-limited model usage. It can support
optional editorial summaries, but the MVP should not depend on paid AI calls.
The first version should generate evidence-based summaries from metrics and
README snippets.

## Recommended Product Shape

Use a Python CLI run once per day by GitHub Actions. The CLI should:

1. Fetch and parse the Trending daily HTML.
2. Enrich each candidate repository with public GitHub metadata.
3. Score repositories with transparent dimensions.
4. Render HTML and plain-text email.
5. Send only if idempotency state shows the date has not already been sent.
6. Commit daily run artifacts and state back to the repo.

## Source Links

- GitHub Trending: https://github.com/trending?since=daily
- GitHub Actions billing and free public runners:
  https://docs.github.com/en/actions/concepts/billing-and-usage
- GitHub Actions workflow schedule syntax:
  https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onschedule
- GitHub Actions limits:
  https://docs.github.com/en/actions/reference/limits
- GitHub Actions product terms:
  https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features
- GitHub REST API rate limits:
  https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
- Resend pricing/free limits:
  https://resend.com/docs/knowledge-base/what-is-resend-pricing
- Brevo free plan:
  https://help.brevo.com/hc/en-us/articles/208589409
- Cloudflare Workers pricing/limits:
  https://developers.cloudflare.com/workers/platform/pricing/
- Cloudflare Cron Triggers:
  https://developers.cloudflare.com/workers/configuration/cron-triggers/
- Vercel Cron Jobs:
  https://vercel.com/docs/cron-jobs/usage-and-pricing
- GitLab scheduled pipelines and compute minutes:
  https://docs.gitlab.com/ci/pipelines/schedules/
  https://docs.gitlab.com/ci/pipelines/compute_minutes/
- GitHub Models billing:
  https://docs.github.com/en/billing/concepts/product-billing/github-models
