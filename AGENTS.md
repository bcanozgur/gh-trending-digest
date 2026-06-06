@/Users/berkecanozgur/.codex/RTK.md

# Project Guidance

This is a greenfield project for a daily GitHub Trending intelligence email.

Use the repo-local skill in `.agents/skills/github-trending-newsletter/SKILL.md`
when planning, implementing, or reviewing ingestion, scoring, newsletter
generation, delivery, scheduling, or operations for this project.

Before code changes, consult Codegraph for the current project state. If the
project has no indexed source yet, initialize or refresh Codegraph after adding
source files.

Default product direction:

- Build a Python CLI, not an always-on web service.
- Run daily from a scheduled GitHub Actions workflow.
- Keep hosting free by using public-repo Actions when possible.
- Store durable state as repo files under `data/`, not in a database server.
- Keep scoring explainable and evidence-based.
- Do not store recipient email addresses in committed files.
