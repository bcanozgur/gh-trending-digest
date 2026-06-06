from __future__ import annotations

import html
import re
import urllib.request
from html.parser import HTMLParser
from typing import Iterable

from gh_trending_notifier.models import TrendingRepo

TRENDING_URL = "https://github.com/trending?since=daily"


class TrendingFetchError(RuntimeError):
    pass


class _RepoArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.articles: list[str] = []
        self._depth = 0
        self._capturing = False
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        class_name = attr.get("class", "")
        if tag == "article" and "Box-row" in class_name:
            self._capturing = True
            self._depth = 1
            self._chunks = [self.get_starttag_text() or ""]
            return
        if self._capturing:
            self._depth += 1
            self._chunks.append(self.get_starttag_text() or "")

    def handle_endtag(self, tag: str) -> None:
        if not self._capturing:
            return
        self._chunks.append(f"</{tag}>")
        self._depth -= 1
        if self._depth == 0:
            self.articles.append("".join(self._chunks))
            self._capturing = False
            self._chunks = []

    def handle_data(self, data: str) -> None:
        if self._capturing:
            self._chunks.append(data)

    def handle_entityref(self, name: str) -> None:
        if self._capturing:
            self._chunks.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self._capturing:
            self._chunks.append(f"&#{name};")


def fetch_trending_html(url: str = TRENDING_URL, timeout: float = 20.0) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": "gh-trending-notifier/0.1 (+https://github.com/trending)",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except OSError as exc:
        raise TrendingFetchError(f"Failed to fetch GitHub Trending: {exc}") from exc


def parse_trending_repos(document: str) -> list[TrendingRepo]:
    parser = _RepoArticleParser()
    parser.feed(document)
    repos = [_parse_article(index + 1, article) for index, article in enumerate(parser.articles)]
    return [repo for repo in repos if repo is not None]


def _parse_article(rank: int, article: str) -> TrendingRepo | None:
    full_name = _extract_full_name(article)
    if not full_name:
        return None

    owner, name = full_name.split("/", 1)
    text = _visible_text(article)
    description = _extract_description(article)
    language = _extract_language(article)
    numbers = _extract_stars_and_forks(article)

    return TrendingRepo(
        rank=rank,
        owner=owner,
        name=name,
        description=description,
        url=f"https://github.com/{owner}/{name}",
        language=language,
        total_stars=numbers.get("stars"),
        forks=numbers.get("forks"),
        stars_today=_extract_stars_today(text),
    )


def _extract_full_name(article: str) -> str | None:
    match = re.search(r'href="/([^"/\s]+/[^"/\s]+)"', article)
    if not match:
        return None
    return html.unescape(match.group(1)).strip()


def _extract_description(article: str) -> str:
    match = re.search(r'<p[^>]*class="[^"]*col-9[^"]*"[^>]*>(.*?)</p>', article, re.S)
    if not match:
        return ""
    return _collapse_ws(_strip_tags(match.group(1)))


def _extract_language(article: str) -> str | None:
    match = re.search(r'itemprop="programmingLanguage"[^>]*>(.*?)</span>', article, re.S)
    if not match:
        return None
    language = _collapse_ws(_strip_tags(match.group(1)))
    return language or None


def _extract_stars_and_forks(article: str) -> dict[str, int]:
    values: dict[str, int] = {}
    links = re.findall(r'href="/[^"]+/(stargazers|forks)"[^>]*>(.*?)</a>', article, re.S)
    for kind, body in links:
        value = _parse_int(_collapse_ws(_strip_tags(body)))
        if kind == "stargazers":
            values["stars"] = value
        elif kind == "forks":
            values["forks"] = value
    return values


def _extract_stars_today(text: str) -> int | None:
    match = re.search(r"([\d,]+)\s+stars?\s+today", text, re.I)
    if not match:
        return None
    return _parse_int(match.group(1))


def _visible_text(fragment: str) -> str:
    return _collapse_ws(_strip_tags(fragment))


def _strip_tags(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", fragment))


def _collapse_ws(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _parse_int(value: str) -> int:
    digits = re.sub(r"[^\d]", "", value)
    return int(digits) if digits else 0


def serialize_trending(repos: Iterable[TrendingRepo]) -> list[dict[str, object]]:
    return [repo.to_dict() for repo in repos]
