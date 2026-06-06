import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase

from gh_trending_notifier.cli import main
from gh_trending_notifier.email_sender import EmailError
from gh_trending_notifier.state import has_sent, record_sent


class StateCliTests(TestCase):
    def test_cli_dry_run_writes_archive_preview_and_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exit_code = main(
                [
                    "run",
                    "--date",
                    "2026-06-07",
                    "--repo-root",
                    str(root),
                    "--html-file",
                    "tests/fixtures/trending_daily.html",
                    "--skip-enrichment",
                ]
            )

            self.assertEqual(exit_code, 0)
            run_file = root / "data" / "runs" / "2026-06-07.json"
            state_file = root / "data" / "state.json"
            html_preview = root / "data" / "previews" / "2026-06-07.html"
            text_preview = root / "data" / "previews" / "2026-06-07.txt"
            self.assertTrue(run_file.exists())
            self.assertTrue(state_file.exists())
            self.assertTrue(html_preview.exists())
            self.assertTrue(text_preview.exists())
            payload = json.loads(run_file.read_text(encoding="utf-8"))
            self.assertEqual(payload["date"], "2026-06-07")
            self.assertEqual(payload["ranked"][0]["repo"]["full_name"], "openai/whisper")

    def test_send_failure_keeps_archive_without_advancing_state(self) -> None:
        old_mail_to = os.environ.pop("MAIL_TO", None)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)

                with self.assertRaises(EmailError):
                    main(
                        [
                            "run",
                            "--date",
                            "2026-06-07",
                            "--repo-root",
                            str(root),
                            "--html-file",
                            "tests/fixtures/trending_daily.html",
                            "--skip-enrichment",
                            "--send",
                        ]
                    )

                self.assertTrue((root / "data" / "runs" / "2026-06-07.json").exists())
                self.assertFalse((root / "data" / "state.json").exists())
                self.assertFalse(has_sent(root, "2026-06-07"))
        finally:
            if old_mail_to is not None:
                os.environ["MAIL_TO"] = old_mail_to

    def test_sent_marker_hashes_recipients(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            marker = record_sent(root, "2026-06-07", "smtp", ["dev@example.com"], "<id@example.com>")
            payload = json.loads(marker.read_text(encoding="utf-8"))

            self.assertTrue(has_sent(root, "2026-06-07"))
            self.assertEqual(payload["provider"], "smtp")
            self.assertNotIn("dev@example.com", marker.read_text(encoding="utf-8"))

    def test_doctor_fails_when_directory_is_not_git_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
            workflow = root / ".github" / "workflows"
            workflow.mkdir(parents=True)
            (workflow / "daily.yml").write_text("name: daily\n", encoding="utf-8")

            exit_code = main(["doctor", "--repo-root", str(root)])

            self.assertEqual(exit_code, 1)
