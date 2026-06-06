from pathlib import Path
from unittest import TestCase

from gh_trending_notifier.trending import parse_trending_repos


class TrendingParserTests(TestCase):
    def test_parses_repository_cards_from_fixture(self) -> None:
        document = Path("tests/fixtures/trending_daily.html").read_text(encoding="utf-8")

        repos = parse_trending_repos(document)

        self.assertEqual([repo.full_name for repo in repos], ["openai/whisper", "vitejs/vite"])
        self.assertEqual(repos[0].rank, 1)
        self.assertEqual(repos[0].language, "Python")
        self.assertEqual(repos[0].total_stars, 101756)
        self.assertEqual(repos[0].forks, 12435)
        self.assertEqual(repos[0].stars_today, 155)
        self.assertEqual(repos[1].description, "Next generation frontend tooling. It's fast!")
