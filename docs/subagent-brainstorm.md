# Subagent Brainstorm Summary

Three independent subagent teams were spawned for product/editorial,
technical architecture, and operations/deliverability. No subagent edited
files.

## Product And Editorial

Target users:

- Busy developers who want to know which trending repos are worth opening.
- Tech leads looking for tools that may improve team velocity.
- AI tooling builders tracking agents, RAG, evals, automation, and infra.
- Founders watching emerging developer pain points.
- OSS maintainers watching ecosystem attention.

Editorial tags:

- `Try Today`
- `Watch`
- `Deep Dive`
- `Hype Risk`
- `AI Workflow`
- `Infra`
- `Frontend`
- `DevTools`
- `Learning`

The product should bias toward "why this matters" and "what can I do with it
today", not just star counts.

## Technical Architecture

Consensus:

- Use Python 3.12.
- Build a CLI, not a server.
- Fetch Trending HTML once daily.
- Use GitHub API only for repositories discovered from Trending.
- Store daily archives and state as JSON files.
- Keep scoring transparent before adding AI.

Important failure modes:

- GitHub Trending DOM changes.
- Rate limits or partial API failures.
- Scheduled workflow delays.
- Duplicate send on rerun.
- SMTP/provider failure after rendering.

## Operations And Deliverability

Consensus:

- Best free run target: GitHub Actions schedule.
- Best free email options: Resend for API quality, Brevo for higher daily free
  volume, SMTP for portability.
- Avoid top-of-hour cron.
- Use GitHub secrets for credentials and recipients.
- Keep workflow permissions minimal.
- Do not store recipient emails in committed files.

Operational caution:

GitHub Actions should stay a low-frequency project workflow. It should not be
used as a high-frequency scraper, long-running backend, or unrelated compute
platform.
