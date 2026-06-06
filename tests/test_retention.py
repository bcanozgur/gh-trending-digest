import json
import os
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from gh_trending_notifier.cli import _retention_days
from gh_trending_notifier.state import prune_old_data, state_path, write_json


def _touch(path: Path, content: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class RetentionTests(TestCase):
    def test_prunes_dated_files_older_than_retention(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            today = date(2026, 6, 30)
            old = (today - timedelta(days=40)).isoformat()  # outside 28-day window
            recent = (today - timedelta(days=5)).isoformat()  # inside window

            _touch(root / "data" / "runs" / f"{old}.json")
            _touch(root / "data" / "previews" / f"{old}.html")
            _touch(root / "data" / "previews" / f"{old}.txt")
            _touch(root / "data" / "sent" / f"{old}.json")
            _touch(root / "data" / "runs" / f"{recent}.json")

            removed = prune_old_data(root, today.isoformat(), 28)

            self.assertEqual(removed, 4)
            self.assertFalse((root / "data" / "runs" / f"{old}.json").exists())
            self.assertTrue((root / "data" / "runs" / f"{recent}.json").exists())

    def test_prunes_stale_state_entries_only(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            today = date(2026, 6, 30)
            write_json(
                state_path(root),
                {
                    "repos": {
                        "a/old": {"last_seen": (today - timedelta(days=40)).isoformat()},
                        "a/recent": {"last_seen": (today - timedelta(days=3)).isoformat()},
                    }
                },
            )

            prune_old_data(root, today.isoformat(), 28)

            repos = json.loads(state_path(root).read_text(encoding="utf-8"))["repos"]
            self.assertNotIn("a/old", repos)
            self.assertIn("a/recent", repos)

    def test_disabled_when_retention_is_zero(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _touch(root / "data" / "runs" / "2000-01-01.json")
            self.assertEqual(prune_old_data(root, "2026-06-30", 0), 0)
            self.assertTrue((root / "data" / "runs" / "2000-01-01.json").exists())

    def test_retention_never_undercuts_dedupe_window(self) -> None:
        old_retention = os.environ.get("DATA_RETENTION_DAYS")
        old_dedupe = os.environ.get("NEWSLETTER_DEDUPE_DAYS")
        os.environ["DATA_RETENTION_DAYS"] = "3"
        os.environ["NEWSLETTER_DEDUPE_DAYS"] = "10"
        try:
            self.assertEqual(_retention_days(), 10)
        finally:
            for key, value in (
                ("DATA_RETENTION_DAYS", old_retention),
                ("NEWSLETTER_DEDUPE_DAYS", old_dedupe),
            ):
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
