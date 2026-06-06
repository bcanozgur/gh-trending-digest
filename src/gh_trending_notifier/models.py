from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class TrendingRepo:
    rank: int
    owner: str
    name: str
    description: str
    url: str
    language: str | None
    total_stars: int | None
    forks: int | None
    stars_today: int | None

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["full_name"] = self.full_name
        return data


@dataclass(frozen=True)
class RepoEnrichment:
    full_name: str
    description: str | None = None
    homepage: str | None = None
    primary_language: str | None = None
    topics: list[str] = field(default_factory=list)
    license_spdx: str | None = None
    default_branch: str | None = None
    archived: bool | None = None
    fork: bool | None = None
    open_issues: int | None = None
    pushed_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    readme_excerpt: str | None = None
    latest_release: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScoreBreakdown:
    practical_usefulness: float
    ai_workflow_impact: float
    ease_of_adoption: float
    technical_quality: float
    momentum: float
    novelty: float
    production_readiness: float
    strategic_relevance: float

    @property
    def total(self) -> float:
        return round(
            self.practical_usefulness
            + self.ai_workflow_impact
            + self.ease_of_adoption
            + self.technical_quality
            + self.momentum
            + self.novelty
            + self.production_readiness
            + self.strategic_relevance,
            2,
        )

    def to_dict(self) -> dict[str, float]:
        data = asdict(self)
        data["total"] = self.total
        return data


@dataclass(frozen=True)
class RankedRepo:
    repo: TrendingRepo
    enrichment: RepoEnrichment | None
    score: ScoreBreakdown
    tags: list[str]
    verdict: str
    caution: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo": self.repo.to_dict(),
            "enrichment": self.enrichment.to_dict() if self.enrichment else None,
            "score": self.score.to_dict(),
            "tags": self.tags,
            "verdict": self.verdict,
            "caution": self.caution,
        }


@dataclass(frozen=True)
class Newsletter:
    date: str
    subject: str
    summary: str
    ranked: list[RankedRepo]
    html: str
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "subject": self.subject,
            "summary": self.summary,
            "ranked": [item.to_dict() for item in self.ranked],
            "html": self.html,
            "text": self.text,
        }
