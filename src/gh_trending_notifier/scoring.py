from __future__ import annotations

from datetime import UTC, datetime, timedelta

from gh_trending_notifier.models import RepoEnrichment, RankedRepo, ScoreBreakdown, TrendingRepo

AI_TERMS = {
    "ai",
    "agent",
    "agents",
    "llm",
    "rag",
    "model",
    "models",
    "eval",
    "evals",
    "openai",
    "anthropic",
    "claude",
    "codex",
    "automation",
    "copilot",
    "inference",
}

DEV_TOOL_TERMS = {
    "cli",
    "sdk",
    "api",
    "devtool",
    "developer",
    "framework",
    "testing",
    "debug",
    "deploy",
    "workflow",
    "terminal",
    "docker",
}


def rank_repositories(
    repos: list[TrendingRepo],
    enrichments: dict[str, RepoEnrichment] | None = None,
    previous_state: dict[str, object] | None = None,
    today: str | None = None,
) -> list[RankedRepo]:
    enrichments = enrichments or {}
    previous_state = previous_state or {}
    max_stars_today = max((repo.stars_today or 0 for repo in repos), default=0)
    ranked = [
        score_repository(
            repo=repo,
            enrichment=enrichments.get(repo.full_name),
            max_stars_today=max_stars_today,
            seen_before=_seen_before(previous_state, repo.full_name),
            today=today,
        )
        for repo in repos
    ]
    return sorted(ranked, key=lambda item: item.score.total, reverse=True)


def score_repository(
    repo: TrendingRepo,
    enrichment: RepoEnrichment | None,
    max_stars_today: int,
    seen_before: bool = False,
    today: str | None = None,
) -> RankedRepo:
    text = _evidence_text(repo, enrichment)
    topics = set((enrichment.topics if enrichment else []) or [])
    ai_fit = _term_score(text, topics, AI_TERMS)
    dev_fit = _term_score(text, topics, DEV_TOOL_TERMS)
    docs_fit = _docs_score(repo, enrichment)
    quality = _quality_score(enrichment)
    momentum = _momentum_score(repo, max_stars_today)
    novelty = 0.35 if seen_before else 1.0
    production = _production_score(enrichment)
    recent = _recent_activity_score(enrichment, today)

    score = ScoreBreakdown(
        practical_usefulness=round(20 * max(dev_fit, docs_fit * 0.85), 2),
        ai_workflow_impact=round(18 * ai_fit, 2),
        ease_of_adoption=round(14 * docs_fit, 2),
        technical_quality=round(14 * max(quality, recent * 0.8), 2),
        momentum=round(12 * momentum, 2),
        novelty=round(8 * novelty, 2),
        production_readiness=round(7 * production, 2),
        strategic_relevance=round(7 * max(ai_fit, dev_fit, momentum * 0.7), 2),
    )

    tags = _tags(ai_fit, dev_fit, production, docs_fit, score.total)
    caution = _caution(enrichment, docs_fit, production)
    verdict = _verdict(repo, enrichment, tags, score.total)

    return RankedRepo(repo=repo, enrichment=enrichment, score=score, tags=tags, verdict=verdict, caution=caution)


def _seen_before(state: dict[str, object], full_name: str) -> bool:
    repos = state.get("repos", {})
    return isinstance(repos, dict) and full_name in repos


def _evidence_text(repo: TrendingRepo, enrichment: RepoEnrichment | None) -> str:
    parts = [repo.description, repo.language or ""]
    if enrichment:
        parts.extend(
            [
                enrichment.description or "",
                enrichment.primary_language or "",
                " ".join(enrichment.topics),
                enrichment.readme_excerpt or "",
            ]
        )
    return " ".join(parts).lower()


def _term_score(text: str, topics: set[str], terms: set[str]) -> float:
    hits = sum(1 for term in terms if term in text or term in topics)
    if hits == 0:
        return 0.0
    return min(1.0, 0.25 + hits * 0.18)


def _docs_score(repo: TrendingRepo, enrichment: RepoEnrichment | None) -> float:
    text = _evidence_text(repo, enrichment)
    score = 0.2 if repo.description else 0.0
    if enrichment and enrichment.readme_excerpt:
        score += 0.35
    for term in ("install", "quickstart", "getting started", "usage", "example", "docker"):
        if term in text:
            score += 0.09
    return min(1.0, score)


def _quality_score(enrichment: RepoEnrichment | None) -> float:
    if not enrichment:
        return 0.25
    score = 0.25
    if enrichment.license_spdx and enrichment.license_spdx != "NOASSERTION":
        score += 0.2
    if enrichment.default_branch:
        score += 0.1
    if enrichment.archived is False:
        score += 0.15
    if enrichment.fork is False:
        score += 0.1
    if enrichment.open_issues is not None:
        score += 0.05
    if enrichment.latest_release:
        score += 0.15
    return min(1.0, score)


def _momentum_score(repo: TrendingRepo, max_stars_today: int) -> float:
    star_ratio = (repo.stars_today or 0) / max_stars_today if max_stars_today else 0
    rank_score = max(0.0, 1 - ((repo.rank - 1) / 25))
    return min(1.0, star_ratio * 0.7 + rank_score * 0.3)


def _production_score(enrichment: RepoEnrichment | None) -> float:
    if not enrichment:
        return 0.2
    score = 0.1
    if enrichment.license_spdx and enrichment.license_spdx != "NOASSERTION":
        score += 0.25
    if enrichment.archived is False:
        score += 0.2
    if enrichment.fork is False:
        score += 0.1
    if enrichment.latest_release:
        score += 0.2
    if enrichment.homepage:
        score += 0.15
    return min(1.0, score)


def _recent_activity_score(enrichment: RepoEnrichment | None, today: str | None) -> float:
    if not enrichment or not enrichment.pushed_at:
        return 0.2
    reference = _parse_date(today) or datetime.now(UTC)
    pushed = _parse_datetime(enrichment.pushed_at)
    if not pushed:
        return 0.2
    age = reference - pushed
    if age <= timedelta(days=7):
        return 1.0
    if age <= timedelta(days=30):
        return 0.75
    if age <= timedelta(days=90):
        return 0.45
    return 0.15


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).replace(tzinfo=UTC)
    except ValueError:
        return None


def _parse_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _tags(ai_fit: float, dev_fit: float, production: float, docs_fit: float, total: float) -> list[str]:
    tags: list[str] = []
    if ai_fit >= 0.4:
        tags.append("AI Workflow")
    if dev_fit >= 0.4:
        tags.append("DevTools")
    if production >= 0.65 and docs_fit >= 0.55:
        tags.append("Try Today")
    if total >= 55:
        tags.append("Deep Dive")
    if total < 32 or docs_fit < 0.25:
        tags.append("Watch")
    if production < 0.35:
        tags.append("Hype Risk")
    return tags or ["Watch"]


def _caution(enrichment: RepoEnrichment | None, docs_fit: float, production: float) -> str | None:
    if not enrichment:
        return "Limited enrichment; verify repository details manually."
    if enrichment.archived:
        return "Repository is archived."
    if docs_fit < 0.25:
        return "Weak onboarding evidence."
    if production < 0.35:
        return "Production readiness is unclear."
    return None


def _verdict(
    repo: TrendingRepo,
    enrichment: RepoEnrichment | None,
    tags: list[str],
    total: float,
) -> str:
    language = (enrichment.primary_language if enrichment else None) or repo.language or "Unknown"
    tag_text = ", ".join(tags[:2])
    stars = f"{repo.stars_today} stars today" if repo.stars_today is not None else "trending today"
    return f"{tag_text}: {language} project with {stars}; score {total:.1f}/100."
