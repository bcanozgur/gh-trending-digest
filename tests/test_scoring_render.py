from unittest import TestCase

from gh_trending_notifier.models import RepoEnrichment, TrendingRepo
from gh_trending_notifier.render import build_newsletter
from gh_trending_notifier.scoring import rank_repositories


class ScoringRenderTests(TestCase):
    def test_ranking_and_newsletter_are_deterministic(self) -> None:
        repos = [
            TrendingRepo(
                rank=1,
                owner="acme",
                name="agent-cli",
                description="AI agent CLI for developer workflow automation",
                url="https://github.com/acme/agent-cli",
                language="Python",
                total_stars=1000,
                forks=50,
                stars_today=200,
            ),
            TrendingRepo(
                rank=2,
                owner="acme",
                name="theme-pack",
                description="A collection of themes",
                url="https://github.com/acme/theme-pack",
                language="CSS",
                total_stars=900,
                forks=20,
                stars_today=50,
            ),
        ]
        enrichments = {
            "acme/agent-cli": RepoEnrichment(
                full_name="acme/agent-cli",
                primary_language="Python",
                topics=["ai", "agent", "cli", "developer-tools"],
                license_spdx="MIT",
                default_branch="main",
                archived=False,
                fork=False,
                pushed_at="2026-06-07T00:00:00Z",
                readme_excerpt="Install with pip. Quickstart and usage examples for automation.",
                latest_release="v1.0.0",
            ),
            "acme/theme-pack": RepoEnrichment(
                full_name="acme/theme-pack",
                primary_language="CSS",
                topics=["themes"],
                archived=False,
                fork=False,
                pushed_at="2026-05-01T00:00:00Z",
            ),
        }

        ranked = rank_repositories(repos, enrichments=enrichments, today="2026-06-07")
        newsletter = build_newsletter("2026-06-07", ranked)

        self.assertEqual(ranked[0].repo.full_name, "acme/agent-cli")
        self.assertIn("AI Workflow", ranked[0].tags)
        self.assertIn("Try Today", ranked[0].tags)
        self.assertIn("acme/agent-cli", newsletter.html)
        self.assertIn("Full reviewed list", newsletter.text)
        self.assertTrue(newsletter.subject.startswith("GitHub Trending:"))
