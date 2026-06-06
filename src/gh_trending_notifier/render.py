from __future__ import annotations

from html import escape

from gh_trending_notifier.models import Newsletter, RankedRepo


def build_newsletter(date: str, ranked: list[RankedRepo]) -> Newsletter:
    top_theme = _top_theme(ranked)
    subject = f"GitHub Trending: {top_theme} - {date}"
    summary = _summary(ranked, top_theme)
    html = render_html(date, subject, summary, ranked)
    text = render_text(date, subject, summary, ranked)
    return Newsletter(date=date, subject=subject, summary=summary, ranked=ranked, html=html, text=text)


def render_html(date: str, subject: str, summary: str, ranked: list[RankedRepo]) -> str:
    top_five = ranked[:5]
    ai = [item for item in ranked if "AI Workflow" in item.tags][:5]
    practical = [item for item in ranked if "Try Today" in item.tags][:5]
    watch = [item for item in ranked if "Watch" in item.tags or "Hype Risk" in item.tags][:5]
    rows = "\n".join(_table_row(item) for item in ranked)
    return f"""<!doctype html>
<html>
  <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #111827;">
    <h1 style="font-size: 24px;">{escape(subject)}</h1>
    <p>{escape(summary)}</p>
    {_section_html("Top picks", top_five)}
    {_section_html("AI workflow impact", ai)}
    {_section_html("Practical tools", practical)}
    {_section_html("Watchlist and cautions", watch)}
    <h2 style="font-size: 18px;">Full reviewed list</h2>
    <table cellpadding="6" cellspacing="0" border="1" style="border-collapse: collapse; border-color: #e5e7eb;">
      <thead>
        <tr>
          <th align="left">Repo</th>
          <th align="left">Score</th>
          <th align="left">Tags</th>
          <th align="left">Verdict</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
    <p style="color: #6b7280; font-size: 12px;">Generated for {escape(date)} from GitHub Trending daily.</p>
  </body>
</html>
"""


def render_text(date: str, subject: str, summary: str, ranked: list[RankedRepo]) -> str:
    lines = [subject, "", summary, "", "Top picks"]
    for index, item in enumerate(ranked[:5], 1):
        lines.extend(_text_item(index, item))
    lines.extend(["", "Full reviewed list"])
    for item in ranked:
        lines.append(
            f"- {item.repo.full_name}: {item.score.total:.1f}/100 [{', '.join(item.tags)}] "
            f"{item.verdict}"
        )
    lines.append("")
    lines.append(f"Generated for {date} from GitHub Trending daily.")
    return "\n".join(lines)


def _section_html(title: str, items: list[RankedRepo]) -> str:
    if not items:
        return ""
    body = "\n".join(_card_html(item) for item in items)
    return f'<h2 style="font-size: 18px;">{escape(title)}</h2>\n{body}'


def _card_html(item: RankedRepo) -> str:
    caution = f"<p><strong>Caution:</strong> {escape(item.caution)}</p>" if item.caution else ""
    return f"""
    <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; margin: 10px 0;">
      <h3 style="margin: 0 0 6px;"><a href="{escape(item.repo.url)}">{escape(item.repo.full_name)}</a> {item.score.total:.1f}</h3>
      <p style="margin: 0 0 6px;">{escape(item.repo.description or "No description.")}</p>
      <p style="margin: 0 0 6px;"><strong>{escape(', '.join(item.tags))}</strong></p>
      <p style="margin: 0;">{escape(item.verdict)}</p>
      {caution}
    </div>
"""


def _table_row(item: RankedRepo) -> str:
    return f"""
        <tr>
          <td><a href="{escape(item.repo.url)}">{escape(item.repo.full_name)}</a></td>
          <td>{item.score.total:.1f}</td>
          <td>{escape(', '.join(item.tags))}</td>
          <td>{escape(item.verdict)}</td>
        </tr>"""


def _text_item(index: int, item: RankedRepo) -> list[str]:
    lines = [
        f"{index}. {item.repo.full_name} - {item.score.total:.1f}/100",
        f"   {item.repo.url}",
        f"   {item.verdict}",
    ]
    if item.caution:
        lines.append(f"   Caution: {item.caution}")
    return lines


def _top_theme(ranked: list[RankedRepo]) -> str:
    if not ranked:
        return "no repositories found"
    ai_count = sum(1 for item in ranked[:10] if "AI Workflow" in item.tags)
    devtools_count = sum(1 for item in ranked[:10] if "DevTools" in item.tags)
    if ai_count >= 3:
        return "AI workflow signal"
    if devtools_count >= 3:
        return "developer tools signal"
    return "daily developer signal"


def _summary(ranked: list[RankedRepo], top_theme: str) -> str:
    if not ranked:
        return "GitHub Trending returned no repositories for the daily view."
    best = ranked[0].repo.full_name
    return f"Today leans toward {top_theme}; the strongest pick is {best}."
