from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from gh_trending_notifier.models import RepoEnrichment, TrendingRepo

API_ROOT = "https://api.github.com"


class GitHubClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class GitHubClient:
    token: str | None = None
    timeout: float = 20.0

    def enrich_many(self, repos: list[TrendingRepo]) -> dict[str, RepoEnrichment]:
        enrichments: dict[str, RepoEnrichment] = {}
        for repo in repos:
            try:
                enrichments[repo.full_name] = self.enrich(repo)
            except GitHubClientError:
                enrichments[repo.full_name] = RepoEnrichment(full_name=repo.full_name)
        return enrichments

    def enrich(self, repo: TrendingRepo) -> RepoEnrichment:
        details = self._get_json(f"/repos/{repo.owner}/{repo.name}")
        readme_excerpt = self._readme_excerpt(repo)
        latest_release = self._latest_release(repo)
        license_info = details.get("license") or {}
        return RepoEnrichment(
            full_name=repo.full_name,
            description=details.get("description"),
            homepage=details.get("homepage") or None,
            primary_language=details.get("language"),
            topics=list(details.get("topics") or []),
            license_spdx=license_info.get("spdx_id") if isinstance(license_info, dict) else None,
            default_branch=details.get("default_branch"),
            archived=details.get("archived"),
            fork=details.get("fork"),
            open_issues=details.get("open_issues_count"),
            pushed_at=details.get("pushed_at"),
            created_at=details.get("created_at"),
            updated_at=details.get("updated_at"),
            readme_excerpt=readme_excerpt,
            latest_release=latest_release,
        )

    def _readme_excerpt(self, repo: TrendingRepo) -> str | None:
        try:
            payload = self._get_json(f"/repos/{repo.owner}/{repo.name}/readme")
        except GitHubClientError:
            return None
        content = payload.get("content")
        if not isinstance(content, str):
            return None
        try:
            raw = base64.b64decode(content, validate=False).decode("utf-8", errors="replace")
        except ValueError:
            return None
        return " ".join(raw.split())[:500] or None

    def _latest_release(self, repo: TrendingRepo) -> str | None:
        try:
            payload = self._get_json(f"/repos/{repo.owner}/{repo.name}/releases/latest")
        except GitHubClientError:
            return None
        tag = payload.get("tag_name")
        return str(tag) if tag else None

    def _get_json(self, path: str) -> dict[str, Any]:
        url = f"{API_ROOT}{path}"
        request = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise GitHubClientError(f"GitHub resource not found: {path}") from exc
            raise GitHubClientError(f"GitHub API failed for {path}: HTTP {exc.code}") from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise GitHubClientError(f"GitHub API failed for {path}: {exc}") from exc

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "gh-trending-notifier/0.1",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers


def graphql_escape(value: str) -> str:
    return json.dumps(value)


def repo_api_url(full_name: str) -> str:
    return f"{API_ROOT}/repos/{urllib.parse.quote(full_name, safe='/')}"
