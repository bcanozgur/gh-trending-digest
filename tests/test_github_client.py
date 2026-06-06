import base64
from unittest import TestCase

from gh_trending_notifier.github_client import GitHubClient, GitHubClientError, repo_api_url
from gh_trending_notifier.models import TrendingRepo


class FakeGitHubClient(GitHubClient):
    def __init__(self, payloads: dict[str, dict[str, object]]) -> None:
        super().__init__(token="test-token")
        self.payloads = payloads

    def _get_json(self, path: str) -> dict[str, object]:
        if path not in self.payloads:
            raise GitHubClientError(f"missing payload: {path}")
        return self.payloads[path]


class GitHubClientTests(TestCase):
    def test_enrich_maps_repository_readme_and_release(self) -> None:
        readme = base64.b64encode(
            b"# Agent CLI\n\nInstall with pip. Quickstart examples for AI workflows."
        ).decode("ascii")
        client = FakeGitHubClient(
            {
                "/repos/acme/agent-cli": {
                    "description": "AI agent CLI",
                    "homepage": "https://example.com",
                    "language": "Python",
                    "topics": ["ai", "agent", "cli"],
                    "license": {"spdx_id": "MIT"},
                    "default_branch": "main",
                    "archived": False,
                    "fork": False,
                    "open_issues_count": 7,
                    "pushed_at": "2026-06-07T00:00:00Z",
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-06-07T00:00:00Z",
                },
                "/repos/acme/agent-cli/readme": {"content": readme},
                "/repos/acme/agent-cli/releases/latest": {"tag_name": "v1.2.3"},
            }
        )
        repo = TrendingRepo(
            rank=1,
            owner="acme",
            name="agent-cli",
            description="AI agent CLI",
            url="https://github.com/acme/agent-cli",
            language="Python",
            total_stars=100,
            forks=10,
            stars_today=20,
        )

        enrichment = client.enrich(repo)

        self.assertEqual(enrichment.full_name, "acme/agent-cli")
        self.assertEqual(enrichment.license_spdx, "MIT")
        self.assertEqual(enrichment.latest_release, "v1.2.3")
        self.assertIn("Quickstart examples", enrichment.readme_excerpt or "")

    def test_enrich_many_degrades_missing_repository_to_empty_enrichment(self) -> None:
        repo = TrendingRepo(
            rank=1,
            owner="missing",
            name="repo",
            description="",
            url="https://github.com/missing/repo",
            language=None,
            total_stars=None,
            forks=None,
            stars_today=None,
        )

        result = FakeGitHubClient({}).enrich_many([repo])

        self.assertEqual(result["missing/repo"].full_name, "missing/repo")
        self.assertIsNone(result["missing/repo"].description)

    def test_repo_api_url_quotes_repository_name_without_breaking_slash(self) -> None:
        self.assertEqual(repo_api_url("acme/agent cli"), "https://api.github.com/repos/acme/agent%20cli")
