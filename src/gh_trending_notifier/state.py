from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from gh_trending_notifier.models import Newsletter, RankedRepo


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def state_path(root: Path) -> Path:
    return root / "data" / "state.json"


def run_path(root: Path, date: str) -> Path:
    return root / "data" / "runs" / f"{date}.json"


def sent_path(root: Path, date: str) -> Path:
    return root / "data" / "sent" / f"{date}.json"


def preview_paths(root: Path, date: str) -> tuple[Path, Path]:
    preview_dir = root / "data" / "previews"
    return preview_dir / f"{date}.html", preview_dir / f"{date}.txt"


def has_sent(root: Path, date: str) -> bool:
    return sent_path(root, date).exists()


def record_run(root: Path, newsletter: Newsletter) -> Path:
    path = run_path(root, newsletter.date)
    write_json(path, newsletter.to_dict())
    html_path, text_path = preview_paths(root, newsletter.date)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(newsletter.html, encoding="utf-8")
    text_path.write_text(newsletter.text, encoding="utf-8")
    return path


def update_state(root: Path, date: str, ranked: list[RankedRepo]) -> Path:
    path = state_path(root)
    current = read_json(path, {"repos": {}})
    repos = current.setdefault("repos", {})
    for item in ranked:
        entry = repos.setdefault(item.repo.full_name, {})
        entry.setdefault("first_seen", date)
        entry["last_seen"] = date
        entry["last_rank"] = item.repo.rank
        entry["last_score"] = item.score.total
        entry["last_stars_today"] = item.repo.stars_today
        entry["last_total_stars"] = item.repo.total_stars
    current["last_run"] = date
    write_json(path, current)
    return path


def record_sent(root: Path, date: str, provider: str, recipients: list[str], message_id: str) -> Path:
    recipient_hashes = [hashlib.sha256(value.encode("utf-8")).hexdigest() for value in recipients]
    path = sent_path(root, date)
    write_json(
        path,
        {
            "date": date,
            "provider": provider,
            "recipient_hashes": recipient_hashes,
            "message_id": message_id,
        },
    )
    return path
